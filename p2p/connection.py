import json
import pickle
import socket
import threading

from .utils import data_header, header_max_size, build_header, split_header


class Connection():

    def __init__(self, main_peer, sock: socket.socket, buffer_size: int = 2 ** 13, data_type: str = "raw"):
        self.main_peer = main_peer
        self.sock = sock
        self.buffer_size = int(buffer_size)
        self.data_type = data_type

        self.terminate_flag = threading.Event()
        self.thread = threading.Thread(target=self._listen)
        self.thread.deamon = True
        self.thread.start()

    def send(self, data):
        header = build_header({
            "size": len(data),
            "data_type": self.data_type
        }, header_type=data_header)

        self.sock.sendall(header.encode("utf-8"))

        if self.data_type == "raw":
            data = pickle.dumps(data)
        elif self.data_type == "json":
            data = json.dumps(data)
        elif self.data_type == "bytes":
            if not isinstance(data, bytes):
                raise ValueError("data is not a bytes object")
        else:
            raise ValueError("data_type must be one of ['raw', 'json', 'bytes']")

        self.sock.sendall(data)

    def _receive(self, header: str):
        header = split_header(header)

        buffer = b""
        nb_chunks = header["size"] // self.buffer_size
        if header["size"] % self.buffer_size > 0:
            nb_chunks += 1

        for _ in range(nb_chunks):
            buffer += self.sock.recv(self.buffer_size)

        data = None
        if header["data_type"] == "raw":
            data = pickle.loads(buffer)
        elif header["data_type"] == "json":
            data = json.loads(buffer)

        return data

    def close(self):
        self.terminate_flag.set()

    def _listen(self):
        self.sock.settimeout(self.main_peer.timeout)

        while not self.terminate_flag.is_set():
            try:
                # will block until any header is received or socket timeout
                header = self.sock.recv(header_max_size).decode("utf-8")
            except socket.timeout:
                # no header received within timeout seconds
                continue

            if header.startswith(data_header):
                self.main_peer.logger.debug(f"Header received: {header}")

                data = self._receive(header)

                self.main_peer.logger.debug(f"Data received: {data}")

        self.main_peer.logger.debug("Connection stopped!")
