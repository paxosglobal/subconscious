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


class TestAll(BaseTestCase):
    def test_all(self):

        user_id = str(uuid1())
        user = User(id=user_id, name='Test name', age=100, status='active')
        ret = self.loop.run_until_complete(user.save(self.db))
        self.assertTrue(ret)

        user_id = str(uuid1())
        user1 = User(id=user_id, name='Test name 2', age=53)
        ret = self.loop.run_until_complete(user1.save(self.db))
        self.assertTrue(ret)

        async def _test_all():
            async for x in await User.all(db=self.db):
                self.assertEqual(type(x), User)
                self.assertTrue(x.name in ('Test name', 'Test name 2'))
                self.assertTrue(x.age in (100, 53))
        self.loop.run_until_complete(_test_all())
