=========
Changelog
=========

2.0
---

The change in the major version number comes mostly from the fact,
that most function names in :class:`passpy.store.Store` have changed.
Therefore this version is incompatible with the previously released
1.0rc2.  Beyond that bugs were fixed, the documentation improved and
tests added.

- Fixed forgetting a trailing '/' in the copy/move functions.
- Improved interacting directly with git from the command line.
- Adapted some output from the command line interface to be more like
  the one from pass.
- Improved error message when trying to access a path outside the
  password store.
- Fix handling when deleting a .gpg-id for a subfolder.
- Prevent deleting the .gpg-id for the root directory of the password store.
