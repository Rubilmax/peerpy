import time
import pytest

from ..utils import with_peers

datas = []


@pytest.fixture
@with_peers
def peers():
    def set_connection_handler(connection):
        connection.handlers["data"] = lambda data: datas.append(data)
        return True

    peer_adder_args = {
        "handlers": {
            "connection": set_connection_handler
        }
    }

    return [{}, peer_adder_args, peer_adder_args]


def test_receive_multiple(peers):
    """Tests data sending from one peer to another"""
    connection_0 = peers[0].connect(peers[1].address_name, data_type="json")
    connection_2 = peers[2].connect(peers[1].address_name, data_type="json")

    datas_test = [f"data{i}" for i in range(15)]
    for data in datas_test:
        connection_0.send(data)
        connection_2.send(data)

    time.sleep(.1)

    assert len(datas) == (len(peers) - 1) * len(datas_test)
