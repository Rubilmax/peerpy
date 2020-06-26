from typing import Dict, Callable, Any, Union
from dataclasses import dataclass

from .exceptions import HeaderSizeError


header_size: int = int(2 ** 6)
header_separator: str = "|"
header_values_separator: str = "&"
header_key_separator: str = "="

data_header: str = "DATA"
hello_header: str = "HELLO"
accept_header: str = "ACCEPT"
deny_header: str = "DENY"

header_data_types: Dict[str, Callable] = {
    "data_size": int,
    "buffer_size": int,
    "strict": bool
}

pinger_port: int = 1024


def build_header(header: Dict[str, Any], header_type: str) -> bytes:
    """Returns a normalized header of type header_type.

    Args:
        header (Dict[str, Any]): the data to put in the header.
        header_type (str, optional): the type of the header to generate. Defaults to data_header.

    Returns:
        bytes: the generated encoded header
    """
    header_elements = [key + header_key_separator + str(value) for key, value in header.items()]
    header_body = header_values_separator.join(header_elements)
    if len(header_body) > 0:
        header_body = header_separator + header_body

    header_bytes = (header_type + header_body).encode("utf-8")
    tail_size = header_size - len(header_bytes)
    if tail_size < 0:
        raise HeaderSizeError(
            f"Header size ({len(header_bytes)}) is greater than the protocol's setting ({header_size})!")

    return header_bytes + header_separator.encode("utf-8") * tail_size


def build_hello_header(peer_name: str, data_type: str, strict: bool) -> bytes:
    """Builds a header used to handshake with another peer and set up a data connection.

    Args:
        peer_name (str): the name of the peer initiating the handshake.
        data_type (str): the data type to be sent.

    Returns:
        bytes: the generated encoded header
    """
    return build_header({
        # so that the other peer knows who we are
        "peer_name": peer_name,
        # so that the other peer knows what data type to handle
        "data_type": data_type,
        # so that the other peer knows if the connection is strict or not
        "strict": strict
    }, header_type=hello_header)


def build_data_header(data_size: int, data_type: str) -> bytes:
    """Builds a header used to indentify data that will be send.

    Args:
        data_size (int): the size of the data, in bytes.
        data_type (str): the data type to be sent.

    Returns:
        bytes: the generated encoded header
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
    if header_values_separator in header:
        for part in header.split(header_values_separator):
            key, value = part.split(header_key_separator)

            # convert data type if necessary
            if key in header_data_types:
                value = header_data_types[key](value)

            values[key] = value

    return values
