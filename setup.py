import os
from setuptools import setup
from distutils.extension import Extension
from Cython.Build import cythonize

setup(
    name="pley",
    version='0.0.1',
    author="Mike O'Malley",
    author_email="spuriousdata@gmail.com",
    license="MIT",
    packages=['pley'],
    install_requires=['PyYAML', 'requests'],
    ext_modules=cythonize([
        Extension('pley.cformats.flac', ['pley/cformats/flac.pyx'],
            libraries=['FLAC'],
            )
        ], gdb_debug=True),
    entry_points={
        'console_scripts': ['pley=pley.__main__:_main'],
    },
)
