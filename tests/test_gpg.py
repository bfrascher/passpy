import pytest

from passpy.gpg import (
    _get_gpg_recipients,
)


@pytest.fixture(scope='session')
def storedir(tmpdir_factory):
    store = tmpdir_factory.mktemp('store')
    gpg_id1 = store.join('.gpg-id')
    gpg_id2 = store.join('noid', 'newid', '.gpg-id')
    gpg_id12 = store.join('newid', '.gpg-id')

    gpg_id1.write('passpy_id1\n', ensure=True)
    gpg_id2.write('passpy_id2\n', ensure=True)
    gpg_id12.write('passpy_id1\npasspy_id2\n', ensure=True)

    return store


def test_get_gpg_recipients(storedir):
    recipients = _get_gpg_recipients(str(storedir))
    assert len(recipients) == 1
    assert recipients[0] == 'passpy_id1'

    recipients = _get_gpg_recipients(str(storedir.join('noid', 'somefile')))
    assert len(recipients) == 1
    assert recipients[0] == 'passpy_id1'

    recipients = _get_gpg_recipients(str(storedir.join('noid', 'newid')))
    assert len(recipients) == 1
    assert recipients[0] == 'passpy_id2'

    recipients = _get_gpg_recipients(str(storedir.join('newid')))
    assert len(recipients) == 2
    assert recipients[0] == 'passpy_id1'
    assert recipients[1] == 'passpy_id2'
