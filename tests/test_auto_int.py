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
        # Provide id
        with self.assertRaises(BadDataError):
            TestUser(id=777)

        user = TestUser()
        user.id = 424
        # Should fail on save
        with self.assertRaises(BadDataError):
            self.loop.run_until_complete(user.save(self.db))
