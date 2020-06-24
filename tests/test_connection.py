from typing import List, Dict, Any

from .utils import with_peers


@with_peers([{}, {}])
def test_send(peers: List[Dict[str, Any]]):
    """Tests data sending from one peer to another"""
    connection = peers[0].connect(peers[1].address_name)

    connection.send("2easy4u")


@with_peers([{}, {}])
def test_send(peers: List[Dict[str, Any]]):
    """Tests relatively large data sending from one peer to another"""
    connection = peers[0].connect(peers[1].address_name)

    connection.send(range(int(1e5)))  # closes before end
