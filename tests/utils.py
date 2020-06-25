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

            time.sleep(.5)  # wait for servers to be listening

            test_func(peers)

            time.sleep(.5)  # wait for transactions to be completed

            # As pytest won't detect errors in separate threads
            # we check threads states and raise RuntimeError if a thread is stopped wheres it shouldn't be
            for peer in peers:
                if not peer.server_thread.is_alive():
                    raise RuntimeError(f"({peer.address_name}) Peer's server crashed!")
                for connection in peer.connections:
                    if not peer.connections[connection].thread.is_alive():
                        raise RuntimeError(
                            f"({peer.address_name}) Peer's connection to {connection.target_name} crashed!")
                if not peer.invisible and not peer.pinger_thread.is_alive():
                    raise RuntimeError(f"({peer.address_name}) Peer's pinger crashed!")

            for peer in peers:
                peer.stop(_async=True)
        return wrapper
    return decorator
