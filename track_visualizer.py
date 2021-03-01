import zmq
import cv2
import numpy as np

def vis_player(c, l, r, off, img):
    out = cv2.rectangle(img, (off + l, c), (off + r, c + 30), (255, 255, 0), 2)
    out = cv2.rectangle(out, (off + l, c + 107), (off + r, c + 30 + 107), (255, 255, 0), 2)
    out = cv2.rectangle(out, (off + l, c + 215), (off + r, c + 30 + 215), (255, 255, 0), 2)
    return out

if __name__ == '__main__':
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.RCVHWM, 10)
    socket.connect("ipc://tracks")
    socket.subscribe("")

    while True:
        frame = socket.recv_pyobj()

        objpic = np.zeros((363, 500, 3), dtype='uint8')

        if frame['ball']['x'] != -1:
            objpic = cv2.circle(objpic, (int(frame['ball']['x']), int(frame['ball']['y'])), radius=10, color=(255, 255, 0), thickness=-1)

        cv2.putText(objpic, f"Ball X Velocity: {frame['ball']['xv']:.3f}", (300, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
        cv2.putText(objpic, f"Ball Y Velocity: {frame['ball']['yv']:.3f}", (300, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)

        cv2.putText(objpic, "{:.1f}".format(frame['human']['goalie']['ang']), (40, 350), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        objpic = vis_player(frame['human']['goalie']['loc'], 30, 90, 0, objpic)

        cv2.putText(objpic, "{:.1f}".format(frame['human']['offense']['ang']), (290, 350), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        objpic = vis_player(frame['human']['offense']['loc'], 30, 90, 250, objpic)

        cv2.putText(objpic, "{:.1f}".format(frame['robot']['goalie']['ang']), (415, 350), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        objpic = vis_player(frame['robot']['goalie']['loc'], 30, 90, 375, objpic)

        cv2.putText(objpic, "{:.1f}".format(frame['robot']['offense']['ang']), (165, 350), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        objpic = vis_player(frame['robot']['offense']['loc'], 30, 90, 125, objpic)

        cv2.imshow("Tracks", objpic)

        if cv2.waitKey(1) & 0xFF is ord('q'):
            break