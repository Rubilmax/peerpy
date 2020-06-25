import sys
import time

import socket
import random
import logging
import threading

from typing import Tuple, List, Any

from .connection import Connection
from .utils import hello_header, header_max_size, build_hello_header, split_header, get_local_ip, check_address, default_buffer_size


class Peer():

    def __init__(self, address: str = None, port: int = 0, timeout: int = 5, invisible: bool = False, max_connections: int = 0):
        if address is None:
            address = get_local_ip()
        elif ":" in address:
            address, port = address.split(":")[:2]

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((address, int(port)))
        self.server.settimeout(timeout)

        self.connections = {}
        self.max_connections = max_connections
        self.logger = logging.getLogger(f"[{self.address_name}]")

        self.stop_server_flag = threading.Event()
        self.server_thread = threading.Thread(target=self._listen_offers)
        self.server_thread.deamon = True
        self.server_thread.start()

        self.pinger_thread = threading.Thread(target=self._listen_pings)
        self.pinger_thread.deamon = True
        self.invisible = invisible  # needs to be the last because checks the pinger_thread state

    @property
    def address(self) -> Tuple[str, int]:
        """This peer' address, in a normalized format

        Returns:
            Tuple[str, int]: the normalized address (ipv4, port)
        """
        return self.server.getsockname()

    @property
    def address_name(self) -> str:
        """This peer's normalized address name

        Returns:
            str: the normalized address name ipv4:port
        """
        return f"{self.address[0]}:{self.address[1]}"

    @property
    def timeout(self) -> float:
        """This peer's default timeout

        Returns:
            float: the default timeout
        """
        return self.server.gettimeout()

    @timeout.setter
    def timeout(self, timeout: float):
        """Sets this peer's default timeout'

        Args:
            timeout (float): the default timeout to set
        """
        self.server.settimeout(timeout)

    @property
    def invisible(self) -> bool:
        """Whether this peer is invisible to other peers on the same local network

        Returns:
            bool: this peer's invisibility
        """
        return self._invisible

    @invisible.setter
    def invisible(self, invisible: bool):
        """Sets wether this peer is invisible to other peers on the same local network

        Args:
            invisible (bool): this peer's invisibility'
        """
        self._invisible = invisible

        # if this peer's now visible and the pinger thread is stopped, restart it
        if not invisible and not self.pinger_thread.is_alive():
            self.pinger_thread.start()

    def connect(self, address: str, port: int = None, buffer_size: int = default_buffer_size, data_type: str = "raw", strict: bool = True) -> Connection:
        """Attempts to start a connection with a remote peer located at (address, port).
        Additional arguments are passed to the Connection constructor and sent to the remote peer right after successful
        connection, so that it knows with what data type to communicate with.

        Args:
            address (str): the ipv4 address of the remote peer, provided with the port if wanted (ipv4:port)
            port (int, optional): the port to use for the connection, if not provided in address. Defaults to None.
            buffer_size (int, optional): the buffer size to use to receive data. Defaults to p2p.utils.default_buffer_size.
            data_type (str, optional): the data type to use for the connection. Defaults to "raw".
            strict (bool, optional): whether this connection is strict on data types. Defaults to True.

        Returns:
            Connection: the connection, if established
        """
        address, address_name = check_address(address, port)

        if address_name not in self.connections:
            # TODO: use create_connection for ipv4 + ipv6 ??
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)

            try:
                sock.connect(address)
            except socket.timeout:
                return False

            header = build_hello_header(self.address_name, data_type)
            sock.sendall(header.encode("utf-8"))

            self.connections[address_name] = Connection(
                self,
                sock,
                buffer_size=buffer_size,
                data_type=data_type,
                strict=strict
            )
            self.logger.debug(f"Connection established with [{address_name}]")

        return self.connections.get(address_name, False)

    def get_local_peers(self) -> List[str]:
        """Returns the list of peers visible on the same local network.

        Returns:
            List[str]: the list of visible peers' addresses
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(.5)

        sock.bind((get_local_ip(), 1024))

        self.logger.debug(f"Pinging local network...")

        address, port = sock.getsockname()
        sock.sendto(f"PING {address}:{port}".encode("utf-8"), ("<broadcast>", 1024))

        addresses = []
        while True:
            try:
                data = sock.recv(512).decode("utf-8")
            except socket.timeout:
                break

            if "PONG" in data:
                address_name = data.split(" ")[1]
                if address_name != self.address_name:
                    self.logger.debug(f"Received pong from {address_name}!")
                    addresses.append(address_name)

        return addresses

    def broadcast(self, data: Any):
        """Broadcasts data to all the connected peers.

        Args:
            data (Any): the data to broadcast
        """
        for connection in self.connections.values():
            # TODO: handle type(data) != connection.data_type
            connection.send(data)

    def stop(self, _async=False):
        """Attempts to stop this peer and all its connections.

        Args:
            _async (bool, optional): whether to stop this peer asynchronously. Defaults to False.
        """
        self.stop_server_flag.set()

        for connection in self.connections.values():
            connection.close()

        if _async:
            for connection in self.connections.values():
                connection.thread.join()

            if self.server_thread.is_alive():
                self.server_thread.join()
            if self.pinger_thread.is_alive():
                self.pinger_thread.join()

    def _listen_offers(self):
        """Starts this peer's server, used to listen for connection requests."""

        self.server.listen()

        while not self.stop_server_flag.is_set():
            if len(self.connections) >= self.max_connections > 0:
                time.sleep(1)
                continue

            try:
                # will block until offer received AND accepted or socket timeout
                sock, peer_address = self.server.accept()
            except socket.timeout:
                # no offer received within timeout seconds
                continue

            sock.settimeout(self.timeout)
            self.logger.debug(f"Received offer from {peer_address}...")

            try:
                # will block until a hello header is received
                header = sock.recv(header_max_size).decode("utf-8")
            except socket.timeout:
                # no offer received within timeout seconds, we cancel the connection
                sock.close()
                continue

            if header.startswith(hello_header):
                header = split_header(header)
                peer_name = header.get("peer_name", "UNKNOWN_PEER")

                self.connections[peer_name] = Connection(
                    self,
                    sock,
                    buffer_size=default_buffer_size,
                    data_type=header.get("data_type", "bytes")  # default most secure value to prevent attacks
                )
                self.logger.debug(f"Offer from [{peer_name}] accepted!")

        self.server.close()
        self.logger.debug("Server stopped!")

    def _listen_pings(self):
        """Starts this peer's pinger, used to answer pings from other seeking peers."""

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as pinger:
            pinger.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            pinger.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            pinger.settimeout(.5)

            # will raise EADDRINUSE error if 2 peers are from the same device on Windows
            pinger.bind(("", 1024))

            while not self.stop_server_flag.is_set() and not self.invisible:
                try:
                    data = pinger.recv(512).decode("utf-8")
                except socket.timeout:
                    continue

                if "PING" in data and not self.invisible:  # in case this peer's visibility changed within the timeout window
                    address_name = data.split(" ")[1]

                    self.logger.debug(f"Received ping from {address_name}!")

                    address, port = address_name.split(":")
                    pinger.sendto(f"PONG {self.address_name}".encode("utf-8"), (address, int(port)))

        self.logger.debug("Pinger stopped!")
