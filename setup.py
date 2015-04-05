#!/usr/bin/env python

VERSION     = '1.0.0'
DESCRIPTION = 'Implements the core Paxos algorithm as a set of composable classes'

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


setup(
    name             = 'composable_paxos',
    version          = VERSION,
    description      = DESCRIPTION,
    license          = "MIT",
    long_description = "Implements the core Paxos algorithm as a set of composable classes",
    url              = 'https://github.com/cocagne/python-composable-paxos',
    author           = "Tom Cocagne",
    author_email     = 'tom.cocagne@gmail.com',
    provides         = ['composable_paxos'],
    py_modules       = ['composable_paxos'],
    keywords         = ['paxos'],
    classifiers      = ['Development Status :: 5 - Production/Stable',
                        'Intended Audience :: Developers',
                        'License :: OSI Approved :: MIT License',
                        'Programming Language :: Python',
                        'Topic :: Software Development :: Libraries',
                        'Topic :: System :: Networking'],
    )

