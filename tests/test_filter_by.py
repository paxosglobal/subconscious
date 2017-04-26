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
        async def _test():
            count = 0
            async for x in TestUser.filter_by(self.db, age=1):
                count += 1
            self.assertEqual(1, count)

            count = 0
            async for x in TestUser.filter_by(self.db, age=[1, 2]):
                count += 1
            self.assertEqual(2, count)

            count = 0
            result_list = []
            async for x in TestUser.filter_by(self.db, status='active'):
                count += 1
                self.assertEqual(x.status, 'active')
                result_list.append(x)
            self.assertEqual(10, count)
            result_list[0].status = 'inactive'
            await result_list[0].save(self.db)

            count = 0
            async for x in TestUser.filter_by(self.db, status='active'):
                count += 1
                self.assertEqual(x.status, 'active')
            # Should be one less now
            self.assertEqual(9, count)

        self.loop.run_until_complete(_test())

    def test_get_by_none(self):
        async def _test():
            result_list = []
            async for x in TestUser.filter_by(self.db, name=None):
                result_list.append(x)
            self.assertEqual(1, len(result_list))
        self.loop.run_until_complete(_test())

    def test_query(self):
        async def _test():
            result_list = []
            async for x in TestUser.query(db=self.db).filter(status='active'):
                result_list.append(x)
            self.assertEqual(10, len(result_list))
        self.loop.run_until_complete(_test())

    def test_query_no_filter(self):
        async def _test():
            result_list = []
            async for x in TestUser.query(db=self.db):
                result_list.append(x)
            self.assertEqual(10, len(result_list))
        self.loop.run_until_complete(_test())

    def test_query_first(self):
        async def _test():
            user = await TestUser.query(db=self.db).filter(status='active').first()
            self.assertEqual(TestUser, type(user))
            self.assertEqual(user.status, 'active')
        self.loop.run_until_complete(_test())

    def test_query_first_no_filter(self):
        async def _test():
            user = await TestUser.query(db=self.db).first()
            self.assertEqual(TestUser, type(user))
            self.assertEqual(user.status, 'active')
        self.loop.run_until_complete(_test())

    def test_query_chaining_filters(self):
        async def _test():
            user = await TestUser.query(db=self.db).filter(name='name-1').filter(status='active').first()
            self.assertEqual(TestUser, type(user))
            self.assertEqual(user.status, 'active')
            self.assertEqual(user.name, 'name-1')
        self.loop.run_until_complete(_test())
