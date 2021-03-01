import zmq
import time

from collections import deque

if __name__ == '__main__':
    q = deque(maxlen=100)
    q.append(time.time())

    i = 0
    
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.RCVHWM, 10)
    socket.connect("ipc://tracks")
    socket.subscribe("")

    while True:
        i += 1
        frame = socket.recv_pyobj()
        #print(frame)
        q.append(time.time())
        if i % 100 == 0:
            fps = len(q) / (q[-1] - q[0])
            print(f"FPS: {fps}")
