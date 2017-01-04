from distutils.core import setup
import redismodel

setup(
    name='subconscious',
    version=redismodel.__version__,
    packages=['subconscious',
              ],
    url='',
    license='',
    author='paxosdev',
    author_email='',
    description='',
    install_requires=['aioredis']
)
