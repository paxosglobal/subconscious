from distutils.core import setup
import subconscious

setup(
    name='subconscious',
    version=subconscious.__version__,
    packages=['subconscious',
              ],
    url='',
    license='',
    author='paxosdev',
    author_email='',
    description='',
    install_requires=['aioredis']
)
