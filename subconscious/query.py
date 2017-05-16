class Query(object):
    def __init__(self, model, db):
        self._model = model
        self._filter = {}
        self._order_by = None
        self._limit = None
        self._offset = None
        self._db = db

    def filter(self, **kwargs):
        self._filter.update(kwargs)
        return self

    def order_by(self, order_by):
        self._order_by = order_by
        return self

    def limit(self, limit):
        self._limit = limit
        return self

    def offset(self, offset):
        self._offset = offset
        return self

    def __aiter__(self):
        self.result_set = self._model.filter_by(
            db=self._db,
            order_by=self._order_by,
            limit=self._limit,
            offset=self._offset,
            **self._filter,)

        return self

    async def __anext__(self):
        async for x in self.result_set:
            return x
        raise StopAsyncIteration

    async def first(self):
        return await self._model.get_object_or_none(db=self._db, order_by=self._order_by, **self._filter)
