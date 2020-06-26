import sys
import os
# allow the example to be run without installing the package, from this repository's root directory
sys.path.append(os.path.abspath(os.path.join('.')))

from peerpy import Peer


# by default, Peer will find the device's local IP
# so that it is reachable, on its default interface, by other peers on the same local network
with Peer(port=12345, timeout=1, handlers={
    "listen": lambda peer: print("Peer 1:", peer.address_name)  # printing this peer's address when ready to connect
}) as peer1:
    # handler to be executed at connection time (returned value indicates whether to accept or deny the connection)
    def set_connection_handler(connection) -> bool:
        connection.handlers["data"] = lambda data: print("Peer 2:", data)
        return connection.target_name == peer1.address_name  # only accept peer1's connections

    with Peer(port=11111, timeout=1, handlers={
        # printing this peer's address when ready to connect
        "listen": lambda peer: print("Peer 2:", peer.address_name),
        # configure connection before accepting it
        "connection": set_connection_handler
    }) as peer2:
        connection = peer1.connect(peer2.address)

        if connection:  # if connection was successful
            connection.send("Hello world!")  # peer1 send "Hello world!" to peer2
            # peer2 prints any data that it receives; so will print "Hello world!"
