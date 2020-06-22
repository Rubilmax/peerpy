import sys
import time
import pytest
import logging

from p2p import Peer


def test_stop():
    peer = Peer(("localhost", 15551), timeout=1)

    time.sleep(.5)

    peer.stop(_async=True)


def test_connect():
    peer1 = Peer(("localhost", 15551), timeout=1)
    peer2 = Peer(("localhost", 15552), timeout=1)

    time.sleep(.5)

    peer1.connect(peer2.address)

    time.sleep(.5)

    peer1.stop(_async=True)
    peer2.stop(_async=True)
