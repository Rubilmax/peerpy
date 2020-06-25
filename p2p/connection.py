import json
import pickle
import socket
import threading
from typing import Any

from .event_handler import EventHandler
from .utils import default_connection_handlers
from .headers import data_header, header_size, build_data_header, split_header


class Connection(EventHandler):

    def __init__(self, main_peer, target_name: str, sock: socket.socket, buffer_size: int, **kwargs):
        data_type = str(kwargs.get("data_type", "json"))
        if data_type not in ["raw", "json", "bytes"]:
            raise ValueError("data_type must be one of ['raw', 'json', 'bytes']")

        handlers = dict(kwargs.get("handlers", default_connection_handlers))
        super().__init__(handlers)

        self.main_peer = main_peer
        self.target_name = str(target_name)
        self.sock = sock
        self.buffer_size = int(buffer_size)
        self._data_type = data_type
        self.strict = bool(kwargs.get("strict", True))
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

        # then send information about data
        header = build_data_header(len(data), self.data_type)
        self.sock.sendall(header)

        # set the socket as blocking so that we wait for the data to be received
        self.sock.setblocking(True)
        self.sock.sendall(data)  # raises an error if data ain't fully sent

        # reset the socket timeout
        self.sock.settimeout(self.main_peer.timeout)

    def _receive(self, header: str):
        """Internal method to start the receiving process

        Args:
            header (str): the header first received from the other peer

        Returns:
            Any: the data received and deserialized (according to the data type referenced in the header)
        """
        header = split_header(header)
        data_type = header.get("data_type", "bytes")  # default most secure value to prevent attacks
        data_size = header.get("data_size", 0)

        if self.strict and data_type != self.data_type:
            self.main_peer.logger.warning(
                f"Data type received is not complying with data type established at connection: {data_type} != {self.data_type}")
            return None

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

            try:
                # will block until any header is received or socket timeout
                header = self.sock.recv(header_size).decode("utf-8")
            except socket.timeout:
                # no header received within timeout seconds
                continue

            # if we received a data header, otherwise do nothing with the received packet
            if header.startswith(data_header):
                data = self._receive(header)

                # TODO: handle when sent data IS python's None
                if data is not None:
                    self.main_peer.logger.debug(f"Data received! Handlers: {self.handlers}")

                    self.handle("data", data)

        self.sock.close()
        self.main_peer.logger.debug("Connection stopped!")
