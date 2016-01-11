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
import random
import re
import shutil
import string

from functools import wraps


def trap(path_index):
    """Decorator to prevent any function from accessing paths outside of
        ``store_dir``.

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
            if isinstance(path_index, str):
                if path_index in kwargs:
                    path_list = kwargs[path_index]
                else:
                    path_list = [None]
            else:
                path_list = args[path_index]
            if not isinstance(path_list, list):
                path_list = [path_list]
            if _contains_sneaky_path(path_list):
                raise PermissionError('Sneaky!')
            return func(*args, **kwargs)
        return trap_wrapper
    return trap_decorator


def _get_parent_dir(path):
    """Returns the parent folder of path.

    :param str path: A file or folder.

    :rtype: str
    :returns: The parent folder of path.  Can be None.
    """
    if path is None:
        return None
    return '/'.join(path.split('/')[:-1])


def _get_name(path):
    """Returns the name of the file or directory at path.

    :param str path: The file or directory to get the name of.

    :rtype: str
    :returns: The name of the file or directory.  Can be None.
    """
    if path is None:
        return None
    return path.split('/')[-1]


# TODO(benedikt) Check that this covers all the cases of the original function.
def _contains_sneaky_path(paths):
    """Check if the user tries to escape from the ``store_dir``.

    To avoid the user escaping out of the boundaries of `store_dir` we
    check, if a user given path contains any segment consisting of
    '..'.

    :param list paths: List of paths to check.

    :rtype: bool
    :returns: `True` if any path in paths contains '..' as a segment.
        `False` otherwise.

    """
    # BEGIN OLD CODE ==================================================
    # Matches any path where at least one segment is '..', '\..',
    # '.\.' or '\.\.'.
    # regex = re.compile(r'(^|/)\\?\.\\?\.($|/)')
    # END OLD CODE ==================================================
    # Matches any segment of path that equals '..'.
    if paths is None:
        return False
    regex = re.compile(r'(^|/)\.\.($|/)')
    for path in paths:
        if regex.search(path) is not None:
            return True
    return False


def _gen_password(length, symbols=True):
    """Generates a random string.

    Uses :cls:`random.SystemRandom` if available and
    :cls:`random.Random` otherwise.

    :param int length: The length of the random string.

    :param bool symbols: (optional) If `True` `string.punctuation`
        will also be used to generate the output. Default: `True`.

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

    return bytes(''.join(rand.choice(chars) for _ in range(length)), 'utf')


def _copy_move(src, dst, force=False, move=False):
    """Copies/moves a file or directory recursively.

    This function is partially based on the `cp` function from the
    pycoreutils package written by Hans van Leeuwen and licensed under
    the MIT license (https://pypi.python.org/pypi/pycoreutils/).

    :param str src: The file or directory to be copied.

    :param str dst: The file or directory to be copied to.

    :param bool force: If `True` existing files at the destination
        will be silently overwritten.

    :raises: :exc:`FileNotFoundError` if there exists no key or
        directory for `src`.

    :raises: :exc:`FileExistsError` if a key at `dst` already exists
        and `force` is set to `False`.

    """
    if move:
        operation = shutil.move
    else:
        operation = shutil.copy

    if not os.path.isdir(src):
        src += '.gpg'
        if not os.path.isfile(src):
            raise FileNotFoundError('{} not found.'.format(src))

        if dst.endswith('/') and not os.path.exists(dst):
            os.makedirs(dst, exist_ok=True)
        if os.path.isdir(dst):
            dst = os.path.join(dst, _get_name(src))
        else:
            dst += '.gpg'

        if os.path.exists(dst) and not force:
            raise FileExistsError('{} already exists.'.format(dst))
        operation(src, dst)
    else:
        if dst.startswith(src):
            raise IOError('Can\'t copy a directory into itself.')

        if not os.path.exists(dst):
            os.makedirs(dst, exist_ok=True)

        for root, dirs, files in os.walk(src):
            mid = root.replace(src, '', 1)

            for d in dirs:
                dstdir = os.path.join(dst, mid, d)
                if not os.path.exists(dstdir):
                    os.mkdir(dstdir)

            for f in files:
                srcfile = os.path.join(root, f)
                dstfile = os.path.join(dst, mid, f)
                if os.path.exists(dstfile) and not force:
                    # TODO(benedikt) Find better solution to just quitting.
                    raise FileExistsError('{} already exists.'.format(dstfile))
                operation(srcfile, dstfile)

    return dst
