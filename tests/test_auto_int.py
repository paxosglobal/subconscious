from .base import BaseTestCase
from subconscious.column import Integer, Column
from subconscious.model import RedisModel, BadDataError


class TestUser(RedisModel):
    id = Integer(primary_key=True, auto_increment=True)
    name = Column(type=str)
    auto_id = Integer(auto_increment=True)


class TestAutoInt(BaseTestCase):

    def test_auto(self):
        user = TestUser(name='foo')
        self.loop.run_until_complete(user.save(self.db))
        self.assertEqual(user.id, 1)
        user = TestUser()
        self.loop.run_until_complete(user.save(self.db))
        self.assertEqual(user.id, 2)

    def test_setting_auto_increment_should_throw_bad_data_error(self):
        # via constructor
        with self.assertRaises(BadDataError):
            TestUser(id=777)

        user = TestUser()
        # via attribute mutation
        with self.assertRaises(BadDataError):
            user.id = 424

    def test_load(self):
        user = TestUser(name='foo')
        self.loop.run_until_complete(user.save(self.db))
        user_in_db = self.loop.run_until_complete(TestUser.load(db=self.db, identifier=1))
        self.assertEqual(user.name, user_in_db.name)

    def test_update(self):
        user = TestUser(name='foo')
        self.loop.run_until_complete(user.save(self.db))
        user_in_db = self.loop.run_until_complete(TestUser.load(db=self.db, identifier=1))
        self.assertEqual(user.name, user_in_db.name)
        user_in_db.name = 'bar'
        self.loop.run_until_complete(user_in_db.save(self.db))
        user_in_db = self.loop.run_until_complete(TestUser.load(db=self.db, identifier=1))
        self.assertEqual('bar', user_in_db.name)
