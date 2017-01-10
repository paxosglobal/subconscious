from .base import BaseTestCase
from subconscious.column import Integer, Column
from subconscious.model import RedisModel


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

        # Provide id
        user = TestUser(id=777)
        self.loop.run_until_complete(user.save(self.db))
        self.assertEqual(user.id, 777)
        self.assertEqual(user.auto_id, 3)
