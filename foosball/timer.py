import zmq
import multiprocessing as mp

def timer_ps(shutdown, outfd, hwm, interval):
    context = zmq.Context()

    socket = context.socket(zmq.PUB)
    socket.setsockopt(zmq.SNDHWM, hwm)
    socket.bind(outfd)
    
    while not shutdown.is_set():
        if shutdown.wait(interval / 1000):
            break
        
        try:
            socket.send(b"beat")
        except zmq.error.Again:
            print("oops")

class Timer:
    hwm = 10

    def __init__(self, outfd, interval=20):
        self.outfd = outfd
        self.shutdown = mp.Event()
        self.psargs = (self.shutdown, self.outfd, self.hwm, interval)
        self.ps = None

    def start(self):
        if self.ps is not None:
            raise RuntimeError("Timer already running!")

        self.ps = mp.Process(target=timer_ps, args=self.psargs)
        self.ps.daemon = True
        self.ps.start()
        print(self)

    def stop(self):
        if self.ps is None:
            raise RuntimeError("Timer not running")

        self.shutdown.set()
        self.ps.join()
        self.ps = None
        self.shutdown.clear()

    def __repr__(self):
        rpr = "-------Timer-------\n"
        rpr += f"OUT: {self.outfd}\n"
        rpr += f"HWM: {self.hwm}\n"

        return rpr