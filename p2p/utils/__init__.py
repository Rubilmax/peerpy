import socket

from typing import Dict, Any, Union, Tuple

default_buffer_size = 8192
default_handlers = {
    "connection": lambda connection: True
}


def get_local_ip() -> str:
    """Returns the local IP address of this device.

    Returns:
        str: the ipv4 used by this device.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        # works even with no internet connection
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]


def check_address(address: str, port: int) -> Tuple[Tuple[str, int], str]:
    """Checks the given address and port allow multiple input types.

    Args:
        address (str): the ipv4 address, followed by the port if wanted
        port (int): the port to use (can be None if port is provided in address)

    Raises:
        ValueError: if port is None and no port can be found in address
        ValueError: if address is not ipv4:port nor (ipv4, port)

    Returns:
        Tuple[Tuple[str, int], str]: the normalized address and port in a tuple, the address and port in a string
    """
    if isinstance(address, str):
        if ":" in address:
            ipv4, port = address.split(":")[:2]
            address = (ipv4, int(port))
        elif port is None:
            raise ValueError("A port must be specified!")
        else:
            address = (address, int(port))
    elif not hasattr(address, "__getitem__"):
        raise ValueError("address should be a string ipv4:port or a tuple (ipv4, port)!")
    else:
        address = (str(address[0]), int(address[1]))

    address_name = f"{address[0]}:{address[1]}"
    return address, address_name
