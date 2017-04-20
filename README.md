# subconscious

In-memory database for python3.6+ only

[![Build Status](https://travis-ci.com/paxos-bankchain/subconscious.svg?branch=master)](https://travis-ci.com/paxos-bankchain/subconscious)

## Install

From [PyPi](https://pypi.python.org/pypi/subconscious):
```bash
$ pip3 install subconscious
```

From [GitHub](https://github.com/paxos-bankchain/dsert/):
```bash
$ pip3 install git+https://github.com/paxos-bankchain/subconscious.git
```

## Examples
See our demo app for a complete example: https://github.com/paxos-bankchain/pastey

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

Install twine:
```
$ pip3 install twine
```

Create a distribution:
```
$ python setup.py sdist bdist_wheel
```

Push your distribution to PyPi:
```
$ twine upload dist/* -r pypi
```

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
