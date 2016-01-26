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

from passpy.util import (
    trap,
    initialised,
    gen_password,
    copy_move,
)


@trap(0)
def trapped_args(path):
    """Dummy function for testing :func:`passpy.util.trap` (args
    version).

    """
    return True


@trap('path')
def trapped_kwargs(path=''):
    """Dummy function for testing :func:`passpy.util.trap` (kwargs
    version).

    """
    return True


@initialised
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
    store.init('dummy id')
    assert check_init(store)


@pytest.mark.parametrize('length,symbols',[
    (27, False),
    (54, True),
])
def test_gen_password(length, symbols):
    """Test for :func:`passpy.util.gen_password`.
    """
    password = gen_password(length, symbols)
    assert len(password) == length
    if not symbols:
        for char in string.punctuation:
            assert char not in password
    assert password.lstrip(string.ascii_letters + string.digits
                           + string.punctuation * symbols) == ''


class TestCopyMove:
    """Tests for :func:`passpy.util.copy_move`."""
    @staticmethod
    def setup_tmpdir(tmpdir):
        """Create come initial files to copy/move."""
        foo = tmpdir.join('foo')
        foo.write(foo.basename, ensure=True)

        bar = tmpdir.join('dir', 'bar')
        bar.write(bar.basename, ensure=True)

        return (foo, bar)

    def test_verbose(self, capsys, tmpdir):
        """Test verbose setting."""
        foo, bar = TestCopyMove.setup_tmpdir(tmpdir)
        bar2 = tmpdir.join('dir', 'dir2', 'bar2')
        bar2.ensure()

        # copy file
        copy_move(str(foo), str(tmpdir.join('foo2')), verbose=True)
        out, err = capsys.readouterr()
        assert err == ''
        assert out == '{0} -> {1}\n'.format(str(foo), str(tmpdir.join('foo2')))

        copy_move(str(foo), str(tmpdir.join('foo3')), verbose=False)
        out, err = capsys.readouterr()
        assert err == ''
        assert out == ''

        # copy directory
        copy_move(str(tmpdir.join('dir')),
                  str(tmpdir.join('folder') + os.sep),
                  verbose=True)
        out, err = capsys.readouterr()
        assert err == ''
        out_list = out.split('\n')
        assert len(out_list) == 4
        assert out_list[0] == '{0} -> {1}'.format(
            str(tmpdir.join('dir', 'dir2')),
            str(tmpdir.join('folder', 'dir2')))
        assert out_list[1] == '{0} -> {1}'.format(str(bar),
            str(tmpdir.join('folder', 'bar')))
        assert out_list[2] == '{0} -> {1}'.format(str(bar2),
            str(tmpdir.join('folder', 'dir2', 'bar2')))
        assert out_list[3] == ''

        copy_move(str(tmpdir.join('dir')),
                  str(tmpdir.join('folder2') + os.sep),
                  verbose=False)
        out, err = capsys.readouterr()
        assert err == ''
        assert out == ''

    def test_force(self, tmpdir):
        """Test force setting."""
        foo, bar = TestCopyMove.setup_tmpdir(tmpdir)
        dir2 = tmpdir.join('dir2')
        foo2 = dir2.join('foo')
        folder = tmpdir.join('folder')

        # copy file
        copy_move(str(foo), str(foo2), force=True)
        assert foo.read() == foo2.read()
        assert bar.read() != foo2.read()

        with pytest.raises(FileExistsError):
            copy_move(str(bar), str(foo2))

        copy_move(str(bar), str(foo2), force=True)
        assert bar.read() == foo2.read()

        # copy directory
        copy_move(str(tmpdir.join('dir')), str(folder) + os.sep,
                  force=True)
        assert folder.join('dir', 'bar').read() == bar.read()
        assert folder.join('dir', 'bar').read() != foo.read()

        # Overwrite bar with foo, so that we can overwrite
        # folder/dir/bar with foo and check.
        copy_move(str(foo), str(bar), force=True)

        with pytest.raises(FileExistsError):
            copy_move(str(tmpdir.join('dir')), str(folder) + os.sep)

        copy_move(str(tmpdir.join('dir')), str(folder) + os.sep,
                  force=True)
        assert folder.join('dir', 'bar').read() == foo.read()

    def test_interactive(self, tmpdir):
        """Test interactive setting."""
        foo, bar = TestCopyMove.setup_tmpdir(tmpdir)
        foo2 = tmpdir.join('foo2')
        folder = tmpdir.join('folder')

        # copy file
        copy_move(str(foo), str(foo2), interactive=True)
        with pytest.raises(IOError):
            copy_move(str(foo), str(foo2), interactive=True)

        # copy directory
        copy_move(str(tmpdir.join('dir')), str(folder) + os.sep,
                  interactive=True)
        with pytest.raises(IOError):
            copy_move(str(tmpdir.join('dir')), str(folder) + os.sep,
                      interactive=True)

    def test_move(self, tmpdir):
        """Test move setting."""
        foo, bar = TestCopyMove.setup_tmpdir(tmpdir)
        foo2 = tmpdir.join('foo2')
        dir2 = tmpdir.join('dir2')

        # copy file
        copy_move(str(foo), str(foo2), move=True)
        assert not os.path.exists(str(foo))
        assert os.path.exists(str(foo2))

        # copy directory
        copy_move(str(tmpdir.join('dir')), str(dir2), move=True)
        assert not os.path.exists(str(tmpdir.join('dir')))
        assert os.path.isdir(str(dir2))
        assert os.path.isfile(str(dir2.join('bar')))

    def test_recursive_error(self, tmpdir):
        """Test raising of :class:`passpy.exceptions.RecursiveCopyMoveError`.

        """
        import passpy

        with pytest.raises(passpy.RecursiveCopyMoveError):
            copy_move(str(tmpdir), str(tmpdir.join('dir')))
