from subconscious.model import RedisModel, Column
from uuid import uuid1
from .base import BaseTestCase
import enum


class StatusEnum(enum.Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'


class TestUser(RedisModel):
    id = Column(primary_key=True)
    name = Column(index=True)
    age = Column(index=True, type=int)
    locale = Column(index=True, type=int, required=False)
    status = Column(type=str, enum=StatusEnum, index=True)


class TestFilterBy(BaseTestCase):
    def setUp(self):
        super(TestFilterBy, self).setUp()
        user = TestUser(id=str(uuid1()), age=0, locale=0+10, status='active')
        self.loop.run_until_complete(user.save(self.db))
        for i in range(9):
            user = TestUser(id=str(uuid1()), name='name-{}'.format(i), age=i, locale=i+10, status='active')
            self.loop.run_until_complete(user.save(self.db))

    def test_filter_by(self):
        users = self.loop.run_until_complete(TestUser.filter_by(self.db, age=1))
        self.assertEqual(1, len(users))

        users = self.loop.run_until_complete(TestUser.filter_by(self.db, age=[1, 2]))
        self.assertEqual(2, len(users))

        users = self.loop.run_until_complete(TestUser.filter_by(self.db, status='active'))
        self.assertEqual(10, len(users))

    def test_get_by(self):
        users = self.loop.run_until_complete(TestUser.get_by(self.db, status='active', age=[1, 2]))
        self.assertEqual(2, len(users))
        users = self.loop.run_until_complete(TestUser.get_by(self.db, status='active'))
        self.assertEqual(10, len(users))
        user = users[0]
        user.status = 'inactive'
        self.loop.run_until_complete(user.save(self.db))
        users = self.loop.run_until_complete(TestUser.get_by(self.db, status='active'))
        # Should be one less now 10 - 1 = 9
        self.assertEqual(9, len(users))

    def test_get_by_none(self):
        users = self.loop.run_until_complete(TestUser.get_by(self.db, name=None))
        self.assertEqual(1, len(users))

