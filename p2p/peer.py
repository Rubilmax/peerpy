import sys
import time

import socket
import random
import logging
import threading

from .utils import hello_header, header_max_size, build_header, split_header, get_local_ip, check_address
from .connection import Connection


class Peer():

    def __init__(self, address: str = None, port: int = 0, timeout: int = 5, invisible: bool = False):
        if address is None:
            address = get_local_ip()
        elif ":" in address:
            address, port = address.split(":")[:2]

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((address, int(port)))
        self.server.settimeout(timeout)

        self.connections = {}
        self.logger = logging.getLogger(f"[{self.address_name}]")

        self.stop_server_flag = threading.Event()
        self.server_thread = threading.Thread(target=self._listen_offers)
        self.server_thread.deamon = True
        self.server_thread.start()

        self.pinger_thread = threading.Thread(target=self._listen_pings)
        self.pinger_thread.deamon = True
        self.invisible = invisible  # needs to be the last because checks the pinger_thread state

    @property
    def address(self):
        return self.server.getsockname()

    @property
    def address_name(self):
        return f"{self.address[0]}:{self.address[1]}"

    @property
    def timeout(self):
        return self.server.gettimeout()

    @property
    def invisible(self):
        return self._invisible

    @invisible.setter
    def invisible(self, invisible):
        self._invisible = invisible

        if not invisible and not self.pinger_thread.is_alive():
            self.pinger_thread.start()

    def connect(self, address: str, port: int = None, buffer_size: int = 2 ** 13, data_type: str = "raw") -> Connection:
        address, address_name = check_address(address, port)

        if address_name not in self.connections:
            self.logger.debug(f"Sending offer to [{address_name}]")

            # TODO: use create_connection for ipv4 + ipv6 ??
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect(address)

            header = build_header({
                "peer_name": self.address_name,
                "buffer_size": buffer_size,
                "data_type": data_type
            }).encode("utf-8")
            sock.send(header)

            self.connections[address_name] = Connection(self, sock, buffer_size=buffer_size, data_type=data_type)

            self.logger.debug(f"Connection established with [{address_name}]")

        return self.connections[address_name]

    def get_local_peers(self):
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

    def broadcast(self, data, data_type: str = "raw"):
        for connection in self.connections.values():
            connection.send(data, data_type)

    def stop(self, _async=False):
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
        self.server.listen()

        self.logger.info(f"Listening for connections...")

        while not self.stop_server_flag.is_set():
            try:
                # will block until offer received AND accepted or socket timeout
                sock, peer_address = self.server.accept()
            except socket.timeout:
                # no offer received within timeout seconds
                continue

            sock.settimeout(self.timeout)

            try:
                # will block until a hello header is received
                header = sock.recv(header_max_size).decode("utf-8")
            except socket.timeout:
                # no offer received within timeout seconds
                sock.close()
                continue

            if header.startswith(hello_header):
                header = split_header(header, hello_header)
                peer_name = header["peer_name"]

                self.connections[peer_name] = Connection(
                    self,
                    sock,
                    buffer_size=header["buffer_size"],
                    data_type=header["data_type"]
                )
                self.logger.debug(f"Offer from [{peer_name}] accepted!")

        self.server.close()
        self.logger.debug("Server stopped!")

    def _listen_pings(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as pinger:
            pinger.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            pinger.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            pinger.settimeout(.5)

            # will raise EADDRINUSE error if 2 peers are from the same device on Windows
            pinger.bind(("", 1024))

            self.logger.debug("Pinger waiting for pings...")

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
