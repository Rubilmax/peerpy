import sys
import os
# allow the example to be run without installing the package, from this repository's root directory
sys.path.append(os.path.abspath(os.path.join('.')))

"""
Hello World Example

This example is made to be run from 2 separate python shells:
python examples/hello_world.py
"""
from peerpy import Peer


def set_connection_handler(connection) -> bool:
    # handler to be executed at connection time (returned value indicates whether to accept or deny the connection)
    connection.set_handler("data", lambda data: print(f"Received: {data}"))


# by default, Peer will find the device's local IP and allocate its own port (in the range of allowed ports)
# so that it is reachable, on its default interface, by other peers on the same local network
with Peer(timeout=1, handlers={"connection": set_connection_handler}) as peer:
    address_name = input("Address to connect to (CTRL+C to stop):\n")
    connection = peer.connect(address_name)

    if connection:  # if connection was successful
        connection.send(f"Hello world from {peer.address_name}!")  # peer sends "Hello world!" to remote peer
        # remote peer prints any data that it receives; so will print "Hello world!"
        print("Hello world sent!")
    else:
        print("Connection couldn't be established!")
