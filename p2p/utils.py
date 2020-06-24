import socket

from typing import Dict, Any

data_header = "DATA:"
hello_header = "HELLO:"
header_max_size = int(2 ** 10)

header_data_types = {
    "size": int
}


def build_header(header: Dict[str, Any], header_type: str = data_header):
    return header_type + "&".join([f"{key}={value}" for key, value in header.items()])


def split_header(header):
    if ":" in header:
        header = header.split(":")[1]

    values = {}
    for part in header.split("&"):
        key, value = part.split("=")

        # convert data type if necessary
        if key in header_data_types:
            value = header_data_types[key](value)

        values[key] = value

    return values


def get_local_ip():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        # works even with no internet connection
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]


def check_address(address: str, port: int):
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
