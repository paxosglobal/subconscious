from subconscious.model import RedisModel, Column
from .base import BaseTestCase
import enum


class StatusEnum(enum.Enum):
    ACTIVE = 'active'


class Diner(RedisModel):
    table_num = Column(composite_key=True, type=int)
    seat_num = Column(composite_key=True, type=int)
    comments = Column(type=str)


class TestCompositeKeys(BaseTestCase):

    def setUp(self):
        super(TestCompositeKeys, self).setUp()

        diner = Diner(
            table_num=1,
            seat_num=4,
            comments='Very polite',
        )
        ret = self.loop.run_until_complete(diner.save(self.db))
        self.assertTrue(ret)

    def test_valid_composite_key_should_return(self):
        results = self.loop.run_until_complete(Diner.filter_by(
            db=self.db,
            table_num=1,
            seat_num=4,
        ))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].comments, 'Very polite')

    def test_partial_composite_key_should_succeed(self):
        # FIXME: is this really the desired behavior?
        results = self.loop.run_until_complete(Diner.filter_by(
            db=self.db,
            table_num=1,
        ))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].comments, 'Very polite')
