Usage
=====

CLI
---

Setting up the password store
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To initialise a new password store use::

  $ passpy init "passpy gpg id"
  Password store initialised for passpy gpg id.

where ``passpy gpg id`` is the ID of the GPG key to encrypt the
password files with.  You can use different IDs for different folders
inside the store by adding the ``-path`` or ``-p`` option.  It is also
possible to use multiple IDs instead of just one.

If you want to use git to revision your passwords you can initialise
it with::

  $ passpy git init

By calling ``passpy git [...]`` you can directly interact with git
acting on the password store to e.g. add remotes to push/pull to/from
them.


Using the password store
~~~~~~~~~~~~~~~~~~~~~~~~

You can use the ``--help`` option on any command to get all the
available options.

To list all existing passwords in the password store use::

  $ passpy ls
  Password Store
  |-- Email
  |   |-- google.com
  |   `-- yahoo.com
  |-- Programming
  |   |-- github.com
  |   `-- Python
  |       |-- python.org
  |       `-- readthedocs.org
  `-- Notes
      `-- Wi-Fi
          |-- home
          `-- work

We can show a password::

  $ passpy show Email/google.com
  z.Rw6$`U=2MZs(i9\>-r

or copy it to the clipboard::

  $ passpy show -c Email/google.com
  Copied Email/google.com to the clipboard.

When accessing a password you will be prompted to enter your password
for the encryption key.  If you have a running ``gpg-agent`` you can
configure it, so that you stay authenticated for several minutes.
This helps especially when accessing multiple passwords in short
order, e.g. when moving passwords and reencrypting them.

To add an existing password to the store use::

  $ passpy insert Webshop/amazon.com
  Enter password for Webshop/amazon.com:
  Repeat for confirmation:

Using the ``--echo`` or ``-e`` option you won't be prompted to repeat
the password.  With ``--multiline`` or ``-m`` you can enter multiple
lines, or you can use ``$ passpy edit pass-name`` to edit password
files with your default text editor.

To let passpy generate a password for you, use::

  $ passpy generate Social/facebook.com 16
  The generated password for Social/facebook.com is:
  &,"S_Bq}qWKW&<^f

If you don't want any symbols in your password use the
``--no-symbols`` or ``-n`` option.  Like ``show`` you can copy the
generated password to the clipboard with ``--clip`` or ``-c`` and
``--in-place`` or ``-i`` will overwrite the first line of an existing
password file with the new password.

To copy or move a password file or folder in the password store use::

  $ passpy cp/mv Webshop Webshops
  /home/user/.password-store/Webshop/amazon.com.gpg -> /home/user/.password-store/Webshops/amazon.com.gpg

To avoid being prompted for every file that already exists at the
destination, use the ``--force`` or ``-f`` option.  When using a
trailing ``/`` in the destination name, the destination will always be
treated as a directory.

Finally, you can delete a password file ::

  $ passpy rm Social/facebook.com
  Really delete Social/facebook.com? [y/N] y
  removed Social/facebook.com

Passing the ``--force`` or ``-f`` option will delete the file without
asking and ``--recursive`` or ``-r`` will delete whole directories, if
one is given.


Library
-------

To use passpy in your Python project, we will first have to create a
new :class:`passpy.store.Store` object

   >>> import passpy
   >>> store = passpy.Store()

If git or gpg2 are not in your PATH you will have to specify them via
``git_bin`` and ``gpg_bin`` when creating the ``store`` object.  You
can also create the store on a different folder, be passing
``store_dir`` along.

To initialise the password store at ``store_dir``, if it isn't
already, use

   >>> store.init_store('store gpg id')

where ``store gpg id`` is the name of a GPG ID.  Optionally, git can
be initialised in very much the same way

   >>> store.init_git()

You are now ready to interact with the password store.  You can set
and get keys using :func:`passpy.store.Store.set_key` and
:func:`passpy.store.Store.get_key`.
:func:`passpy.store.Store.gen_key` generates a new password for a new
or existing key.  To delete a key or directory, use
:func:`passpy.store.Store.remove_path`.

For a full overview over all available methods see
:ref:`store-module-label`.



Data Organisation
-----------------

You are free to organise your files in the store however you like.
But, as the ``--clip`` or ``-c`` option only copies the first line of
a password file to the clipboard and the ``--in-place`` or ``-i``
option overwrites the first line with a new password, it is
recommended that you have your password on the first line for each
password file.  That way it is easy to fetch a password for a login
form or update an existing password file.

Some users might want to store additional information for a store
entry, like a websites URL, the username and so on.  There are many
methods to do this, some of which are listed under `Data Organization`
on the website for `ZX2C4's pass`_.  The authors preferred way to do
this (both for pass and passpy) is to have additional lines under the
first one with a leading keyword.  An entry might look like this::

  z.Rw6$`U=2MZs(i9\>-r
  URL: accounts.google.com/*
  Username: somegoogleuser@gmail.com

  Chrome Sync Password: EK6zzRo4chejRBztuVUF3CvqvRg9E4

.. _ZX2C4's pass: https://www.passwordstore.org

Of course, as said in the beginning of the section, how you organise
your data is completely up to you and this is just one way of doing
things.
