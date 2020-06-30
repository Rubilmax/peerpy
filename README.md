# peerpy 1.0.0
## Discover and connect every device running python on a local network via TCP!

This module provides a high-level API for discovering and connecting multiple devices on a local network, without the headache of implementing python's built-in socket module!

## Installation

`pip install peerpy`

## Quick tour

Connecting two devices running python is as easy, reliable and painless as 8 lines of code!

Start by importing the `Peer` class, which automatically detects your device's local IP and run a socket server, listening on a given port:

```python
from peerpy import Peer
```

Start a peer object on the listening device:

```python
with Peer(port=54865) as peer:
    # let the program run until CTRL+C
    while True:
        time.sleep(1.)
```

Connect your second device to your listening device:

```python
with Peer(port=12152) as peer:
    connection = peer.connect("192.168.0.2:54865")

    if connection:
        connection.send(f"Hello world from {peer.address_name}!")
```

You can even add handlers which are executed on a separate thread on specific events, such as:

```python
def set_connection_handler(connection):
    connection.set_handler("data", lambda data: print(data))

with Peer(handlers={
    # called when socket server is listening
    "listen": lambda peer: print(peer.address_name),
    # called when socket has established a connection
    "connection": set_connection_handler,
    # called when socket server has stopped
    "stop": lambda peer: print("Peer stopped!")
}) as peer:
```

For more details on handlers and connections, please consider reading [the documentation](https://peerpy.readthedocs.io).

## Examples

To begin with this module, please consider reading [the examples](https://github.com/Rubilmax/peerpy/blob/master/examples/) given on this repository.

## Documentation

For further documentation, please [Read The Docs](https://peerpy.readthedocs.io)!