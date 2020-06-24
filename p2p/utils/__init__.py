import socket

from typing import Dict, Any, Union, Tuple

default_buffer_size = 8192

header_separator = "|"
data_header = "DATA"
hello_header = "HELLO"
header_max_size = int(2 ** 10)

header_data_types = {
    "data_size": int,
    "buffer_size": int
}


def build_header(header: Dict[str, Any], header_type: str) -> str:
    """Returns a normalized header of type header_type.

    Args:
        header (Dict[str, Any]): the data to put in the header.
        header_type (str, optional): the type of the header to generate. Defaults to data_header.

    Returns:
        str: the generated header
    """
    return header_type + header_separator + "&".join([f"{key}={value}" for key, value in header.items()])


def build_hello_header(peer_name: str, data_type: str) -> str:
    """Builds a header used to handshake with another peer and set up a data connection.

    Args:
        peer_name (str): the name of the peer initiating the handshake.
        data_type (str): the data type to be sent.

    Returns:
        str: the generated header
    """
    return build_header({
        # so that the other peer knows who we are
        "peer_name": peer_name,
        # so that the other peer knows what data type to handle
        "data_type": data_type
    }, header_type=hello_header)


def build_data_header(data_size: int, data_type: str) -> str:
    """Builds a header used to indentify data that will be send.

    Args:
        data_size (int): the size of the data, in bytes.
        data_type (str): the data type to be sent.

    Returns:
        str: the generated header
    """
    return build_header({
        # so that the other peer knows how much data to handle
        "data_size": data_size,
        # so that the other peer know which type of data to handle
        "data_type": data_type
    }, header_type=data_header)


def split_header(header: str) -> Dict[str, Union[str, int]]:
    """Splits the given header into a dictionnary mapping keys to values.

    Args:
        header (str): the header received

    Returns:
        Dict[str, Union[str, int]]: the header mapping entries found in the original header
    """
    # TODO: what if header contains malicious data?? can crash the thread...
    if header_separator in header:
        header = header.split(header_separator)[1]

    values = {}
    for part in header.split("&"):
        key, value = part.split("=")

        # convert data type if necessary
        if key in header_data_types:
            value = header_data_types[key](value)

        values[key] = value

    return values


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
