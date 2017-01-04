from subconscious.columns import Column
from subconscious.model import Model
from uuid import uuid1
from datetime import datetime
from .base import BaseTestCase


class TimestampedModel(Model):
    created_at = Column(col_type=str, index=True)
    updated_at = Column(col_type=str, index=True)

    def __init__(self, **kwargs):
        super(TimestampedModel, self).__init__(**kwargs)
        if kwargs.get('updated_at'):
            self.updated_at = kwargs.pop('updated_at')
        if kwargs.get('created_at'):
            self.created_at = kwargs.pop('created_at')

    async def save(self, db):
        now = datetime.now().isoformat()
        self.updated_at = now
        if not await db.exists(self.redis_key(self.identifier())):
            self.created_at = now
        return await super().save(db)


class User(TimestampedModel):
    id = Column(pk=True)
    name = Column(index=True)
    age = Column(index=True, col_type=int)
    locale = Column(index=True, col_type=int, required=False)


class TestInheritedModel(BaseTestCase):

    def test_inherited(self):
        user_id = str(uuid1())
        user = User(id=user_id, name='Kepler', age=32)
        ret = self.loop.run_until_complete(user.save(self.db))
        self.assertTrue(ret)
        user_in_db = self.loop.run_until_complete(User.load(self.db, identifier=user_id))
        self.assertIsNotNone(user_in_db.created_at)
        self.assertIsNotNone(user_in_db.updated_at)
        created_at_before = user_in_db.created_at
        updated_at_before = user_in_db.updated_at

        user_in_db.age = 35
        ret = self.loop.run_until_complete(user_in_db.save(self.db))
        self.assertTrue(ret)
        user_in_db = self.loop.run_until_complete(User.load(self.db, identifier=user_id))
        self.assertNotEqual(user_in_db.updated_at, updated_at_before)
        self.assertEqual(user_in_db.created_at, created_at_before)

