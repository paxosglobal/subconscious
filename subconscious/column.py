from .model import Column


class Integer(Column):
    def __init__(
            self,
            primary_key=None,
            composite_key=None,
            index=None,
            required=None,
            enum=None,
            sort=None, auto=True):
        super(Integer, self).__init__(int, primary_key, composite_key, index, required, enum, sort)
        self.auto = auto

    async def auto_generate(self, db, model):
        return await db.incr('auto:{}:{}'.format(model.key_prefix(), self.name))

