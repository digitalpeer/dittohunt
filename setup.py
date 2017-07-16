#!/usr/bin/env python
# Copyright (c) 2017 Joshua Henderson <digitalpeer@digitalpeer.com>
#
# SPDX-License-Identifier: GPL-3.0
# coding=utf-8
import sys
from setuptools import setup, find_packages
from setuptools.command.sdist import sdist as _sdist
import subprocess
import codecs
from dittohunt.version import __version__

class sdist(_sdist):
    def run(self):
        try:
            subprocess.check_call('make')
        except subprocess.CalledProcessError as e:
            raise SystemExit(e)
        _sdist.run(self)

try:
    import pypandoc
    README = pypandoc.convert('README.md', 'rst')
except ImportError:
    with codecs.open('README.md', encoding='utf-8') as f:
        README = f.read()

with codecs.open('CHANGES.rst', encoding='utf-8') as f:
    CHANGES = f.read()

setup(
    name='dittohunt',
    version=__version__,
    author='Joshua Henderson',
    author_email='digitalpeer@digitalpeer.com',
    url='https://github.com/digitalpeer/dittohunt',
    download_url='https://github.com/digitalpeer/dittohunt/zipball/master',
    description='A duplicate file finder, previewer, and deleter.',
    long_description=README + '\n\n' + CHANGES,
    packages=find_packages(),
    include_package_data=True,
    package_data={
        '': ['*.txt', '*.rst', '*.md'],
    },
    entry_points={
        'gui_scripts': [
            'dittohunt = dittohunt.dittohunt:main',
        ]
    },
    install_requires=[
        'shutil>=2.3'
    ],
    keywords='file find duplicate',
    classifiers=['Development Status :: 3 - Alpha',
                 'Environment :: X11 Applications :: Qt',
                 'Natural Language :: English',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python :: 2',
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: 3',
                 'Programming Language :: Python :: 3.5',
                 'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
                 'Topic :: Desktop Environment :: File Managers',
                 'Topic :: System :: Filesystems',
                 'Topic :: Utilities',
                 'Intended Audience :: End Users/Desktop',
                 'Intended Audience :: Information Technology',
                 'Intended Audience :: Science/Research',
    ],
    cmdclass={'sdist': sdist},
)
