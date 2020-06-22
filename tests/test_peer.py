import logging

from p2py.__main__ import Peer

logging.basicConfig(level=logging.DEBUG)


def test_close():
    peer = Peer(("localhost", 15553))
    peer.close()
