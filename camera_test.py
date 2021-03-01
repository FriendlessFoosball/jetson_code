import zmq
import cv2
import time
import threading

context = zmq.Context()

def recv(shutdown):
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.RCVHWM, 10)
    socket.connect('ipc://camera')
    socket.subscribe('')

    rep_socket = context.socket(zmq.REP)
    rep_socket.bind('inproc://cache')
    
    poller = zmq.Poller()
    poller.register(socket, zmq.POLLIN)
    poller.register(rep_socket, zmq.POLLIN)

    frame = None

    while not shutdown.is_set():
        try:
            socks = dict(poller.poll())
        except KeyboardInterrupt:
            break

        if socket in socks:
            item = socket.recv_pyobj()
            print(f"Received frame {item['id']}")
            frame = item

        if rep_socket in socks:
            msg = rep_socket.recv()
            rep_socket.send_pyobj(frame)

# async def show_frame():
#     global frame

#     while True:
#         if frame is not None:
#             #cv2.imshow("Stream", frame)
#             print(frame)
#             frame = None
#         #await asyncio.sleep(1)

# async def main():
#     await asyncio.gather(recv(), show_frame())

# asyncio.run(main())

if __name__ == '__main__':
    shutdown = threading.Event()
    args = (shutdown, )
    thread = threading.Thread(target=recv, args=args, daemon=True)
    thread.start()

    req_socket = context.socket(zmq.REQ)
    req_socket.connect('inproc://cache')

    while True:
        req_socket.send(b'hi!')

        item = req_socket.recv_pyobj()

        if item is None:
            time.sleep(0.001)
            continue

        cv2.imshow("Stream", item['image'])

        if cv2.waitKey(1) & 0xFF is ord('q'):
            break
    
    shutdown.set()
    thread.join()