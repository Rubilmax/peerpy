import sys
import os
# allow the example to be run without installing the package, from this repository's root directory
sys.path.append(os.path.abspath(os.path.join('.')))

import cv2
import time
import queue
from peerpy import Peer

# OpenCV's imshow is not thread-safe: instead, we push frames to each of the following queues
# and the main thread reads them and display frames
peer1_input = queue.Queue()
peer2_input = queue.Queue()


def handle_frame(frame):
    peer2_input.put(frame)


def display_frames():
    try:
        frame1 = peer1_input.get(timeout=.5)
        cv2.imshow("Webcam input", frame1)
    except queue.Empty:
        pass

    try:
        frame2 = peer2_input.get(timeout=.5)
        cv2.imshow("Peer 2 input", frame2)
    except queue.Empty:
        pass


cam = cv2.VideoCapture(0)

with Peer(port=12345, timeout=1) as peer1:
    # handler to be executed at connection time (returned value indicates whether to accept or deny the connection)
    def set_connection_handler(connection) -> bool:
        connection.handlers["data"] = handle_frame
        return connection.target_name == peer1.address_name  # only accept peer1's connections

    with Peer(port=11111, timeout=1, handlers={
        # configure connection before accepting it
        "connection": set_connection_handler
    }) as peer2:
        # data_type="raw" to tell the other peer that we are sending a python object (which will need to be unpickled)
        connection = peer1.connect(peer2.address, data_type="raw")

        if connection:  # if connection was successful
            while True:
                ret, frame = cam.read()

                if not ret:
                    print("Failed grabbing camera frame")
                    break

                k = cv2.waitKey(1)
                if k % 256 == 27:
                    print("Escape hit, closing...")
                    break

                connection.send(frame)
                peer1_input.put(frame)
                display_frames()

            cam.release()
            cv2.destroyAllWindows()
