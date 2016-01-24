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
import pytest
import string

import passpy.util as util


@util.trap(0)
def trapped_args(path):
    """Dummy function for testing :func:`passpy.util.trap` (args
    version).

    """
    return True


@util.trap('path')
def trapped_kwargs(path=''):
    """Dummy function for testing :func:`passpy.util.trap` (kwargs
    version).

    """
    return True


@util.initialised
def check_init(store):
    """Dummy function for testing :func:`passpy.util.initialised`."""
    return True


@pytest.mark.parametrize('path,trapped', [
    (None, True),
    ('..', False),
    ('../', False),
    ('../dir', False),
    ('root/..', True),
    ('root/../dir', True),
])
def test_trap(path, trapped):
    """Test for :func:`passpy.util.trap`.
    """
    if trapped:
        assert trapped_args(path)
        assert trapped_kwargs(path=path)
    else:
        with pytest.raises(PermissionError):
            trapped_args(path)
        with pytest.raises(PermissionError):
            trapped_kwargs(path=path)


def test_initialised(tmpdir):
    """Test for :func:`passpy.util.initialised`.
    """
    import passpy
    store = passpy.Store(store_dir=str(tmpdir.join('.password-store')))
    with pytest.raises(passpy.StoreNotInitialisedError):
        check_init(store)
    # As there are not other files in the tmpdir gpg will never be
    # called.  So there is no need for a real GPG ID.
    store.init_store('dummy id')
    assert check_init(store)


def test_gen_password():
    """Test for :func:`passpy.util.gen_password`.
    """
    password = util.gen_password(27, False)
    assert len(password) == 27
    assert string.punctuation not in password
    assert password.lstrip(string.ascii_letters + string.digits) == ''

    password = util.gen_password(54, True)
    assert len(password) == 54
    assert password.lstrip(string.ascii_letters + string.digits
                           + string.punctuation) == ''



def test_copy_move(capsys, tmpdir):
    """Test for :func:`passpy.util.copy_move`.
    """
    import passpy

    # ==================================================
    # file creation
    # ==================================================
    foo = tmpdir.join('foo')
    foo.write(foo.basename, ensure=True)

    bar = tmpdir.join('bar')
    bar.write(bar.basename, ensure=True)

    # ==================================================
    # tests
    # ==================================================
    with pytest.raises(FileNotFoundError):
        util.copy_move(str(tmpdir.join('no-such-file')),
                       str(tmpdir.join('dst')))

    # ==== copy/move files ====
    assert util.copy_move(str(foo), str(tmpdir.join('foo2')))\
        == str(tmpdir.join('foo2'))
    assert util.copy_move(str(bar), os.path.join(str(tmpdir), 'dir/'))\
        == str(tmpdir.join('dir/bar'))
    assert util.copy_move(str(tmpdir.join('foo2')),
                          str(tmpdir.join('dir/foo2')),
                          verbose=True, move=True)\
        == str(tmpdir.join('dir/foo2'))

    out, err = capsys.readouterr()
    assert out == '{0} -> {1}\n'.format(str(tmpdir.join('foo2')),
                                        str(tmpdir.join('dir/foo2')))

    with pytest.raises(IOError):
        util.copy_move(str(bar), str(tmpdir.join('dir/bar')), interactive=True)

    out, err = capsys.readouterr()
    assert out == 'Really overwrite {0}? [y/N] '.format(
        str(tmpdir.join('dir/bar')))

    with pytest.raises(FileExistsError):
        util.copy_move(str(bar), str(tmpdir.join('dir/bar')))

    assert util.copy_move(str(bar), str(tmpdir.join('dir/bar')), force=True)\
        == str(tmpdir.join('dir/bar'))

    with pytest.raises(passpy.RecursiveCopyMoveError):
        util.copy_move(str(tmpdir.join('dir')), str(tmpdir.join('dir/newdir')))


    # ===== copy/move directories =====
    assert util.copy_move(str(tmpdir.join('dir')), str(tmpdir.join('newdir')))\
        == str(tmpdir.join('newdir'))

    dirls = os.listdir(str(tmpdir.join('dir')))
    newdirls = os.listdir(str(tmpdir.join('newdir')))
    assert len(dirls) == len(newdirls)
    for entry in dirls:
        assert entry in newdirls

    assert util.copy_move(str(tmpdir.join('dir')), str(tmpdir.join('newdir')))\
        == str(tmpdir.join('newdir/dir'))

    assert util.copy_move(str(tmpdir.join('newdir')),
                          str(tmpdir.join('folder')), verbose=True, move=True)\
        == str(tmpdir.join('folder'))

    out, err = capsys.readouterr()
    out_list = out.split('\n')
    assert len(out_list) == 6
    assert out_list[0] == 'created directory {0}'.format(
        str(tmpdir.join('folder/dir')))
    assert out_list[5] == ''

    with pytest.raises(IOError):
        util.copy_move(str(tmpdir.join('dir')), str(tmpdir.join('folder')),
                       interactive=True)

    with pytest.raises(FileExistsError):
        util.copy_move(str(tmpdir.join('dir')), str(tmpdir.join('folder')))

    assert util.copy_move(str(tmpdir.join('dir')), str(tmpdir.join('folder')),
                          force=True) == str(tmpdir.join('folder/dir'))
