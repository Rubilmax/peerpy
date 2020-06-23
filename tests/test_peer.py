import time
from typing import List, Dict, Any

from p2p import Peer


def with_peers(peers_args: List[Dict[str, Any]]):
    """Decorator used to instanciate, start and asynchronously stop peers during tests.

    Args:
        peers_args (List[Dict[str, Any]]): the list of peer kwargs to instanciate peers with.
    """
    def decorator(test_func):
        def wrapper():
            peers = [Peer(**peer_args, timeout=1) for peer_args in peers_args]
            time.sleep(.5)

            test_func(peers)

            for peer in peers:
                peer.stop(_async=True)
        return wrapper
    return decorator


@with_peers([{}])
def test_stop(peers: List[Dict[str, Any]]):
    """Tests the instanciation and asynchronous stop a peer object"""
    assert peers[0].server_thread.is_alive()


@with_peers([{}, {}])
def test_connect(peers: List[Dict[str, Any]]):
    """Tests the connection of a peer to another"""
    peers[0].connect(peers[1].address)

    assert peers[1].address_name in peers[0].connections


@with_peers([{}, {}, {}])
def test_ping(peers: List[Dict[str, Any]]):
    """Tests the discovery protocol on a network of 3 peers"""
    assert sorted(peers[0].get_local_peers()) == sorted([peer.address_name for peer in peers[1:]])


@with_peers([{} for _ in range(10)])
def test_ping_large_network(peers: List[Dict[str, Any]]):
    """Tests the discovery protocol on a relatively large network"""
    assert sorted(peers[0].get_local_peers()) == sorted([peer.address_name for peer in peers[1:]])


@with_peers([{}, {}, {"invisible": True}])
def test_invisibility(peers: List[Dict[str, Any]]):
    """Tests the invisibility argument at peer instanciation"""
    assert peers[0].get_local_peers() == [peers[1].address_name]
    assert peers[2].invisible


@with_peers([{}, {}, {}])
def test_invisibility_property(peers: List[Dict[str, Any]]):
    """Tests the invisibility property when a peer is already running"""
    peers[2].invisible = True
    peers[2].invisible = False
    assert sorted(peers[0].get_local_peers()) == sorted([peers[1].address_name, peers[2].address_name])

    peers[2].invisible = True
    assert peers[0].get_local_peers() == [peers[1].address_name]

    time.sleep(1)

    assert not peers[2].pinger_thread.is_alive()
