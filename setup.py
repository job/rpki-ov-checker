#!/usr/bin/env python3
# Copyright (C) 2020 Job Snijders <job@ntt.net>
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

import rpki_ov_checker
version = rpki_ov_checker.__version__

import codecs
import os
import sys

from os.path import abspath, dirname, join
from setuptools import setup, find_packages

here = abspath(dirname(__file__))


def parse_requirements(filename):
    """ load requirements from a pip requirements file """
    lineiter = (line.strip() for line in open(filename))
    return [line for line in lineiter if line and not line.startswith("#")]

with codecs.open(join(here, 'README.md'), encoding='utf-8') as f:
    README = f.read()

if sys.argv[-1] == 'publish':
    os.system('python3 setup.py sdist upload')
    print("You probably want to also tag the version now:")
    print(("  git tag -a %s -m 'version %s'" % (version, version)))
    print("  git push --tags")
    sys.exit()

install_reqs = parse_requirements('requirements.txt')
reqs = install_reqs

setup(
    name='rpki-ov-checker',
    version=version,
    maintainer="Job Snijders",
    maintainer_email='job@ntt.net',
    url='https://github.com/job/rpki-ov-checker',
    description='RPKI Origin Validation checker',
    long_description=README,
    long_description_content_type="text/markdown",
    license='ISCL',
    keywords='rpki prefix routing networking',
    setup_requires=reqs,
    install_requires=reqs,
    classifiers=[
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Networking',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3 :: Only'
    ],
    packages=find_packages(exclude=['tests', 'tests.*']),
    entry_points={'console_scripts':
                  ['rpki-ov-checker = rpki_ov_checker.checker:main']},
)
