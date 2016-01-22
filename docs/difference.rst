Differences to ZX2C4's pass
===========================

While passpy is fully compatible with [ZX2C4's
pass](http://www.passwordstore.org), there are some differences:

- As for the moment passpy does not print as many messages to the
  user, as pass does.  Also some messages might be phrased
  differently.

- When invoking ``pass`` without any known command, ``show`` is used.
  passpy always needs to be given a command to invoke.

- passpy allows ``gen`` as a alternative to ``generate``.

- After editing a password file with an editor pass notes the used
  editor in the git commit message.  passpy uses the same message for
  updating a key, regardless if an editor was used or not.  This is
  because for both cases :func:`passpy.store.Store.set_key` is being
  called which also handles the git commit.

- pass lists all files in the password store that do not start with a
  ``.``.  passpy only lists files that end on ``.gpg``.  The reason
  for this change is that the returned key names should be directly
  accessible with :func:`passpy.store.Store.get_key`, which expects a
  file ending on ``.gpg``.
