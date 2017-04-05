# python modules
import asyncio
import inspect
import logging

from .column import Column


logger = logging.getLogger(__name__)

VALUE_ID_SEPARATOR = '\x00'
MODEL_NAME_ID_SEPARATOR = ':'


# Exceptions

class InvalidQuery(Exception):
    pass


class InvalidModelDefinition(Exception):
    pass


class BadDataError(Exception):
    pass


class UnexpectedColumnError(Exception):
    pass


class ModelMeta(type):

    def __init__(cls, what, bases=None, attributes=None):
        super(ModelMeta, cls).__init__(what, bases, attributes)
        if cls.__name__ not in ('RedisModel', 'TimeStampedModel'):
            columns = []
            num_primary, num_composite = 0, 0
            cls._pk_name = None
            # grab all Columns from the model
            for name, column in inspect.getmembers(cls, lambda col: isinstance(col, Column)):
                column.name = name
                columns.append(column)
                if column.primary:
                    num_primary += 1
                    cls._pk_name = column.name
                if column.composite:
                    num_composite += 1

            # Defensive checks
            if num_primary == 0:
                if num_composite == 0:
                    err_msg = 'No primary key or composite key in {}'.format(cls.__name__)
                    raise InvalidModelDefinition(err_msg)
                if num_composite == 1:
                    err_msg = 'Your composite key is really a primary key in {}'.format(cls.__name__)
                    raise InvalidModelDefinition(err_msg)
            if num_primary == 1:
                if num_composite != 0:
                    err_msg = 'Cannot have both primary and composite keys in {}'.format(cls.__name__)
                    raise InvalidModelDefinition(err_msg)

            cls._columns = tuple(sorted(columns, key=lambda c: c.name))
            cls._indexed_columns = tuple(sorted([col for col in cls._columns if col.indexed], key=lambda c: c.name))
            cls._sortable_columns = tuple(sorted([col for col in cls._columns if col.sorted], key=lambda c: c.name))
            cls._identifier_columns = tuple(
                sorted([col for col in cls._columns if col.primary or col.composite],
                       key=lambda c: c.name))
            cls._auto_columns = sorted(
                [col for col in cls._columns if getattr(col, 'auto_increment', False)],
                key=lambda c: c.name
            )
            cls._queryable_colnames_set = set(
                [col.name for col in cls._indexed_columns + cls._identifier_columns + cls._sortable_columns]
            )
            cls._sortable_column_names = tuple([x.name for x in cls._sortable_columns])
            cls._auto_column_names = {col.name for col in cls._auto_columns}
            cls._indexed_column_names = {col.name for col in cls._indexed_columns}
            cls._columns_map = {c.name: c for c in cls._columns}
            cls._identifier_column_names = tuple([x.name for x in cls._identifier_columns])


