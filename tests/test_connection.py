import time

from typing import List, Dict, Any

from .utils import with_peers

data_test = "2easy4u"
data_large = list(range(int(2e6)))


@with_peers([{}, {}])
def test_send(peers: List[Dict[str, Any]]):
    """Tests data sending from one peer to another"""
    connection = peers[0].connect(peers[1].address_name, data_type="json")

    connection.send("2easy4u")


@with_peers([{}, {}])
def test_send_large(peers: List[Dict[str, Any]]):
    """Tests relatively large data sending from one peer to another"""
    connection = peers[0].connect(peers[1].address_name, data_type="raw")

    connection.send(data_large)


def set_connection_handler(connection):
    def check_data(data):
        assert data == data_test

    connection.handlers["data"] = check_data
    return True


@with_peers([{}, {"handlers": {"connection": set_connection_handler}}])
def test_data_handler(peers: List[Dict[str, Any]]):
    """Tests a peer's connection & data handlers"""
    connection = peers[0].connect(peers[1].address_name)
    connection.send(data_test)
