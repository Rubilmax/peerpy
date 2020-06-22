import json
import pickle
import socket
import threading

header_name = "HEADER:"


def split_header(header):
    values = {}

    parts = header.split("&")
    for part in parts:
        key, value = part.split("=")
        values[key] = value

    values["size"] = int(values["size"])

    return values


class Connection():

    def __init__(self, main_peer, target_peer, sock: socket.socket, buffer_size: int = 2 ** 13):
        self.main_peer = main_peer
        self.target_peer = target_peer
        self.sock = sock

        self.buffer_size = int(buffer_size)

        self.terminate_flag = threading.Event()
        self.thread = threading.Thread(target=self.main_loop)
        self.thread.start()

    def send(self, data):
        data = pickle.dumps(data)

        size = len(data)
        header = f"{header_name}size={size}".encode("utf-8")
        self.sock.sendall(header)

        self.sock.sendall(data)

    def _receive(self, header: str):
        header = split_header(header)

        buffer = b""
        nb_chunks = header["size"] // self.buffer_size
        if header["size"] % self.buffer_size > 0:
            nb_chunks += 1

        for _ in range(nb_chunks):
            buffer += self.sock.recv(self.buffer_size)

        return pickle.loads(buffer)

    def close(self):
        self.terminate_flag.set()

    def main_loop(self):
        self.sock.settimeout(5)

        while not self.terminate_flag.is_set():
            try:
                # will block until header is received or socket timeout
                header = self.sock.recv(2 ** 10).decode("utf-8")
            except socket.timeout:
                continue

            if header.startswith(header_name):
                self.main_peer.logger.debug(f"Header received: {header}")

                data = self._receive(header.strip(header_name))

                self.main_peer.logger.debug(f"Data received: {data}")

        self.main_peer.logger.debug("Connection stopped!")
