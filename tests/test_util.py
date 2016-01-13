import pytest

import pypass.util as util


@util.trap(0)
def trapped(path):
    return True


# Implicitly also tests _contains_sneaky_path, so no need to write a
# separate test.
@pytest.mark.parametrize('path,raises', [
    ('..', True),
    ('~/..', True),
    ('../abc', True),
    ('abc../', False),
    ('/some/dir/../another', True),
    ('a..dir', False)
])
def test_trap(path, raises):
    if raises:
        with pytest.raises(PermissionError):
            trapped(path)
    else:
        assert trapped(path)


@pytest.mark.parametrize('path,pdir', [
    (None, None),
    ('parent/dir/file', 'parent/dir'),
    ('/dir/another/', '/dir/another'),
    ('/dir/file', '/dir'),
])
def test_get_parent_dir(path, pdir):
    assert util._get_parent_dir(path) == pdir


@pytest.mark.parametrize('path,name', [
    (None, None),
    ('parent/dir/file', 'file'),
    ('parent/dir/another/', ''),
])
def test_get_name(path, name):
    assert util._get_name(path) == name


@pytest.mark.parametrize('length,symbols', [
    (27, False),
    (31, True),
    (0, False),
    (18, True),
    (500, True),
    (7, False),
])
def test_gen_password(length, symbols):
    import string

    password = util._gen_password(length, symbols)
    assert len(password) == length
    if not symbols:
        for s in string.punctuation:
            assert s not in password
        assert password.strip(string.ascii_letters + string.digits) == ''
    else:
        assert password.strip(string.ascii_letters +
                              string.digits + string.punctuation) == ''


def test_copy_move():
    pass
