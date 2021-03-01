import zmq
import multiprocessing as mp
import cv2
import time
import imutils

from imutils.video import VideoStream
from foosball.perception_utils import *
from foosball.angle_finder import find_angle

def camera_ps(shutdown, outfd, hwm, config, on_jetson):
    context = zmq.Context()

    socket = context.socket(zmq.PUB)
    socket.setsockopt(zmq.SNDHWM, hwm)
    socket.bind(outfd)

    if on_jetson:
        camera = VideoStream(src="nvarguscamerasrc wbmode=4 aelock=true gainrange=\"8 8\" ispdigitalgainrange=\"1 1\" exposuretimerange=\"5000000 5000000\" ! video/x-raw(memory:NVMM), "\
                            "width=(int)1280, height=(int)720, format=(string)NV12, " \
                            "framerate=(fraction)40/1 ! nvvidconv flip-method=2 ! video/x-raw, " \
                            "format=(string)BGRx ! videoconvert ! video/x-raw, " \
                            "format=(string)BGR ! appsink").start()
    else:
        camera = VideoStream('unity_5.mkv')
    time.sleep(2.0)

    frame = 0
    mask = get_mask(config['ROI'])
    filt = get_filt()
    vm = VelocityMonitor()
    roi = config['ROI']
    bt = config['BALL_THRESH']
    rt = config['ROBOT_THRESH']
    ht = config['HUMAN_THRESH']

    while not shutdown.is_set():
        # Fetch and crop frame
        image = camera.read()
        image = crop_image(image, mask)
        image = imutils.resize(image, width=500)

        # Preprocess frame for perception
        hsv = cv2.GaussianBlur(image, (11, 11), 0)
        hsv = cv2.cvtColor(hsv, cv2.COLOR_BGR2HSV)

        # Threshold frame
        ball = cv2.inRange(hsv, *bt)
        robot = cv2.inRange(hsv, *rt)
        human = cv2.inRange(hsv, *ht)

        # Postprocess thresholds
        human = cv2.erode(human, None, iterations=2)
        human = human / 255
        robot = robot / 255

        # Track ball
        try:
            ballx, bally = track_ball(ball)
            vm.pos(ballx, bally)
        except ValueError:
            ballx, bally = -1., -1.
            vm.clear()

        ballxv, ballyv = vm.velocity()
        ballxv /= config['PIXELS_PER_CM']
        ballyv /= config['PIXELS_PER_CM']

        # Track human player
        hg_roi = human[:, 0:125]
        hg_loc = get_player_pos(hg_roi, filt)
        hg_l, hg_r = get_player_bounds(hg_roi)
        hg_ang = -find_angle(*mirror_player(hg_l, hg_r, *config['GOALIE_PARAMS']), True)

        ho_roi = human[:, 250:375]
        ho_loc = get_player_pos(ho_roi, filt)
        ho_l, ho_r = get_player_bounds(ho_roi)
        ho_ang = -find_angle(*mirror_player(ho_l, ho_r, *config['OFFENSE_PARAMS']), False)

        # Track robot player
        rg_roi = robot[:, 375:500]
        rg_loc = get_player_pos(rg_roi, filt)
        rg_l, rg_r = get_player_bounds(rg_roi)
        rg_ang = find_angle(rg_l, rg_r, True)

        ro_roi = robot[:, 125:250]
        ro_loc = get_player_pos(ro_roi, filt)
        ro_l, ro_r = get_player_bounds(ro_roi)
        ro_ang = find_angle(ro_l, ro_r, False)

        # Compile track object
        tracks = {
            'frame': frame,
            'ball': {
                'x': ballx,
                'y': bally,
                'xv': ballxv,
                'yv': ballyv
            },
            'human': {
                'goalie': {
                    'loc': hg_loc,
                    'ang': hg_ang
                },
                'offense': {
                    'loc': ho_loc,
                    'ang': ho_ang
                }
            },
            'robot': {
                'goalie': {
                    'loc': rg_loc,
                    'ang': rg_ang
                },
                'offense': {
                    'loc': ro_loc,
                    'ang': ro_ang
                }
            }
        }

        print(f"Sending frame {frame}")
        try:
            socket.send_pyobj(tracks, flags=zmq.NOBLOCK)
        except zmq.error.Again:
            print("hwm hit!")

        frame += 1

class Camera:
    hwm = 10

    def __init__(self, endpoint, config, is_jetson=True):
        self.outfd = endpoint
        self.shutdown = mp.Event()
        self.psargs = (self.shutdown, self.outfd, self.hwm, config, is_jetson)
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
