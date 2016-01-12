# pypass -- A Python implementation of ZX2C4's pass.
# Copyright (C) 2016 Benedikt Rascher-Friesenhausen <benediktrascherfriesenhausen@gmail.com>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import logging

from git import (
    Repo,
    InvalidGitRepositoryError,
    NoSuchPathError
)


def _git_list_dir(path):
    """List all non git entries in directory.

    When specifying a directory to GitPython currently all files will
    be found, even the on .git directories.  To prevent these files
    from being added this function lists all entries in a directory
    but ommits any found .git directories.

    :param str path: The directory to list the entries of.

    :rtype: list
    :returns: A list of entries in `path` or `None` if `path` is not a
        directory.

    """
    if path is None:
        return None
    if not os.path.isdir(path):
        return None
    return [entry for entry in os.listdir(path)
            if entry != '.git']


def _get_git_repository(path):
    """Get the git repository at path.

    :param str path: The path of a git repository to return.

    :rtype: :cls:``git.Repo``
    :returns: The git repository at path or None if no repository
        exists.

    """
    repo = None
    try:
        repo = Repo(path)
    except InvalidGitRepositoryError:
        logging.debug("'{}' is not a valid git repository."
                          .format(path))
    except NoSuchPathError:
        logging.debug("'{}' is not a valid path."
                      .format(path))
    return repo


def _git_reset(repo):
    """Reset the index to the current commit.

    :param repo: The repository to use
    :type repo: :cls:``git.Repo``
    """
    repo.index.reset()


def _git_commit(repo, msg):
    """Commit the current changes.

    :param repo: The repository to use.
    :type repo: :cls:``git.Repo``

    :param str msg: The commit message.
    """
    if repo is None:
        return
    repo.git.commit(m=msg)


def _git_add_path(repo, path, msg, commit=True):
    """Add a file or directory to the git repository and commit.

    :param repo: The git repository.  If None the function will
        silently fail.
    :type repo: :cls:``git.Repo``

    :param path: The path of the file to commit relative
        to ``store_dir``.
    :type path: str or list

    :param str msg: The commit message.

    :param bool commit: (optional) If `True` the added file will also
        be commited. Default: `True`.

    :raises: ``OSError`` if something went wrong with adding the
        files.

    """
    if repo is None:
        return
    if not isinstance(path, list):
        path = [path]
    repo.git.add(*path)
    if commit:
        _git_commit(repo, msg)


def _git_remove_path(repo, path, msg, recursive=False, commit=True):
    """Remove the file or directory at path from the repository and commit.

    :param repo: The git repository.  If None the function will
        silently fail.
    :type repo: :class:`git.Repo`

    :param path: The file or directory to remove.
    :type path: str or list

    :param str msg: The commit message.

    :param bool recursive: (optional) Set to `True` if directories
        should be removed from the repository recursively.  Default:
        `False`.

    """
    if repo is None:
        return
    if not isinstance(path, list):
        path = [path]
    repo.git.rm(*path, r=True)
    if commit:
        _git_commit(repo, msg)


def _git_init(path):
    return Repo.init(path)


def _git_config(repo, *args):
    repo.git.config(args)
