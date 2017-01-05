from subconscious.model import RedisModel, Column
from uuid import uuid1
from .base import BaseTestCase
import enum


class StatusEnum(enum.Enum):
    ACTIVE = 'active'


class TestUser(RedisModel):
    id = Column(primary_key=True)
    name = Column(index=True)
    age = Column(index=True, type=int)
    locale = Column(index=True, type=int, required=False)
    status = Column(type=str, enum=StatusEnum)


class TestAll(BaseTestCase):
    def test_all(self):

        user_id = str(uuid1())
        user = TestUser(id=user_id, name='Test name', age=100, status='active')
        ret = self.loop.run_until_complete(user.save(self.db))
        self.assertTrue(ret)

        user_id = str(uuid1())
        user1 = TestUser(id=user_id, name='Test name 2', age=53)
        ret = self.loop.run_until_complete(user1.save(self.db))
        self.assertTrue(ret)

        async def _test_all():
            for x in await TestUser.all(db=self.db):
                self.assertEqual(type(x), TestUser)
                self.assertTrue(x.name in ('Test name', 'Test name 2'))
                self.assertTrue(x.age in (100, 53))
        self.loop.run_until_complete(_test_all())
