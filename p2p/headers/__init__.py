from typing import Dict, Any, Union, Tuple

header_separator = "|"
header_values_separator = "&"
header_key_separator = "="

data_header = "DATA"
hello_header = "HELLO"
accept_header = "ACCEPT"
deny_header = "DENY"

header_max_size = int(2 ** 10)

header_data_types = {
    "data_size": int,
    "buffer_size": int,
    "strict": bool
}


def build_header(header: Dict[str, Any], header_type: str) -> str:
    """Returns a normalized header of type header_type.

    Args:
        header (Dict[str, Any]): the data to put in the header.
        header_type (str, optional): the type of the header to generate. Defaults to data_header.

    Returns:
        str: the generated header
    """
    header_elements = [key + header_key_separator + str(value) for key, value in header.items()]
    header_body = header_values_separator.join(header_elements)
    if len(header_body) > 0:
        header_body = header_separator + header_body

    return header_type + header_body


def build_hello_header(peer_name: str, data_type: str, strict: bool) -> str:
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
        "data_type": data_type,
        # so that the other peer knows if the connection is strict or not
        "strict": strict
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
    if header_values_separator in header:
        for part in header.split(header_values_separator):
            key, value = part.split(header_key_separator)

            # convert data type if necessary
            if key in header_data_types:
                value = header_data_types[key](value)

            values[key] = value

    return values
