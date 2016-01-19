Usage
=====

CLI
---

To see the command line help, type

  $ python -m pypass

or, if you have also installed pypass to your bin, simply use

  $ pypass

If you don't already have a password store you will need to set up a
new one using

  $ pypass init <gpg-id>

The default location is `~/.password-store`.  To change the location
you can either provide the `--store-dir=<path/to/dir>` option or set
the PYPASS_STORE_DIR environment variable.  The <gpg-id> can be the
name or either short or full ID of one of your gpg keys with which to
encrypt your password store.  You can also provide multiple IDs which
will then be used in sequence when encrypting or decrypting your
passwords.  If you also want to use git as a revision tool for your
password store you can initiate it with

  $ pypass git init

It is recommended that you use a `gpg-agent` together with pypass to
make batch operations like copy/move/delete on your password store
easier.  If you don't have a `gpg-agent` running you should either
provide the `--no-agent`` option or set PYPASS_NO_AGENT in you
environment.

Now that the password store is set up you can begin to add your
passwords or generate new ones.  All passwords are saved in a gpg
encrypted file that you can place anywhere inside the password store
folder.  Let's say you want to set up an account with a new email
provider, you could add it like

  $ pypass generate email/newmail.fake <length>

This way a folder `email` will be created if not already exists and
your new password of length <length> will be saved inside the
`newmail.fake` file.  It will also be printed to the command line.  If
you'd rather have it copied to the clipboard, use the `--clip` or `-c`
option.  You can also use `generate` to create a new password for an
existing file.  By using the `--in-place` or `-i` option the first
line of the provided password file will be overwritten with a newly
generated password.
