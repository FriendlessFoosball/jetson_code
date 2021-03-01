import cv2
import imutils
import numpy as np
import time

from imutils.video import VideoStream
from collections import deque

class FPSCounter:
    def __init__(self):
        self.q = deque(maxlen=100)

    def frame(self):
        self.q.append(time.time())

    def fps(self):
        return len(self.q)/(self.q[-1] - self.q[0])

camera = VideoStream(src="nvarguscamerasrc wbmode=4 aelock=true gainrange=\"8 8\" ispdigitalgainrange=\"1 1\" exposuretimerange=\"5000000 5000000\" ! video/x-raw(memory:NVMM), "\
                        "width=(int)1280, height=(int)720, format=(string)NV12, " \
                        "framerate=(fraction)50/1 ! nvvidconv flip-method=2 ! video/x-raw, " \
                        "format=(string)BGRx ! videoconvert ! video/x-raw, " \
                        "format=(string)BGR ! appsink").start()

time.sleep(2.0)

tl = [200, 80]
tr = [1004, 95]
bl = [199, 646]
br = [990, 662]

BALL_THRESH = ((7, 0, 0), (61, 167, 255))
ROBOT_THRESH = ((150, 74, 37), (198, 255, 207))
HUMAN_THRESH = ((104, 175, 0), (128, 255, 255))

rect = np.array([tl, tr, br, bl])
blank = np.zeros((720, 1280), dtype='uint8')
mask = cv2.fillConvexPoly(blank, rect, 1)

filt = np.zeros((245, ))
filt[0:30] = 1
filt[107:137] = 1
filt[215:245] = 1

def get_player_pos(roi):
    col = np.sum(roi, axis=1)
    hgoalie_locs = np.convolve(col, filt, 'valid')
    #cv2.imshow("tracks", np.repeat(np.expand_dims(hgoalie_locs, axis=1), 100, axis=1) / 3000)
    return np.argmax(hgoalie_locs)

def get_player_bounds(roi):
    row = np.sum(roi, axis=0)
    mask = row != 0
    first = np.argmax(mask)
    last = len(mask) - np.argmax(np.flip(mask))

    return (first, last)

def vis_player(c, l, r, off, img):
    out = cv2.rectangle(img, (off + l, c), (off + r, c + 30), (255, 255, 0), 2)
    out = cv2.rectangle(out, (off + l, c + 107), (off + r, c + 30 + 107), (255, 255, 0), 2)
    out = cv2.rectangle(out, (off + l, c + 215), (off + r, c + 30 + 215), (255, 255, 0), 2)
    return out

fpsc = FPSCounter()
fpsc.frame()

i = 0

while True:
    image = camera.read()
    fpsc.frame()
    if i % 50 == 0:
        print(f"FPS: {fpsc.fps()}")
    i += 1

    image = cv2.bitwise_and(image, image, mask=mask)
    image = image[79:662, 198:1004]
    image = imutils.resize(image, width=500)

    #cv2.imshow("Camera", image)
    #objpic = image

    hsv = cv2.GaussianBlur(image, (11, 11), 0)
    hsv = cv2.cvtColor(hsv, cv2.COLOR_BGR2HSV)

    ball = cv2.inRange(hsv, *BALL_THRESH)
    robot = cv2.inRange(hsv, *ROBOT_THRESH)
    human = cv2.inRange(hsv, *HUMAN_THRESH)

    human = cv2.erode(human, None, iterations=2)
    #human = cv2.dilate(human, None, iterations=1)
    human = human / 255
    robot = robot / 255

    #objects = np.stack([ball, robot, human * 255], axis=2)
    #cv2.imshow("Objects", objects)

    # ball tracking
    if np.sum(ball) > 20 * 255:
        try:
            m = cv2.moments(ball, True)
            ballx, bally = m['m10']/m['m00'], m['m01']/m['m00']

            #objpic = cv2.circle(objpic, (int(ballx), int(bally)), radius=10, color=(255, 255, 0), thickness=-1)
        except ZeroDivisionError:
            ballx, bally = -1, -1
    else:
        ballx, bally = -1, -1

    # human tracking
    hg_loc = get_player_pos(human[:, 0:125])
    hg_l, hg_r = get_player_bounds(human[:, 0:125])

    #objpic = vis_player(hg_loc, hg_l, hg_r, 0, objpic)

    ho_loc = get_player_pos(human[:, 250:375])
    ho_l, ho_r = get_player_bounds(human[:, 250:375])

    #objpic = vis_player(ho_loc, ho_l, ho_r, 250, objpic)

    # robot tracking
    rg_loc = get_player_pos(robot[:, 375:500])
    rg_l, rg_r = get_player_bounds(robot[:, 375:500])

    #objpic = vis_player(rg_loc, rg_l, rg_r, 375, objpic)

    ro_loc = get_player_pos(robot[:, 125:250])
    ro_l, ro_r = get_player_bounds(robot[:, 125:250])

    #objpic = vis_player(ro_loc, ro_l, ro_r, 125, objpic)

    #cv2.imshow("Tracks", objpic)

    # if cv2.waitKey(1) & 0xFF is ord('q'):
    #     break