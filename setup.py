import os
from setuptools import setup

setup(
    name="pley",
    version='0.0.1',
    author="Mike O'Malley",
    author_email="spuriousdata@gmail.com",
    license="MIT",
    packages=['pley'],
    install_requires=['PyYAML', 'requests'],
    entry_points={
        'console_scripts': ['pley=pley.__main__:_main'],
    },
)
