import socket

header_name = "HEADER:"


def split_header(header):
    values = {}

    parts = header.split("&")
    for part in parts:
        key, value = part.split("=")
        values[key] = value

    values["size"] = int(values["size"])

    return values


def get_local_ip():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        # works even with no internet connection
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
