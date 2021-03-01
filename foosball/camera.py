import zmq
import multiprocessing as mp
import cv2
import time
import imutils

from collections import deque
from imutils.video import VideoStream

class FPSCounter:
    def __init__(self):
        self.q = deque(maxlen=100)

    def frame(self):
        self.q.append(time.time())

    def fps(self):
        return len(self.q)/(self.q[-1] - self.q[0])

def camera_ps(shutdown, outfd, hwm, framerate, on_jetson):
    context = zmq.Context()

    socket = context.socket(zmq.PUB)
    socket.setsockopt(zmq.SNDHWM, hwm)
    socket.bind(outfd)

    if on_jetson:
        camera = VideoStream(src="nvarguscamerasrc ! video/x-raw(memory:NVMM), "\
                            "width=(int)1280, height=(int)720, format=(string)NV12, " \
                            "framerate=(fraction)50/1 ! nvvidconv flip-method=2 ! video/x-raw, " \
                            "format=(string)BGRx ! videoconvert ! video/x-raw, " \
                            "format=(string)BGR ! appsink").start()
    else:
        camera = VideoStream('unity_5.mkv')
    time.sleep(2.0)

    frame = 0
    fpsc = FPSCounter()
    fpsc.frame()

    while not shutdown.is_set():
        fpsc.frame()
        image = camera.read()
        image = imutils.resize(image, width=500)

        image = cv2.GaussianBlur(image, (11, 11), 0)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # undistort and do four-point transform/crop

        snd = [image.tobytes(), bytes(str(frame), 'utf-8')]
        print(f"Sending frame {frame}")
        print(f"FPS: {fpsc.fps()}")

        try:
            socket.send_multipart(snd, flags=zmq.NOBLOCK)
        except zmq.error.Again:
            print("hwm hit!")

        frame += 1

class Camera:
    hwm = 10

    def __init__(self, endpoint, framerate=50, is_jetson=True):
        self.outfd = endpoint
        self.shutdown = mp.Event()
        self.psargs = (self.shutdown, self.outfd, self.hwm, framerate, is_jetson)
        self.ps = None

    def start(self):
        if self.ps is not None:
            raise RuntimeError("Camera already running!")

        self.ps = mp.Process(target=camera_ps, args=self.psargs)
        self.ps.daemon = True
        self.ps.start()
        print(self)

    def stop(self):
        if self.ps is None:
            raise RuntimeError("Camera not running")

        self.shutdown.set()
        self.ps.join()
        self.ps = None
        self.shutdown.clear()

    def __repr__(self):
        rpr = "-------Camera-------\n"
        rpr += f"OUT: {self.outfd}\n"
        rpr += f"HWM: {self.hwm}\n"

        return rpr
