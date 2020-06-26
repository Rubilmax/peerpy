import pytest

from ..utils import with_peers
from .conftest import data_test, data_large


@pytest.fixture
@with_peers
def peers():
    return [{}, {}]


def test_send(peers):
    """Tests data sending from one peer to another"""
    connection = peers[0].connect(peers[1].address_name, data_type="json")

    connection.send(data_test)


def test_send_large(peers):
    """Tests relatively large data sending from one peer to another"""
    connection = peers[0].connect(peers[1].address_name, data_type="raw")

    connection.send(data_large)
