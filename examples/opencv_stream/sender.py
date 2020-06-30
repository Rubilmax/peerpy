import sys
import os
# allow the example to be run without installing the package, from this repository's root directory
sys.path.append(os.path.abspath(os.path.join('.')))

import cv2
import queue

from peerpy import Peer, protocol


cam = cv2.VideoCapture(0)

with Peer(timeout=1) as peer:
    while True:
        ret, frame = cam.read()

        if not ret:
            print("Failed grabbing camera frame")
            break

        k = cv2.waitKey(1)
        if k % 256 == 27:
            print("Escape hit, closing...")
            break

        peer.broadcast(frame)
        #cv2.imshow("Webcam", frame)

cam.release()
# cv2.destroyAllWindows()
