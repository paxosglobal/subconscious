class Query(object):
    def __init__(self, model, db):
        self._model = model
        self._filter = {}
        self._db = db

    async def first(self):
        if self._filter:
            return await self._model.get_object_or_none(db=self._db, **self._filter)
        else:
            async for x in self._model.all(db=self._db, limit=1):
                return x
        return None

    def filter(self, **kwargs):
        self._filter.update(kwargs)
        return self

    def execute(self):
        if self._filter:
            return self._model.filter_by(db=self._db, **self._filter)
        else:
            return self._model.all(db=self._db)
