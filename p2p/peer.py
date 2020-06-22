import sys
import time
import numpy
import socket
import typing
import logging
import threading

from .connection import Connection


class Peer():

    def __init__(self, address, timeout: int = 5):
        self.address = address
        self.timeout = timeout

        self.connections = {}
        self.logger = logging.getLogger(f"[{self.address[0]}:{self.address[1]}]")
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.terminate_flag = threading.Event()
        self.thread = threading.Thread(target=self._listen)
        self.thread.deamon = True
        self.thread.start()

    def connect(self, address) -> Connection:
        peer_name = f"[{address[0]}:{address[1]}]"

        if peer_name not in self.connections:
            self.logger.debug(f"Sending offer to {peer_name}")

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect(address)

            self.connections[peer_name] = Connection(self, sock)

            self.logger.debug(f"Connection established with {peer_name}")

        return self.connections[peer_name]

    def broadcast(self, data):
        for connection in self.connections.values():
            connection.send(data)

    def stop(self, _async=False):
        self.terminate_flag.set()

        for connection in self.connections.values():
            connection.close()

        if _async:
            for connection in self.connections.values():
                connection.thread.join()

            self.thread.join()

    def _listen(self):
        try:
            self.server.bind(self.address)
        except OSError as error:
            self.logger.error(error)
            return

        self.server.settimeout(self.timeout)
        self.server.listen()
        self.logger.debug(f"Listening for connections...")

        while not self.terminate_flag.is_set():
            try:
                # will block until offer received AND accepted or socket timeout
                sock, peer_address = self.server.accept()
            except socket.timeout:
                continue
            peer_name = f"[{peer_address[0]}:{peer_address[1]}]"
            self.connections[peer_name] = Connection(self, sock)

            self.logger.debug(f"Offer from [{peer_address[0]}:{peer_address[1]}] accepted!")

        self.logger.debug("Stopped!")
