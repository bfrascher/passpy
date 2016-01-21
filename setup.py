#!/usr/bin/env python3

from distutils.core import setup

setup(
    name='pypass',
    version='0.9',
    description='ZX2C4\'s pass compatible Python library and cli',
    url='https://github.com/bfrascher/pypass',
    author='Benedikt Rascher-Friesenhausen',
    author_email='benediktrascherfriesenhausen+pypass@gmail.com',
    license='GPLv3+',
    packages=['pypass'],
    install_requires=[
        'python-gnupg',
        'gitpython',
        'pyperclip',
        'Click',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Developers',
        'License :: GPLv3+',
        'Programming Language :: Python :: 3.5',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: Unix',
        'Operating System :: MacOS',
    ],
    entry_points='''
        [console_scripts]
        pypass=pypass.__main__:cli
    ''',
)
