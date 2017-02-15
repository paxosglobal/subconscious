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
            encoding='utf-8',
        )
        self.db = self.loop.run_until_complete(db_co)

    def tearDown(self):
        async def delete_all():
            async for k in self.db.iscan(match='*Test*', count=100):
                await self.db.delete(k)
        self.loop.run_until_complete(delete_all())
