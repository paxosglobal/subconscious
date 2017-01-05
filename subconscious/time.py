# python modules
import arrow
import datetime
import logging


logger = logging.getLogger(__name__)


def assert_valid_dt(some_dt):
    if not some_dt:
        raise Exception('No value supplied')
    if type(some_dt) is not datetime.datetime:
        raise Exception('%s is of type %s and not datetime' % (some_dt, type(some_dt)))
    if some_dt.tzinfo is None:
        raise Exception('%s is not timezone aware' % some_dt)


def get_dt_from_iso8601(iso_8601_str):
    " Convert an iso-8601 string to a python datetime object "

    # weak checks to be explicit (arrow will accept other formats)

    if type(iso_8601_str) is not str:
        raise RuntimeError('%s is not of type str' % iso_8601_str)

    for required_char in (':', '-'):
        if required_char not in iso_8601_str:
            raise RuntimeError('Invalid ISO8601 String: %s' % iso_8601_str)

    # convert to datetime in UTC
    arrow_dt = arrow.get(iso_8601_str).datetime
    assert_valid_dt(arrow_dt)
    return arrow_dt


def utcnow_with_tz():
    """
    Create a timezone-aware datetime reflecting utcnow

    utcnow() surprisingly doesn't do this for you!
    http://stackoverflow.com/questions/2331592/datetime-datetime-utcnow-why-no-tzinfo

    Note: for automatically setting times in the DB, use this instead:
    http://stackoverflow.com/a/30083454
    """
    to_return = datetime.datetime.now(datetime.timezone.utc)
    assert_valid_dt(to_return)
    return to_return
