import inspect
import asyncio
import logging
from .columns import Column
from .query import Query

VALUE_ID_SEPARATOR = '\x00'
MODEL_NAME_ID_SEPARATOR = ':'

logger = logging.getLogger(__name__)


class _AllIter:
    def __init__(self, db, model, match, count=100):
        self.match = match
        self.count = count
        self.db = db
        self.model = model
        self.iterable = self.db.iscan(match=self.match, count=self.count)

    async def __aiter__(self):
        return self

    async def __anext__(self):
        while True:
            key = await self.iterable.__anext__()
            return await self.model.load(self.db, key.decode().partition(MODEL_NAME_ID_SEPARATOR)[2])


class ModelMeta(type):
    def __init__(cls, what, bases=None, attributes=None):
        super().__init__(what, bases, attributes)
        if what not in ('Model',):
            cls._columns = set()
            cls._column_names = set()
            cls._indexed_columns = set()
            cls._indexed_column_names = set()
            cls._identifier_column_names = set()
            cls._pk = None
            for name, column in inspect.getmembers(cls, lambda col: type(col) == Column):
                column.name = name
                cls._columns.add(column)
                cls._column_names.add(name)
                if column.index is True:
                    cls._indexed_columns.add(column)
                    cls._indexed_column_names.add(name)
                if column.pk is True:
                    assert cls._pk is None, "Only one primary key is allowed"
                    cls._pk = column
                    cls._identifier_column_names.add(name)
                if column.composite is True:
                    cls._identifier_column_names.add(name)


class Model(metaclass=ModelMeta):
    _custom_indexes = {}

    def __init__(self, **kwargs):
        assert (self._pk is None and len(self._identifier_column_names) > 1) \
            or (self._pk and len(self._identifier_column_names) == 1), \
            "{}: You need exactly 1 primary_key column or more than 1 composite_key columns".format(
                self.__class__.__name__)
        for column in self._columns:
            if column.name in kwargs:
                value = kwargs.pop(column.name)
                assert type(value) == column.col_type, "Column `{}` in {} has value {}, should be of type {}".format(
                    column.name,
                    self.__class__.__name__,
                    value,
                    column.col_type,
                )
                if column.enum_choices:
                    assert value in column.enum_choices, "Column `{}` in {} has value {}, should be in set {}".format(
                        column.name,
                        self.__class__.__name__,
                        value,
                        column.enum_choices,
                    )
                setattr(self, column.name, value)
            else:
                assert not column.required, 'Column `{}` in `{}` is required'.format(
                    column.name,
                    self.__class__.__name__,
                )
                setattr(self, column.name, None)

    @classmethod
    def query(cls, db):
        return Query(cls, db)

    def as_dict(self):
        _dict = {}
        for name in self._column_names:
            if getattr(self, name):
                _dict[name] = getattr(self, name)
        return _dict

    async def save_index(self, db):
        for column in self._indexed_columns:
            index_key = 'index:{key_prefix}:{column_name}'.format(
                key_prefix=self.key_prefix(),
                column_name=column.name,

            )
            index_value = '{value}{separator}{identity}'.format(
                value=getattr(self, column.name),
                identity=self.identifier(),
                separator=VALUE_ID_SEPARATOR
            )
            await db.zadd(index_key, 0, index_value)
        for index in self._custom_indexes:
            index_key = ':'.join(['custom', self.key_prefix(), ] + list(index))
            sort_str = '-'.join([str(getattr(self, x)) for x in index])
            for name in self._indexed_column_names:
                value = getattr(self, name)
                index_value = '{name}{separator}{value}{separator}{sort_str}{value_id_separator}{identifier}'.format(
                    name=name,
                    value=value,
                    sort_str=sort_str,
                    identifier=self.identifier(),
                    value_id_separator=VALUE_ID_SEPARATOR,
                    separator=MODEL_NAME_ID_SEPARATOR,
                )
                await db.zadd(index_key, 0, index_value)

    @classmethod
    def key_prefix(cls):
        return cls.__name__

    def identifier(self):
        identifiers = [str(getattr(self, name)) for name in sorted(self._identifier_column_names)]
        return ':'.join(identifiers)

    @classmethod
    def redis_key(cls, identifier):
        return '{}{}{}'.format(cls.key_prefix(), MODEL_NAME_ID_SEPARATOR, identifier)

    async def save(self, db):
        await self.save_index(db)
        logger.debug('Saving object with key {}'.format(self.redis_key(self.identifier())))
        return await db.hmset_dict(self.redis_key(self.identifier()), self.as_dict())

    @classmethod
    async def get_by(cls, db, **kwargs):
        """Query by attributes. Ordering is not supported
        Example:
            User.get_by(db, age=[32, 54])
            User.get_by(db, age=23, name="guido")

        """
        result_set = set()
        first_iteration = True
        for k, v in kwargs.items():
            assert k in cls._indexed_column_names
            if isinstance(v, (list, tuple)):
                values = [str(x) for x in v]
            else:
                values = (str(v),)
            temp_set = set()
            for value in values:
                index_key = 'index:{key_prefix}:{column_name}'.format(
                    key_prefix=cls.key_prefix(),
                    column_name=k)
                temp_set = temp_set.union({x.decode().partition(VALUE_ID_SEPARATOR)[2] for x in await db.zrangebylex(
                    index_key,
                    min='{}{}'.format(value, VALUE_ID_SEPARATOR).encode(),
                    max='{}{}\xff'.format(value, VALUE_ID_SEPARATOR).encode())})
            if first_iteration:
                result_set = result_set.union(temp_set)
                first_iteration = False
            else:
                result_set = result_set.intersection(temp_set)
        futures = []
        for key in result_set:
            futures.append(cls.load(db, key))

        return await asyncio.gather(*futures)

    @classmethod
    async def load(cls, db, identifier):
        if isinstance(identifier, tuple):
            identifier = ":".join(identifier)
        key = cls.redis_key(identifier)
        logger.debug('Loading object with key {}'.format(key))
        if await db.exists(key):
            data = await db.hgetall(key)
            kwargs = {}
            fields_stored = []
            for key_bin, value_bin in data.items():
                key, value = key_bin.decode(), value_bin.decode()
                column = getattr(cls, key, False)
                if not column or (column.col_type == str):
                    kwargs[key] = value
                else:
                    kwargs[key] = column.col_type(value)
                fields_stored.append(key)
            stored_entity = cls(**kwargs)
            [setattr(stored_entity, x, None) for x in cls._column_names if x not in fields_stored]
            return stored_entity
        else:
            logger.debug('Object with key {} not existing'.format(key))
            return None

    @classmethod
    async def all(cls, db):
        return _AllIter(db, cls, '{}{}*'.format(cls.key_prefix(), MODEL_NAME_ID_SEPARATOR), count=1000)
