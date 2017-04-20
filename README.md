# subconscious

In-memory database for python3.6+ only

[![Build Status](https://api.travis-ci.com/paxos-bankchain/subconscious.svg?token=PA4epyQZ24dEsEEpEEEZ&branch=develop)](https://travis-ci.com/paxos-bankchain/subconscious)

## Install

From [PyPi](https://pypi.python.org/pypi/subconscious):
```bash
$ pip3 install subconscious
```

## Quickstart

Let's say you have the following in your `models.py` file:
```python
from enum import Enum
from subconscious.model import RedisModel
from subconscious.column import Column

class User(RedisModel):

    # This can be defined inside this class (easier imports) or elsewhere
    class Gender(Enum):
        MALE = 'male'
        FEMALE = 'female'

    uuid = Column(type=str, primary_key=True)
    name = Column(type=str, required=True)
    age = Column(index=True, type=int, sort=True, required=True)
    gender = Column(index=True, enum=Gender)
    country_code = Column(type=str, index=True)
```

Then somewhere you can use that model like this:
```python
from aioredis import create_redis
from asyncio import get_event_loop
from models import User
from uuid import uuid4

loop = get_event_loop()

async def go():
    db = await create_redis(('localhost', 6379), loop=loop, encoding='utf-8')
    my_uuid = str(uuid4())
    my_user = User(
        uuid=my_uuid,
        name='John Doe',
        age=30,
        gender=User.Gender.MALE.value,
        country_code='USA',
    )
    print('Saving user with uuid {}...'.format(my_uuid))
    await my_user.save(db)
    retrieved_user = await User.load(db, my_uuid)
    print('Retrieved {}'.format(retrieved_user.as_dict()))

loop.run_until_complete(go())
```

Which results in:
```
Saving user with uuid 153d68ff-2897-4385-af0c-fea986a68d1f...
Retrieved {'age': 30, 'country_code': 'USA', 'gender': 'male', 'name': 'John Doe', 'uuid': '153d68ff-2897-4385-af0c-fea986a68d1f'}
```

You can also do advanced queries like this:
```python
users = await User.filter_by(
    db=db,
    age=[18, 19, 20, 21, 22],
    country_code='USA',
    gender=User.Gender.MALE,
)
```

Or use an async generator like this:
```python
[async for user in await User.all(
    db=db,
    order_by='age',  # you can also do '-age' for reverse sort
    limit=10,
)]
```

## More Examples
See our demo app for a live example: https://github.com/paxos-bankchain/pastey

## Test

Run redis. We recommend using [docker](https://www.docker.com/community-edition):
```bash
$  docker run -p 6379:6379 redis
```
(you can use `-d` to daemonize this process)

Instll [nose](http://nose.readthedocs.io/en/latest/]):
```bash
$ pip3 install nose
```

Confirm tests pass:
```
$ nosetests .
```

## Contribute

Check out repo:
```bash
$ git checkout git+https://github.com/paxos-bankchain/subconscious.git && cd subconscious
```

Install locally
```bash
pip3 install --editable
```

Make some changes and confirm that tests still pass

---

## Updating PyPi

You must have the credentials in order to push updates to [PyPi](https://pypi.python.org/pypi).

### Do it Live
Create a `.pypirc` file in your home directory:
```
$ cat ~/.pypirc
[distutils]
index-servers=
    pypi

[pypi]
repository = https://pypi.python.org/pypi
username = paxos
password = <password goes here>
```

Create a distribution:
```
$ python setup.py sdist bdist_wheel
```

Push your distribution to PyPi (may need to `pip3 install twine` first):
```
$ twine upload dist/* -r pypi
```

### Testing

To test this process, you can use [PyPi's test server](https://testpypi.python.org/). Add an entry to `.pypirc` that looks like this with whatever creds you create for testpypi:
```
[testpypi]
repository = https://testpypi.python.org/pypi
username = <your user name goes here>
password = <your password goes here>
```

Then use the following command to push your distrobution to test PyPi:
```
$ twine upload dist/* -r testpypi
```
