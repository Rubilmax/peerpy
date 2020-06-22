import sys
import time
import numpy
import socket
import typing
import logging
import threading

from connection import Connection


class Peer():

    def __init__(self, address):
        self.address = address

        self.connections = []
        self.logger = logging.getLogger(f"[{self.address[0]}:{self.address[1]}]")
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.terminate_flag = threading.Event()
        self.thread = threading.Thread(target=self._listen)
        self.thread.start()

    def connect(self, address) -> Connection:
        peer_name = f"[{address[0]}:{address[1]}]"
        self.logger.debug(f"Sending offer to {peer_name}")

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect(address)

        connection = Connection(self, sock)
        self.connections.append(connection)

        self.logger.debug(f"Connection established with {peer_name}")

        return connection

    def broadcast(self, data):
        for connection in self.connections:
            connection.send(data)

    def stop(self):
        self.terminate_flag.set()

        for connection in self.connections:
            connection.close()

    def _listen(self):
        try:
            self.server.bind(self.address)
        except OSError as error:
            self.logger.error(error)
            return

        self.server.settimeout(5)
        self.server.listen()
        self.logger.debug(f"Listening for connections...")

        while not self.terminate_flag.is_set():
            try:
                # will block until offer received AND accepted or socket timeout
                sock, peer_address = self.server.accept()
            except socket.timeout:
                continue
            connection = Connection(self, sock)

            self.logger.debug(f"Offer from [{peer_address[0]}:{peer_address[1]}] accepted!")
            self.connections.append(connection)

        self.logger.debug("Stopped!")


peer1 = Peer(("localhost", 15151))
peer2 = Peer(("localhost", 15152))
time.sleep(2)
connection = peer1.connect(("localhost", 15152))

try:
    data = numpy.ones(1000000)
    print(sys.getsizeof(data))
    connection.send(data)
except Exception as ex:
    print(ex)
finally:
    logging.debug(f"Attempting stop...")
    peer1.stop()
    peer2.stop()
