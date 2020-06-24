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
