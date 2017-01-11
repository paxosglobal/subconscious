from subconscious.model import RedisModel, Column, InvalidModelDefinition, UnexpectedColumnError
from uuid import uuid1
from .base import BaseTestCase
import enum


class StatusEnum(enum.Enum):
    ACTIVE = 'active'


class TestUser(RedisModel):
    id = Column(primary_key=True)
    name = Column(index=True)
    age = Column(index=True, type=int)
    locale = Column(index=True, type=int, required=False)
    status = Column(type=str, enum=StatusEnum, index=True)


class TestSaveAndLoad(BaseTestCase):

    def test_save_and_load(self):
        user_id = str(uuid1())
        user = TestUser(id=user_id, name='Test name', age=100, status='active')
        ret = self.loop.run_until_complete(user.save(self.db))
        self.assertTrue(ret)

        # load
        user_in_db = self.loop.run_until_complete(TestUser.load(self.db, identifier=user_id))
        self.assertEqual(user_in_db.name, user.name)

    def test_init_model_with_no_indexed_cols_should_error(self):
        with self.assertRaises(InvalidModelDefinition):
            class BadModel(RedisModel):
                unindex_col = Column()


class BadSave(BaseTestCase):

    def test_unexpected_column_should_fail(self):

        class TestModel(RedisModel):
            id = Column(type=int, primary_key=True)

        with self.assertRaises(UnexpectedColumnError):
            TestModel(id=1, this_column_does_not_exist='foo')
