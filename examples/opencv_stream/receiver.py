import sys
import os
# allow the example to be run without installing the package, from this repository's root directory
sys.path.append(os.path.abspath(os.path.join('.')))

import cv2
import time
import queue

from peerpy import Peer, protocol

# OpenCV's imshow is not thread-safe: instead, we push frames to a queue
# and the main thread reads it and display frames
frames = queue.Queue()

# by default, whenever a frame is received from a connection, put it in the queue
protocol.defaults.connection_handlers["data"] = lambda frame: frames.put(frame)


with Peer(timeout=1) as peer:
    address_name = input("Address to connect to (CTRL+C to stop):\n")
    # data_type="raw" to tell the other peer that we are sending a python object (which will need to be unpickled)
    connection = peer.connect(address_name, data_type="raw", stream=True)

    if connection:  # if connection was successful
        while True:
            try:
                frame = frames.get(timeout=.5)
                cv2.imshow("Remote stream", frame)
            except queue.Empty:
                print("No frame received!")
                continue
    else:
        print("Connection couldn't be established!")

cv2.destroyAllWindows()
