from subconscious.model import RedisModel, Column, InvalidQuery
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
            async for x in TestUser.all(db=self.db):
                self.assertEqual(type(x), TestUser)
                self.assertTrue(x.name in ('Test name', 'ZTest name', 'Test name2'))
                self.assertTrue(x.age in (100, 53))
        self.loop.run_until_complete(_test_all())

    def test_all_with_order(self):
        async def _test():

            expected_in_order = ['Test name', 'Test name2', 'ZTest name']
            result_list = []
            async for x in TestUser.all(db=self.db, order_by='name'):
                result_list.append(x.name)
            self.assertEqual(result_list, expected_in_order)

            expected_in_order.sort(reverse=True)
            result_list = []
            async for x in TestUser.all(db=self.db, order_by='-name'):
                result_list.append(x)
            self.assertEqual([x.name for x in result_list], expected_in_order)

            # update a record to force sort order change
            result_list[0].name = 'AATest name'
            await result_list[0].save(self.db)
            result_list = []
            expected_in_order = ['AATest name', 'Test name', 'Test name2']
            async for x in TestUser.all(db=self.db, order_by='name'):
                result_list.append(x)
            self.assertEqual([x.name for x in result_list], expected_in_order)

        self.loop.run_until_complete(_test())

    def test_filter_by_non_existing_fields_should_fail(self):
        async def _test():
            async for x in TestUser.filter_by(db=self.db, non_existing1='dummy', non_existing2=1):
                assert x  # Just to satisfy flake8
        with self.assertRaises(InvalidQuery):
            self.loop.run_until_complete(_test())

    def test_filter_by_non_indexed_field_should_fail(self):
        async def _test():
            async for x in TestUser.filter_by(db=self.db, status='active',):
                assert x  # Just to satisfy flake8
        with self.assertRaises(InvalidQuery):
            self.loop.run_until_complete(_test())

    def test_all_iter(self):
        names_in_expected_order = ['Test name', 'Test name2', 'ZTest name']
        result_array = []

        async def _test_loop():
            count = 0
            async for x in TestUser.all(db=self.db, order_by='name'):
                self.assertEqual(x.name, names_in_expected_order[count])
                count += 1
                result_array.append(x.name)
            self.assertEqual(names_in_expected_order, result_array)

        self.loop.run_until_complete(_test_loop())


class TestAllLimitOffset(TestAll):

    def test_limit_only(self):
        async def _test():
            result_array = []
            async for x in TestUser.all(db=self.db, order_by='name', limit=1):
                result_array.append(x.name)
            self.assertEqual(result_array, ['Test name'])
        self.loop.run_until_complete(_test())

    def test_limit_and_offset(self):
        async def _test():
            result_array = []
            async for x in TestUser.all(db=self.db, order_by='name', limit=1, offset=1):
                result_array.append(x.name)
            self.assertEqual(result_array, ['Test name2'])
        self.loop.run_until_complete(_test())

    def test_offset_only(self):
        async def _test():
            result_array = []
            async for x in TestUser.all(db=self.db, order_by='name', offset=1):
                result_array.append(x.name)
            self.assertEqual(result_array, ['Test name2', 'ZTest name'])
        self.loop.run_until_complete(_test())

    def test_over_offset(self):
        async def _test():
            result_array = []
            async for x in TestUser.all(db=self.db, order_by='name', offset=999):
                result_array.append(x.name)
            self.assertEqual(result_array, [])
        self.loop.run_until_complete(_test())

    def test_nonbinding_limit(self):
        async def _test():
            result_array = []
            async for x in TestUser.all(db=self.db, order_by='name', limit=999):
                result_array.append(x.name)
            self.assertEqual(result_array, ['Test name', 'Test name2', 'ZTest name'])
        self.loop.run_until_complete(_test())
