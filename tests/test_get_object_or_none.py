from subconscious.model import RedisModel, Column
from .base import BaseTestCase
import enum


class StatusEnum(enum.Enum):
    ACTIVE = 'active'


class Diner(RedisModel):
    table_num = Column(composite_key=True, type=int)
    seat_num = Column(composite_key=True, type=int)
    comments = Column(type=str)


class TestGetObectOrNone(BaseTestCase):
    def setUp(self):
        super(TestGetObectOrNone, self).setUp()

        diner = Diner(
            table_num=1,
            seat_num=4,
            comments='Very polite',
        )
        ret = self.loop.run_until_complete(diner.save(self.db))
        self.assertTrue(ret)
        diner = Diner(
            table_num=2,
            seat_num=5,
            comments='Very rude',
        )
        ret = self.loop.run_until_complete(diner.save(self.db))
        self.assertTrue(ret)

    def test_get_object_or_none(self):
        diner = self.loop.run_until_complete(Diner.get_object_or_none(self.db, table_num=1))
        self.assertIsNotNone(diner)
        self.assertEqual(Diner, type(diner))

        # Not existing in the db
        diner = self.loop.run_until_complete(Diner.get_object_or_none(self.db, table_num=999))
        self.assertIsNone(diner)

        diner = self.loop.run_until_complete(Diner.get_object_or_none(self.db, table_num=[1, 2]))
        self.assertIsNotNone(diner)
        self.assertEqual(Diner, type(diner))
