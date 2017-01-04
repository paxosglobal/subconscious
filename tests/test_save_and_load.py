import asyncio
from subconscious.columns import Column
from subconscious.model import Model
from uuid import uuid1
from .base import BaseTestCase
import enum


class StatusEnum(enum.Enum):
    ACTIVE = 'active'


class User(Model):
    id = Column(pk=True)
    name = Column(index=True)
    age = Column(index=True, col_type=int)
    locale = Column(index=True, col_type=int, required=False)
    status = Column(col_type=str, enum=StatusEnum)
    _custom_indexes = {('name', 'age'), ('age', 'name'), ('name',)}


class UserComposite(Model):
    id = Column(index=True)
    name = Column(index=True, composite=True)
    age = Column(index=True, composite=True, col_type=int)
    _custom_indexes = {('name', 'age'), ('age', 'name'), ('name',)}


class TestSave(BaseTestCase):

    def test_save_and_get(self):
        user_id = str(uuid1())
        user = User(id=user_id, name='Test name', age=100, status='active')
        ret = self.loop.run_until_complete(user.save(self.db))
        self.assertTrue(ret)

        user_in_db = self.loop.run_until_complete(User.load(self.db, identifier=user_id))
        self.assertEqual(user_in_db.name, 'Test name')
        self.assertIsNone(user_in_db.locale)

        self.assertEqual(type(user_in_db.age), int)

        # update
        user_in_db.name = 'Test name updated'
        ret = self.loop.run_until_complete(user_in_db.save(self.db))
        self.assertTrue(ret)

        user_in_db = self.loop.run_until_complete(User.load(self.db, identifier=user_id))
        self.assertEqual(type(user_in_db), User)
        self.assertEqual(user_in_db.name, 'Test name updated')

        # Test get_by
        asyncio.set_event_loop(self.loop)
        users = self.loop.run_until_complete(User.get_by(self.db, age=100))
        self.assertEqual(len(users), 1)
        self.assertEqual(type(users[0]), User)
        users = self.loop.run_until_complete(User.get_by(self.db, age=102))
        self.assertEqual(len(users), 0)
        # add one more user
        user_id = str(uuid1())
        user1 = User(id=user_id, name='Test name 2', age=100)
        ret = self.loop.run_until_complete(user1.save(self.db))
        self.assertTrue(ret)

        # get by age
        users = self.loop.run_until_complete(User.get_by(self.db, age=100))
        self.assertEqual(len(users), 2)

        for user in users:
            self.assertEqual(type(user), User)

        # get by name
        users = self.loop.run_until_complete(User.get_by(self.db, name=['Test name 2', 'Test name updated']))
        self.assertEqual(len(users), 2)

        for user in users:
            self.assertEqual(type(user), User)

    def test_composite_save_and_load(self):
        user_id = str(uuid1())
        user = UserComposite(id=user_id, name='Test name', age=100)
        ret = self.loop.run_until_complete(user.save(self.db))
        self.assertTrue(ret)

        user_in_db = self.loop.run_until_complete(UserComposite.load(self.db, identifier=('100', 'Test name')))
        self.assertEqual(user_in_db.name, 'Test name')
        self.assertEqual(type(user_in_db.age), int)

        # update
        user_in_db.id = 'updated id'
        ret = self.loop.run_until_complete(user_in_db.save(self.db))
        self.assertTrue(ret)

        user_in_db = self.loop.run_until_complete(UserComposite.load(self.db, identifier=('100', 'Test name')))
        self.assertEqual(type(user_in_db), UserComposite)
        self.assertEqual(user_in_db.id, 'updated id')

    def test_get_by_using_pk(self):
        user_id = str(uuid1())
        user = User(id=user_id, name='Test name', age=100, status='active')
        ret = self.loop.run_until_complete(user.save(self.db))
        self.assertTrue(ret)
        asyncio.set_event_loop(self.loop)
        users_in_db = self.loop.run_until_complete(User.get_by(self.db, id=user_id))
        self.assertTrue(len(users_in_db), 1)
