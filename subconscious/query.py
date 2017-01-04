import asyncio


class Query(object):
    _filter = {}
    _order = []

    def __init__(self, model, db):
        self.model = model
        self.db = db

    def filter(self, **kwargs):
        self._filter.update(kwargs)
        return self

    def order(self, *args):
        self._order = args
        return self

    async def execute(self):
        index_key = ':'.join(['custom', self.model.key_prefix()] + list(self._order))
        first_iteration = True
        result_list = list()
        for key, val in self._filter.items():
            look_up_string = '{}:{}:'.format(key, val)
            temp_list = [x.decode().partition('\x00')[2] for x in await self.db.zrangebylex(
                index_key,
                min="{look_up_string}".format(look_up_string=look_up_string).encode(),
                max="{look_up_string}\xff".format(look_up_string=look_up_string).encode(),
            )]
            if first_iteration:
                result_list = temp_list
                first_iteration = False
            else:
                result_list = list(filter(lambda x: x in result_list, temp_list))

        futures = []
        for key in result_list:
            futures.append(self.model.load(self.db, key))

        return await asyncio.gather(*futures)
