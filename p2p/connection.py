import json
import pickle
import socket
import threading
from typing import Any

from .utils import data_header, header_max_size, build_header, split_header


class Connection():

    def __init__(self, main_peer, sock: socket.socket, buffer_size: int = 2 ** 13, data_type: str = "raw", strict: bool = True):
        if self.data_type not in ["raw", "json", "bytes"]:
            raise ValueError("data_type must be one of ['raw', 'json', 'bytes']")

        self.main_peer = main_peer
        self.sock = sock
        self.buffer_size = int(buffer_size)
        self._data_type = data_type
        self.strict = strict

        self.stop_listener_flag = threading.Event()
        self.thread = threading.Thread(target=self._listen)
        self.thread.deamon = True
        self.thread.start()

    @property
    def data_type(self):
        self._data_type

    @data_type.setter
    def data_type(self, data_type):
        self._data_type = data_type

        if self.strict:
            # TODO: send data_type update
            pass

    def send(self, data: Any):
        """Send data to the target peer, serializing it to this connection's default data format.

        Args:
            data (Any): the data to serialize and send

        Raises:
            ValueError: if this connection's default format is bytes and the data is not bytes
        """
        # first encode data according to this connection's default data type
        if self.data_type == "raw":
            data = pickle.dumps(data)
        elif self.data_type == "json":
            data = json.dumps(data)
        else:
            if not isinstance(data, bytes):
                raise ValueError("data is not a bytes object")

        # then send information about data
        header = build_header({
            # so that the other peer knows how much data to handle
            "size": len(data),
            # so that the other peer know which type of data to handle
            "data_type": self.data_type
        }, header_type=data_header)

        self.sock.sendall(header.encode("utf-8"))

        self.sock.sendall(data)

    def _receive(self, header: str):
        """Internal method to start the receiving process

        Args:
            header (str): the header first received from the other peer

        Returns:
            Any: the data received and deserialized (according to the data type referenced in the header)
        """
        header = split_header(header)

        if self.strict and header["data_type"] != self.data_type:
            return None

        # receiving data
        buffer = b""
        nb_chunks = header["size"] // self.buffer_size
        if header["size"] % self.buffer_size > 0:
            nb_chunks += 1

        for _ in range(nb_chunks):
            buffer += self.sock.recv(self.buffer_size)

        # deserializing data
        data = None
        if header["data_type"] == "raw":
            data = pickle.loads(buffer)
        elif header["data_type"] == "json":
            data = json.loads(buffer)

        return data

    def close(self):
        self.stop_listener_flag.set()

    def _listen(self):
        while not self.stop_listener_flag.is_set():
            # in case timeout has changed
            if self.main_peer.timeout != self.sock.gettimeout():
                self.sock.settimeout(self.main_peer.timeout)

            try:
                # will block until any header is received or socket timeout
                header = self.sock.recv(header_max_size).decode("utf-8")
            except socket.timeout:
                # no header received within timeout seconds
                continue

            # if we received a data header, otherwise do nothing with the received packet
            if header.startswith(data_header):
                self.main_peer.logger.debug(f"Header received: {header}")

                data = self._receive(header)

                self.main_peer.logger.debug(f"Data received: {data}")

        self.sock.close()
        self.main_peer.logger.debug("Connection stopped!")
