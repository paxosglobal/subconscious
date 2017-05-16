#!/usr/bin/env python3

from setuptools import setup, find_packages


setup(
    name='subconscious',
    version='0.08.5',
    packages=find_packages(),
    url='https://github.com/paxos-bankchain/subconscious',
    license='MIT',
    author='Paxos Trust Company, LLC',
    author_email='pypi@paxos.com',
    description='redis-backed db for python3 (asyncio compatible)',
    install_requires=['aioredis'],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        # async_generator requires python3.6+
        'Programming Language :: Python :: 3.6',
    ],
)