class RedisModel(object, metaclass=ModelMeta):

    # force only keyword arguments
    def __init__(self, **kwargs):
        loading = kwargs.pop('loading', False)
        for column in self._columns:
            if column.name in kwargs:
                value = kwargs.pop(column.name)
                if type(value) != column.field_type:
                    err_msg = "Column `{}` in {} has value {}, should be of type {}".format(
                        column.name,
                        self.__class__.__name__,
                        value,
                        column.field_type,
                    )
                    raise BadDataError(err_msg)

                if column.enum_choices and value not in column.enum_choices:
                    err_msg = "Column `{}` in {} has value {}, should be in set {}".format(
                        column.name,
                        self.__class__.__name__,
                        value,
                        column.enum_choices,
                    )
                    raise BadDataError(err_msg)
                if getattr(column, 'auto_increment', False) and not loading:
                    err_msg = "Not allowed to set auto_increment column({})".format(column.name)
                    raise BadDataError(err_msg)

                self.__dict__.update({column.name: value})
            else:
                if column.required and not getattr(column, 'auto_increment', False):
                    err_msg = 'Missing column `{}` in `{}` is required'.format(
                        column.name,
                        self.__class__.__name__,
                    )
                    raise BadDataError(err_msg)

        # Require that every kwarg supplied matches an expected column
        # TODO: handle TimeStampedModel cols better
        known_cols_set = set([column.name for column in self._columns] + ['updated_at', 'created_at'])
        supplied_cols_set = set([x for x in kwargs])
        unknown_cols_set = supplied_cols_set - known_cols_set
        if unknown_cols_set != set():
            err_msg = 'Unknown column(s): {} in `{}`'.format(
                unknown_cols_set,
                self.__class__.__name__,
            )
            raise UnexpectedColumnError(err_msg)

    def __setattr__(self, name, value):
        if name in self._auto_column_names:
            err_msg = "Not allowed to set auto_increment column({})".format(name)
            raise BadDataError(err_msg)

        return super(RedisModel, self).__setattr__(name, value)

    @classmethod
    def key_prefix(cls):
        """Prefix that we use for Redis storage, used for all keys related
        to this object. Default to class name.
        """
        return cls.__name__

    @classmethod
    def make_key(cls, identifier):
        """Convenience method for computing the Redis object instance key
        from the identifier
        """
        return "{}{}{}".format(cls.key_prefix(), MODEL_NAME_ID_SEPARATOR, identifier)

    def has_real_data(self, column_name):
        return not isinstance(getattr(self, column_name), Column)

    def identifier(self):
        identifiers = [str(getattr(self, column.name)) for column in self._identifier_columns]
        return ':'.join(identifiers)

    def redis_key(self):
        """Key used for storage of object instance in Redis.
        """
        return "{}{}{}".format(self.key_prefix(), MODEL_NAME_ID_SEPARATOR, self.identifier())

    def as_dict(self):
        """Dict version of this object
        """
        # WARNING: we have to send a copy, otherwise changing the dict
        # changes the object!
        # FIXME: this returns no keys for keys whose value is None!
        return self.__dict__.copy()

    def __repr__(self):
        return "<{}>".format(self.redis_key())

    @classmethod
    def get_index_key(cls, column_name):
        return 'index{}{}{}{}'.format(MODEL_NAME_ID_SEPARATOR, cls.key_prefix(), MODEL_NAME_ID_SEPARATOR, column_name)

    async def save_index(self, db, stale_object=None):
        for indexed_column in self._queryable_colnames_set:
            index_key = self.get_index_key(indexed_column)
            if stale_object:
                stale_index_value = '{}{}{}'.format(
                    getattr(stale_object, indexed_column),
                    VALUE_ID_SEPARATOR,
                    stale_object.identifier()
                )
                await db.zrem(index_key, stale_index_value)
            index_value = '{}{}{}'.format(
                getattr(self, indexed_column),
                VALUE_ID_SEPARATOR,
                self.identifier()
            )
            # Index it by adding to a sorted set with 0 score. It will be lexically sorted by redis
            await db.zadd(index_key, 0, index_value,)

    async def save(self, db):
        """Save the object to Redis.
        """
        kwargs = {}
        for col in self._auto_columns:
            if not self.has_real_data(col.name):
                kwargs[col.name] = await col.auto_generate(db, self)
        self.__dict__.update(kwargs)

        # we have to delete the old index key
        stale_object = await self.__class__.load(db, identifier=self.identifier())
        success = await db.hmset_dict(self.redis_key(), self.__dict__.copy())
        await self.save_index(db, stale_object=stale_object)
        return success

    async def exists(self, db):
        return await db.exists(self.redis_key())

    @classmethod
    async def load(cls, db, identifier=None, redis_key=None):
        """Load the object from redis. Use the identifier (colon-separated
        composite keys or the primary key) or the redis_key.
        """
        if not identifier and not redis_key:
            raise InvalidQuery('Must supply identifier or redis_key')
        if redis_key is None:
            redis_key = cls.make_key(identifier)
        if await db.exists(redis_key):
            data = await db.hgetall(redis_key)
            kwargs = {}
            for key_bin, value_bin in data.items():
                key, value = key_bin, value_bin
                column = getattr(cls, key, False)
                if not column or (column.field_type == str):
                    kwargs[key] = value
                else:
                    kwargs[key] = column.field_type(value)
            kwargs['loading'] = True
            return cls(**kwargs)
        else:
            logger.debug("No Redis key found: {}".format(redis_key))
            return None

    @classmethod
    async def _get_ids_for_all(cls, db, order_by):
        if not order_by:
            order_by = cls._identifier_column_names[0]
        if order_by[0] in ['+', '-']:
            direction, order_by = order_by[0], order_by[1:]
        else:
            direction = '+'
        if order_by not in cls._queryable_colnames_set:
            err_msg = 'order_by `{}` not in {}'.format(order_by, cls._queryable_colnames_set)
            raise InvalidQuery(err_msg)
        if direction == '+':
            range_func = db.zrange
        else:
            range_func = db.zrevrange
        all_keys = []
        for index_entry in await range_func(cls.get_index_key(order_by), 0, -1):
            all_keys.append('{}{}{}'.format(
                cls.key_prefix(),
                MODEL_NAME_ID_SEPARATOR,
                index_entry.split(VALUE_ID_SEPARATOR)[-1])
            )
        return all_keys

    @classmethod
    async def all(cls, db, order_by=None):
        """Return all object instances of this class that's in the db.
        """
        all_keys = await cls._get_ids_for_all(db, order_by=order_by)

        if not all_keys:
            return []
        futures = []
        for redis_key in all_keys:
            futures.append(cls.load(db, redis_key=redis_key))
        return [x for x in await asyncio.gather(*futures, loop=db.connection._loop)
                if x is not None]

    @classmethod
    async def all_iter(cls, db, order_by=None):
        for redis_key in await cls._get_ids_for_all(db, order_by=order_by):
            yield await cls.load(db, redis_key=redis_key)

    @classmethod
    async def _get_ids_filter_by(cls, db, **kwargs):
        missing_cols_set = set(kwargs.keys()) - cls._queryable_colnames_set
        if missing_cols_set:
            err_msg = '{missing_cols_set} not in {queryable_cols}'.format(
                missing_cols_set=missing_cols_set,
                queryable_cols=cls._queryable_colnames_set,
            )
            raise InvalidQuery(err_msg)
        result_set = set()
        first_iteration = True
        for k, v in kwargs.items():
            if v is None:
                v = cls._columns_map[k]
            if isinstance(v, (list, tuple)):
                values = [str(x) for x in v]
            else:
                values = (str(v),)
            temp_set = set()
            for value in values:
                temp_set = temp_set.union({x.partition(VALUE_ID_SEPARATOR)[2] for x in await db.zrangebylex(
                    cls.get_index_key(k),
                    min='{}{}'.format(value, VALUE_ID_SEPARATOR).encode(),
                    max='{}{}\xff'.format(value, VALUE_ID_SEPARATOR).encode())})
            if first_iteration:
                result_set = result_set.union(temp_set)
                first_iteration = False
            else:
                result_set = result_set.intersection(temp_set)
        return sorted(result_set)

    @classmethod
    async def filter_by(cls, db, **kwargs):
        """Query by attributes. Ordering is not supported
        Example:
            User.get_by(db, age=[32, 54])
            User.get_by(db, age=23, name="guido")

        """
        futures = []
        for key in await cls._get_ids_filter_by(db, **kwargs):
            futures.append(cls.load(db, key))
        return await asyncio.gather(*futures, loop=db.connection._loop)

    @classmethod
    async def filter_by_iter(cls, db, **kwargs):
        """Query by attributes iteratively. Ordering is not supported
        Example:
            User.get_by(db, age=[32, 54])
            User.get_by(db, age=23, name="guido")

        """
        for key in await cls._get_ids_filter_by(db, **kwargs):
            yield await cls.load(db, key)
