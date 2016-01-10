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

import logging

from git import (
    Repo,
    InvalidGitRepositoryError,
    NoSuchPathError
)


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


def _git_commit(repo, msg):
    """Commit the current changes.

    :param repo:
    :type repo: :cls:``git.Repo``

    :param str msg: The commit message.
    """
    if repo is None:
        return
    repo.index.commit(msg)


def _git_add_file(repo, path, msg):
    """Add a file or folder to the git repository and commit.

    :param repo: The git repository.  If None the function will
        silently fail.
    :type repo: :cls:``git.Repo``

    :param str path: The path of the file to commit relative to
        ``store_dir``.

    :param str msg: The commit message.

    :raises: ``OSError`` if something went wrong with adding the
        files.

    """
    if repo is None:
        return
    repo.index.add([path])
    _git_commit(repo, msg)


def _git_remove_path(repo, path, msg, recursive=False):
    """Remove the file or folder at path from the repository and commit.

    :param repo: The git repository.  If None the function will
        silently fail.
    :type repo: :cls:``git.Repo``

    :param str path: The file or folder to remove.

    :param str msg: The commit message.

    :param bool recursive: (optional) Set to `True` if folders should
        be removed from the repository recursively.  Default: `False`.

    """
    if repo is None:
        return
    repo.index.remove([path], r=recursive)
    _git_commit(repo, msg)


def _git_init(path):
    return Repo.init(path)


def _git_config(repo, *args):
    repo.git.config(args)
