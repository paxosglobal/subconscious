import time
import logging

logger = logging.getLogger(__name__)


def timeit(method):

    async def timed(*args, **kw):
        ts = time.time()
        result = await method(*args, **kw)
        te = time.time()
        logger.info('%r (%r, %r) %2.2f sec' % (method.__name__, args, kw, te-ts))
        return result

    return timed
