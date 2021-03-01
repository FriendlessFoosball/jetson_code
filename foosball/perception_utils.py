import cv2
import time
import numpy as np

from collections import deque

class VelocityMonitor:
    def __init__(self, ma_len=3, velocity_len=5):
        self.locs = deque(maxlen=ma_len)
        self.mas = deque(maxlen=velocity_len)

    def clear(self):
        self.locs.clear()
        self.mas.clear()

    def _update_mas(self):
        if len(self.locs) == 0:
            return

        xs, ys = zip(*self.locs)
        ax = sum(xs) / len(xs)
        ay = sum(ys) / len(ys)
        self.mas.append((ax, ay, time.time()))

    def pos(self, x, y):
        self.locs.append((x, y))
        self._update_mas()

    def velocity(self):
        if len(self.locs) < 2:
            return 0., 0.
        
        dx = self.mas[-1][0] - self.mas[0][0]
        dy = self.mas[-1][1] - self.mas[0][1]
        dt = self.mas[-1][2] - self.mas[0][2]

        return dx / dt, dy / dt

def get_mask(rect):
    rect = np.array(rect)
    blank = np.zeros((720, 1280), dtype='uint8')
    return cv2.fillConvexPoly(blank, rect, 1)

def crop_image(image, mask):
    crop = cv2.bitwise_and(image, image, mask=mask)
    return crop[79:662, 198:1004]

def track_ball(ball_thresh):
    if np.sum(ball_thresh) <= 20 * 255:
        raise ValueError("No ball in image")

    try:
        m = cv2.moments(ball_thresh, True)
        x, y = m['m10']/m['m00'], m['m01']/m['m00']
    except ZeroDivisionError:
        raise ValueError("No ball in image")

    return x, y

def get_filt():
    filt = np.zeros((245, ))
    filt[0:30] = 1
    filt[107:137] = 1
    filt[215:245] = 1

    return filt

def get_player_pos(roi, filt):
    col = np.sum(roi, axis=1)
    potential_locs = np.convolve(col, filt, 'valid')
    return np.argmax(potential_locs)

def get_player_bounds(roi):
    row = np.sum(roi, axis=0)
    mask = row != 0
    first = np.argmax(mask)
    last = len(mask) - np.argmax(np.flip(mask))

    return first, last

def mirror_player(l, r, center, lshift, rshift):
    nr = min(2 * center - l + rshift, 125)
    nl = max(2 * center - r + lshift, 0)

    return nl, nr