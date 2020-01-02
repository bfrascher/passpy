passpy
======

passpy has been written to be a platform independent library and cli
that is compatible with `ZX2C4's pass`_.

.. _ZX2C4's pass: http://www.passwordstore.org

passpy saves your passwords in gpg encrypted files and optionally uses git as a
revision tool.  All files are stored inside the directory given by the
`PASSWORD_STORE_DIR` environment variable (`~/.password-store` if not set) and
can be organised into folders.  You can also just copy the whole store to have
your passwords available where ever you like.

Installation
------------

PyPI
~~~~

Just do
``$ [sudo] pip install passpy``

Arch Linux
~~~~~~~~~~

The package ``python-passpy`` is available in the AUR for you to install
however you like.

Manually
~~~~~~~~

Either clone the git repository using
``$ git clone https://github.com/bfrascher/passpy.git``

or download the source from the releases tab and extract it.
Afterwards change into the new folder and do
``$ [sudo] python setup.py install``

Dependencies
------------

passpy depends on Python 3.3 or later (it has mostly been tested using
Python 3.5).  The program makes use of `git`_ and `gpg2`_ as well as
either xclip or xsel on Linux.

.. _git: https://www.git-scm.com
.. _gpg2: https://gnupg.org

The following Python packages will be installed alongside passpy:

- `gitpython`_

  .. _gitpython: https://github.com/gitpython-developers/GitPython

- `python-gnupg`_

  .. _python-gnupg: https://bitbucket.org/vinay.sajip/python-gnupg

- `click`_

  .. _click: http://click.pocoo.org/

- `pyperclip`_

  .. _pyperclip: https://github.com/asweigart/pyperclip

If you are on Windows and want colourised output on the command line,
you will additionally need to install `colorama`_.

.. _colorama: https://github.com/tartley/colorama

Changelog
---------

1.0.1
~~~~~

- Fix documentation.

1.0.0
~~~~~

- Read the default password store location from the `PASSWORD_STORE_DIR`
  environment variable, just like `pass` does (contributed by Jonathan Waldrep).

Contents
========

.. toctree::
   :maxdepth: 2

   tutorial
   difference
   reference



Indices and tables
==================

* :ref:`genindex`
* :ref:`search`
