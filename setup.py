#!/usr/bin/env python

import os
from setuptools import setup

__author__ = 'Akretion : david.beal@akretion.com sebastien.beau@akretion.com'
__version__ = '0.1.0'

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    # Basic package information.
    name = 'ebaypyt',
    version = __version__,

    # Packaging options.
    include_package_data = True,

    # Package dependencies.
    install_requires = ['uuid', 'lxml'],

    # Metadata for PyPI.
    author = 'David Beal, Sebastien Beau',
    author_email = 'david.beal@akretion.com, sebastien.beau@akretion.com',
    license = 'GNU AGPL-3',
    url = 'https://github.com/Akretion/ebaypyt.git',
    packages=['ebaypyt'],
    keywords = 'ebay api client',
    description = 'A library to access Ebay Web Service from Python.',
    long_description = read('README.md'),
    classifiers = [
        'Development Status :: 1 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Internet :: WWW/HTTP :: Site Management',
        'Topic :: Internet'
    ]
)
