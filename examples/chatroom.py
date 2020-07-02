import sys
import os
# allow the example to be run without installing the package, from this repository's root directory
sys.path.append(os.path.abspath(os.path.join('.')))

"""
Chatroom Example

This example is made to be run from 2 separate python shells:
python examples/hello_world.py
"""
from peerpy import Peer, protocol


def print_message(connection, message):
    print(f"{connection.target_name}: {message}")


# by default, whenever a message is received from a connection, print it
protocol.defaults.connection_handlers["data"] = print_message


# by default, Peer will find the device's local IP and allocate its own port (in the range of allowed ports)
# so that it is reachable, on its default interface, by other peers on the same local network
with Peer(timeout=1) as peer:
    address_name = input("Address to connect to (CTRL+C to stop):\n")
    connection = peer.connect(address_name, data_type="json")

    if connection:  # if connection was successful
        while True:
            message = input("")
            print(f"{peer.address_name}: {message}")
            if not connection.send(message):
                print("Chat message couldn't be delivered!")
    else:
        print("Connection couldn't be established!")
