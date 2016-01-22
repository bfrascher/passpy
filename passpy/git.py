# passpy --  ZX2C4's pass compatible library and cli
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

from git import (
    Repo,
    InvalidGitRepositoryError,
    NoSuchPathError
)


def get_git_repository(path):
    """Get the git repository at path.

    :param str path: The path of a git repository to return.

    :rtype: :class:`git.repo.base.Repo`
    :returns: The git repository at path or None if no repository
        exists.

    """
    try:
        repo = Repo(path)
    except InvalidGitRepositoryError:
        return None
    except NoSuchPathError:
        return None
    return repo


def _git_commit(repo, msg, verbose=False):
    """Commit the current changes.

    :param repo: The repository to use.
    :type repo: :class:`git.repo.base.Repo`

    :param str msg: The commit message.

    :param bool verbose: (optional) If ``True`` git's standard output
        will be printed.

    """
    if repo is None:
        return
    res = repo.git.commit(m=msg)
    if verbose:
        print(res)


def git_add_path(repo, path, msg, commit=True, verbose=False):
    """Add a file or directory to the git repository and commit.

    :param repo: The git repository.  If ``None`` the function will
        silently fail.
    :type repo: :class:`git.repo.base.Repo`

    :param path: The path of the file or directory to commit relative
        to :py:attr:`passpy.store.Store.store_dir`.
    :type path: str or list

    :param str msg: The commit message.

    :param bool commit: (optional) If ``True`` the added file will also
        be commited.

    :param bool verbose: (optional) If ``True`` git's standard output
        will be printed.

    :raises OSError: if something went wrong with adding the files.

    """
    if repo is None:
        return
    if not isinstance(path, list):
        path = [path]
    repo.git.add(*path)
    if commit:
        _git_commit(repo, msg, verbose)


def git_remove_path(repo, path, msg, recursive=False, commit=True,
                    verbose=False):
    """Remove the file or directory at path from the repository and commit.

    :param repo: The git repository.  If ``None`` the function will
        silently fail.
    :type repo: :class:`git.repo.base.Repo`

    :param path: The file or directory to remove.
    :type path: str or list

    :param str msg: The commit message.

    :param bool recursive: (optional) Set to ``True`` if directories
        should be removed from the repository recursively.

    :param bool verbose: (optional) If ``True`` git's standard output
        will be printed.

    """
    if repo is None:
        return
    if not isinstance(path, list):
        path = [path]
    repo.git.rm(*path, r=recursive)
    if commit:
        _git_commit(repo, msg, verbose)


def git_init(path):
    """Create a new git repository.

    :param str path: The absolute path directory to create a git
        repository in.

    :rtype: :class:`git.Repo`
    :returns: The newly initialised git repository.

    """
    return Repo.init(path)


def git_config(repo, *args):
    """Change the configuration of a git repository.

    :param repo: The git repository to change the configuration for.
    :type repo: :class:`git.Repo`

    """
    repo.git.config(args)
