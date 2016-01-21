Overview
========

pypass has been written to be a platform independent library and cli
that is compatible with `ZX2C4's pass`_.

.. _ZX2C4's pass: http://www.passwordstore.org

pypass uses gpg and optionally git to save and revision your passwords
in a simple directory tree structure.


Installation
------------

To install simply download the `source`_, change into the new directory and call

.. _source: https://github.com/bfrascher/pypass

  $ python setup.py install

This will automatically install all missing Python dependencies and
create an entry script `pypass` that acts as a shortcut for the
command line interface component of pypass.


Dependencies
------------

To use pypass you will need to have Python 3.5 as well as the
following additional applications and python packages installed:

- git
- gpg2
- xclip/xsel (Linux only)
- pbcopy/pbpaste (OSX only)
- `gitpython`_

  .. _gitpython: https://github.com/gitpython-developers/GitPython

- `python-gnupg`_

  .. _python-gnupg: https://bitbucket.org/vinay.sajip/python-gnupg

- `click`_

  .. _click: http://click.pocoo.org/

- `pyperclip`_

  .. _pyperclip: https://github.com/asweigart/pyperclip
