import aioredis
import asyncio
from unittest import TestCase


class BaseTestCase(TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(None)
        db_co = aioredis.create_redis(
            address=('localhost', 6379),
            db=13,
            loop=self.loop,
        )
        self.db = self.loop.run_until_complete(db_co)

    def tearDown(self):
        self.loop.run_until_complete(self.db.flushall())
