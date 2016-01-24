#!/usr/bin/env python3

import re

from setuptools import setup


with open('passpy/__init__.py', 'r') as init_file:
    version = re.search(r'^__version__ = \'([.\d\w]*)\'',
                        init_file.read(), re.MULTILINE).group(1)

if version is None:
    raise RuntimeError('Could not extract version')


setup(
    name='passpy',
    version=version,
    description='ZX2C4\'s pass compatible Python library and cli',
    url='https://github.com/bfrascher/passpy',
    author='Benedikt Rascher-Friesenhausen',
    author_email='benediktrascherfriesenhausen+passpy@gmail.com',
    license='GPLv3+',
    packages=['passpy'],
    install_requires=[
        'python-gnupg>=0.3.8',
        'GitPython>=1.0.1',
        'pyperclip>=1.5',
        'click>=2.0',
    ],
    extras_require = {
        'color': ['colorama'],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS',
        'Topic :: Utilities',
    ],
    entry_points='''
        [console_scripts]
        passpy=passpy.__main__:cli
    ''',
)
