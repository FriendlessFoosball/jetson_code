import zmq
import multiprocessing as mp
import time


def serial_recv(endpoint):
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.RCVHWM, 10)
    socket.bind('tcp://localhost:5558')
    socket.subscribe('')

    while True:
        item = socket.recv_pyobj()
        


class SerialInterface:
    hwm = 10

    def __init__(self, endpoint, framerate=50, is_jetson=True):
        self.outfd = endpoint
        self.shutdown = mp.Event()
        self.psargs = (self.shutdown, self.outfd, self.hwm, framerate, is_jetson)
        self.ps = None

    def start(self):
        if self.ps is not None:
            raise RuntimeError("Serial Interface already running!")

        self.ps = mp.Process(target=serial_recv, args=self.psargs)
        self.ps.daemon = True
        self.ps.start()
        print(self)

    def stop(self):
        if self.ps is None:
            raise RuntimeError("Serial Interface not running")

        self.shutdown.set()
        self.ps.join()
        self.ps = None
        self.shutdown.clear()

    def __repr__(self):
        rpr = "-------Serial Interface-------\n"
        rpr += f"OUT: {self.outfd}\n"
        rpr += f"HWM: {self.hwm}\n"

        return rpr