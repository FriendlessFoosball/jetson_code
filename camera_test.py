import asyncio
import zmq
import cv2
from zmq.asyncio import Context
import time

context = Context.instance()
frame = None

async def recv():
    global frame

    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.RCVHWM, 10)
    socket.connect('tcp://localhost:5558')
    socket.subscribe('')

    while True:
        item = await socket.recv_pyobj()
        print(f"Received frame {item['id']}")
        frame = item['image']

async def show_frame():
    global frame

    while True:
        if frame is not None:
            #cv2.imshow("Stream", frame)
            print(frame)
            frame = None
        #await asyncio.sleep(1)

async def main():
    await asyncio.gather(recv(), show_frame())

asyncio.run(main())

# if __name__ == '__main__':
#     context = Context.instance()

#     socket = context.socket(zmq.SUB)
#     socket.setsockopt(zmq.RCVHWM, 10)
#     socket.connect('tcp://localhost:5558')
#     socket.subscribe('')

#     while True:
#         item = socket.recv_pyobj()
#         print(f"Received frame {item['id']}")

#         cv2.imshow("Stream", item['image'])

#         if cv2.waitKey(1) & 0xFF is ord('q'):
#             break