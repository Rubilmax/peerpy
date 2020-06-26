import sys
import os
sys.path.append(os.path.abspath(os.path.join('.')))  # ignore this

from peerpy import Peer


# handler to be executed at connection time (return value indicates whether to accept or deny the connection)
def set_connection_handler(connection) -> bool:
    connection.handlers["data"] = lambda data: print("Peer 2:", data)
    return True


# by default, Peer will find the device's local IP
# so that it is reachable, on its default interface, by other peers on the same local network
with Peer(port=12345, timeout=1, handlers={
    "listen": lambda peer: print("Peer 1:", peer.address_name)
}) as peer1:
    with Peer(port=11111, timeout=1, handlers={
        "listen": lambda peer: print("Peer 2:", peer.address_name),
        "connection": set_connection_handler
    }) as peer2:
        connection = peer1.connect(peer2.address)

        if connection:  # if connection was successful
            connection.send("Hello world!")  # peer1 send "Hello world!" to peer2
            # peer2 prints any data that it receives; so will print "Hello world!"
