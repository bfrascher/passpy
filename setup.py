#!/usr/bin/env python3

from setuptools import setup


with open("README.md", "r") as f:
    long_description = f.read()


setup(
    name='passpy',
    version='1.0.1',
    description='ZX2C4\'s pass compatible Python library and cli',
    long_description=long_description,
    long_description_content_type='text/markdown',
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
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
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
