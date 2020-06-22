import sys
import time
import pytest
import logging

from p2p import Peer


def test_stop():
    peer = Peer(timeout=1)

    time.sleep(.5)

    peer.stop(_async=True)


def test_connect():
    peer1 = Peer(port=15551, timeout=1)
    peer2 = Peer(port=15552, timeout=1)

    time.sleep(.5)

    peer1.connect(peer2.address)

    time.sleep(.5)

    peer1.stop(_async=True)
    peer2.stop(_async=True)


def test_ping():
    peer1 = Peer(port=15551, timeout=1)
    peer2 = Peer(port=15552, timeout=1)
    peer3 = Peer(port=15553, timeout=1)

    time.sleep(.5)

    assert sorted(peer1.get_local_peers()) == sorted([peer2.address_name, peer3.address_name])

    time.sleep(.5)

    peer1.stop()
    peer2.stop()
    peer3.stop()
