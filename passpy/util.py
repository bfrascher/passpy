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

import os
import random
import shutil
import string

from functools import wraps

from passpy.exceptions import (
    StoreNotInitialisedError,
    RecursiveCopyMoveError
)


def trap(path_index):
    """Prevent accessing files and directories outside the password store.

    `path_index` is necessary as the functions that need to be trapped
    have different argument lists.  This way we can indicate which
    argument contains the paths that are to be checked.

    :param path_index: The index for the path variable in either
        `args` or `kwargs`.
    :type path_index: int or str

    :rtype: func
    :returns: The trapped function.

    """
    def trap_decorator(func):
        @wraps(func)
        def trap_wrapper(*args, **kwargs):
            try:
                path_list = args[path_index]
            except TypeError:
                try:
                    path_list = kwargs[path_index]
                except KeyError:
                    path_list = None
            except IndexError:
                path_list = None

            if path_list is not None and not isinstance(path_list, list):
                path_list = [path_list]
            if path_list is not None:
                for path in path_list:
                    path = os.path.normpath(path)
                    if path.startswith('..' + os.sep) or path == '..':
                        raise PermissionError('Sneaky!')

            return func(*args, **kwargs)
        return trap_wrapper
    return trap_decorator


def initialised(func):
    """Check that the store is initialised before running.

    Used as a decorator in methods for :class:`passpy.store.Store`.

    :param func: A method of :class:`passpy.store.Store`.
    :type store: function

    :rtype: function
    :returns: The method if the store is initialised.

    :raises passpy.exceptions.StoreNotInitialisedError: if the store
        is not initialised.

    """
    @wraps(func)
    def initialised_wrapper(*args, **kwargs):
        store = args[0]
        if not store.is_init():
            raise StoreNotInitialisedError(
                'You need to initialise the store first.')
        return func(*args, **kwargs)
    return initialised_wrapper


def gen_password(length, symbols=True):
    """Generates a random string.

    Uses :class:`random.SystemRandom` if available and
    :class:`random.Random` otherwise.

    :param int length: The length of the random string.

    :param bool symbols: (optional) If ``True``
        :const:`string.punctuation` will also be used to generate the
        output.

    :rtype: str
    :returns: A random string of length `length`.

    """
    try:
        rand = random.SystemRandom()
    except NotImplementedError:
        rand = random.Random()

    chars = string.ascii_letters + string.digits
    if symbols:
        chars += string.punctuation

    return ''.join(rand.choice(chars) for _ in range(length))


def copy_move(src, dst, force=False, move=False, interactive=False,
               verbose=False):
    """Copies/moves a file or directory recursively.

    This function is partially based on the `cp` function from the
    `pycoreutils`_ package written by Hans van Leeuwen and licensed
    under the MIT license.

    .. _pycoreutils: https://pypi.python.org/pypi/pycoreutils/

    :param str src: The file or directory to be copied.

    :param str dst: The file or directory to be copied to.

    :param bool force: If ``True`` existing files at the destination
        will be silently overwritten.

    :param bool interactive: If ``True`` the user will be prompted for
        every file to be overwritten.  Has no effect if `force` is
        also ``True``.

    :param bool verbose: If ``True`` print the old and new filename
        for every copied/moved file.

    :raises FileNotFoundError: if there exists no key or directory for
        `src`.

    :raises FileExistsError: if a key at `dst` already exists and
        `force` is set to ``False``.

    """
    if move:
        operation = shutil.move
    else:
        operation = shutil.copy

    if os.path.isfile(src):
        if dst.endswith(os.sep) and not os.path.exists(dst):
            os.makedirs(dst, exist_ok=True)
        else:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.isdir(dst):
            dst = os.path.join(dst, os.path.basename(src))

        if os.path.exists(dst) and not force:
            if interactive:
                answer = input('Really overwrite {0}? [y/N] '.format(dst))
                if answer.lower() != 'y':
                    return None
            else:
                raise FileExistsError('{0} already exists.'.format(dst))
        operation(src, dst)
        if verbose:
            print('{0} -> {1}'.format(src, dst))
    elif os.path.isdir(src):
        if os.path.commonpath([src, dst]) == src:
            raise RecursiveCopyMoveError('Can\'t copy or move a '
                                         'directory into itself.')

        if os.path.exists(dst):
            dst = os.path.join(dst, os.path.basename(src))
        if not os.path.exists(dst):
            os.makedirs(dst, exist_ok=True)

        for root, dirs, files in os.walk(src):
            mid = os.path.relpath(root, src)

            for d in dirs:
                dstdir = os.path.normpath(os.path.join(dst, mid, d))
                if not os.path.exists(dstdir):
                    os.mkdir(dstdir)
                    if verbose:
                        print('created directory {0}'.format(dstdir))

            for f in files:
                srcfile = os.path.join(root, f)
                dstfile = os.path.normpath(os.path.join(dst, mid, f))
                if os.path.exists(dstfile) and not force:
                    if interactive:
                        answer = input('Really overwrite {0}? [y/N] '
                                       .format(dstfile))
                        if answer.lower() != 'y':
                            continue
                    else:
                        raise FileExistsError('{0} already exists.'
                                              .format(dstfile))
                operation(srcfile, dstfile)
                if verbose:
                    print('{0} -> {1}'.format(srcfile, dstfile))
    else:
        raise FileNotFoundError('{0} does not exist.'.format(src))

    return dst
