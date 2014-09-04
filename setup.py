#!/usr/bin/env python

from setuptools import setup
from snakebyte import __version__

long_description = "Sunlight FDW"

setup(
    name="snakebyte",
    version=__version__,
    packages=['snakebyte',],
    author="Paul Tagliamonte",
    author_email="paultag@gmail.com",
    long_description=long_description,
    description='does some stuff with things & stuff',
    license="Expat",
    url="",
    platforms=['any']
)
