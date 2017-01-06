from subconscious.model import RedisModel, Column
from uuid import uuid1
from .base import BaseTestCase
import enum


class StatusEnum(enum.Enum):
    ACTIVE = 'active'


class TestUser(RedisModel):
    id = Column(primary_key=True)
    name = Column(index=True, sort=True)
    age = Column(index=True, type=int,)
    locale = Column(index=True, type=int, required=False)
    status = Column(type=str, enum=StatusEnum)


class TestAll(BaseTestCase):

    def setUp(self):
        super(TestAll, self).setUp()
        user_id = str(uuid1())
        user = TestUser(id=user_id, name='Test name', age=100, status='active')
        ret = self.loop.run_until_complete(user.save(self.db))
        self.assertTrue(ret)

        user_id = str(uuid1())
        user1 = TestUser(id=user_id, name='ZTest name', age=53)
        ret = self.loop.run_until_complete(user1.save(self.db))
        self.assertTrue(ret)

        user_id = str(uuid1())
        user1 = TestUser(id=user_id, name='Test name2', age=53)
        ret = self.loop.run_until_complete(user1.save(self.db))
        self.assertTrue(ret)

    def test_all(self):
        async def _test_all():
            for x in await TestUser.all(db=self.db):
                self.assertEqual(type(x), TestUser)
                self.assertTrue(x.name in ('Test name', 'ZTest name', 'Test name2'))
                self.assertTrue(x.age in (100, 53))
        self.loop.run_until_complete(_test_all())

    def test_all_with_order(self):
        users = self.loop.run_until_complete(TestUser.all(db=self.db, order_by='name'))
        self.assertEqual('Test name', users[0].name)
        self.assertEqual('Test name2', users[1].name)
        self.assertEqual('ZTest name', users[2].name)

        users = self.loop.run_until_complete(TestUser.all(db=self.db, order_by='-name'))
        self.assertEqual('ZTest name', users[0].name)
        self.assertEqual('Test name2', users[1].name)
        self.assertEqual('Test name', users[2].name)

        # update a record to force sort order change
        user = users[0]
        user.name = 'AATest name'
        self.loop.run_until_complete(user.save(self.db))
        users = self.loop.run_until_complete(TestUser.all(db=self.db, order_by='name'))
        self.assertEqual('AATest name', users[0].name)
        self.assertEqual('Test name', users[1].name)
        self.assertEqual('Test name2', users[2].name)

    def test_filter_by_non_existing_fields(self):
        # Calls to filter_by with non existing fields should throw AssertionError
        self.assertRaises(
            AssertionError,
            lambda: self.loop.run_until_complete(TestUser.filter_by(
                db=self.db,
                non_existing1='dummy',
                non_existing2=1
            )))

    def test_filter_by_non_indexed_filed(self):
        # Calls to filter_by with non indexed fields should throw AssertionError
        self.assertRaises(
            AssertionError,
            lambda: self.loop.run_until_complete(TestUser.filter_by(
                db=self.db,
                status='active',
            )))
