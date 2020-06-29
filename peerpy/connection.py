import json
import pickle
import socket
import threading
from typing import Any

from .event_handler import EventHandler
from .utils import valid_data_types, build_data_header, split_header
from .protocol import headers, defaults


class Connection(EventHandler):

    def __init__(self, main_peer, target_name: str, sock: socket.socket, buffer_size: int, **kwargs):
        data_type = str(kwargs.get("data_type", "json"))
        if data_type not in valid_data_types:
            raise ValueError(f"data_type must be one of {valid_data_types}")

        stream = bool(kwargs.get("stream", False))
        data_size = int(kwargs["data_size"]) if "data_size" in kwargs else "auto"
        if stream and data_size != "auto" and data_size <= 0:
            raise ValueError(f"Data size should be > 0 or 'auto' (Received {data_size})!")

        handlers = dict(kwargs.get("handlers", defaults.connection_handlers))
        super().__init__(handlers)

        self.main_peer = main_peer
        self.target_name = str(target_name)
        self.sock = sock
        self.buffer_size = int(buffer_size)
        self._data_type = data_type
        self.strict = bool(kwargs.get("strict", True))
        self.stream = stream
        self.data_size = data_size
        self.active = True

        self.thread = threading.Thread(target=self._listen)

    @property
    def data_type(self):
        return self._data_type

    def start_thread(self):
        if not self.thread.is_alive():
            self.thread.start()

    def send(self, data: Any):
        """Send data to the target peer, serializing it to this connection's default data format.

        Args:
            data (Any): the data to serialize and send

        Raises:
            ValueError: if this connection's default format is bytes and the data is not bytes
        """
        # send a header if the connection is not streaming
        # otherwise, data_type is fixed and known and data is of fixed size so header is useless
        # first encode data according to this connection's default data type
        if self.data_type == "raw":
            data = pickle.dumps(data)
        elif self.data_type == "json":
            data = json.dumps({
                "data": data
            }).encode("utf-8")
        else:
            if not isinstance(data, bytes):
                raise ValueError("data is not a bytes object")

        if not self.stream or self.data_size == "auto":
            # then send information about data
            header = build_data_header(len(data), self.data_type)
            self.sock.sendall(header)

            if self.data_size == "auto":
                self.data_size = len(data)

        # set the socket as blocking so that we wait for the data to be received
        self.sock.setblocking(True)
        self.sock.sendall(data)  # raises an error if data ain't fully sent

        # reset the socket timeout
        self.sock.settimeout(self.main_peer.timeout)

    def _receive_data(self, header: str):
        """Internal method to start the receiving process

        Args:
            header (str): the header first received from the other peer

        Returns:
            Any: the data received and deserialized (according to the data type referenced in the header)
        """
        header = split_header(header)
        # TODO: handle missing values
        data_type = header.get("data_type", "bytes")  # default most secure value to prevent attacks
        data_size = header.get("data_size", 0)

        if self.data_size == "auto":
            self.data_size = data_size

        if self.strict and data_type != self.data_type:
            self.main_peer.logger.warning(
                f"Data type received is not complying with data type established at connection: {data_type} != {self.data_type}")
            return None

        return self._receive(data_size, data_type)

    def _receive(self, data_size: int, data_type: str):
        # receiving data
        buffer = b""
        nb_chunks = data_size // self.buffer_size
        residue_size = data_size % self.buffer_size

        for _ in range(nb_chunks):
            buffer += self.sock.recv(self.buffer_size)
        if residue_size > 0:
            buffer += self.sock.recv(residue_size)

        # deserializing data
        data = None
        if data_type == "raw":
            data = pickle.loads(buffer)
        elif data_type == "json":
            data = json.loads(buffer)["data"]

        return data

    def close(self, force: bool = False):
        """Closes the connection nicely.

        Args:
            force (bool, optional): whether to force close the connection.
            This setting should be considered dangerous, as data can be lost. Defaults to False.
        """
        self.active = False
        self.sock.settimeout(0)  # try to speed up closing process

        if force:
            self.sock.shutdown(socket.SHUT_RDWR)

    def _listen(self):
        while self.active:
            # in case timeout has changed
            if self.main_peer.timeout != self.sock.gettimeout():
                self.sock.settimeout(self.main_peer.timeout)

            header, data = None, None
            try:
                # will block until any streaming data/header is received or socket timeout
                if self.stream and self.data_size != "auto":
                    data = self._receive(self.data_size, self.data_type)
                else:
                    header = self.sock.recv(headers.size).decode("utf-8")
            except socket.timeout:
                # no header/streaming data received within timeout seconds
                continue

            # if we received a data header, otherwise do nothing with the received packet
            if header is not None and header.startswith(headers.data_header):
                data = self._receive_data(header)

            if data is not None:
                # TODO: handle when sent data IS python's None
                self.handle("data", data)

        self.sock.close()
