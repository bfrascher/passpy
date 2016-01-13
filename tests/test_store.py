import pytest
from pypass import Store


@pytest.fixture(scope='module')
def store():
    return Store(debug=True)
