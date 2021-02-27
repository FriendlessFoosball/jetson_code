import zmq
import multiprocessing as mp
import cv2
import time
import imutils

from imutils.video import VideoStream

def camera_ps(shutdown, outfd, hwm):
    context = zmq.Context()

    socket = context.socket(zmq.PUB)
    socket.setsockopt(zmq.SNDHWM, hwm)
    socket.bind(outfd)

    camera = VideoStream(src="nvarguscamerasrc ! video/x-raw(memory:NVMM), "\
                         "width=(int)1280, height=(int)720, format=(string)NV12, " \
                         "framerate=(fraction)50/1 ! nvvidconv flip-method=2 ! video/x-raw, " \
                         "format=(string)BGRx ! videoconvert ! video/x-raw, " \
                         "format=(string)BGR ! appsink").start()
    time.sleep(2.0)

    frame = 0

    while not shutdown.is_set():
        image = camera.read()
        image = imutils.resize(image, width=500)

        image = cv2.GaussianBlur(image, (11, 11), 0)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        snd = {'image': image, 'id': frame}

        try:
            socket.send_pyobj(snd, flags=zmq.NOBLOCK)
        except zmq.error.Again:
            print("hwm hit!")

        frame += 1

class Camera:
    hwm = 10

    def __init__(self, endpoint, framerate=50):
        self.outfd = endpoint
        self.shutdown = mp.Event()
        self.psargs = (self.shutdown, self.outfd, self.hwm)
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
