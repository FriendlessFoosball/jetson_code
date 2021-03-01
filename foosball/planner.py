import zmq
import multiprocessing as mp
import onnxruntime as ort
import numpy as np

# 361 x 500
BALL_X_CENTER = 250
BALL_Y_CENTER = 180
FIELD_LENGTH = 233
FIELD_WIDTH = 163

MAX_BALL_VELOCITY = 30

MIN_AXLE_LOC = 7
MAX_AXLE_LOC = 116

center_loc = (MIN_AXLE_LOC + MAX_AXLE_LOC) / 2
diff = (MAX_AXLE_LOC - MIN_AXLE_LOC) / 2

MAX_LIN_VELOCITY = 16
MAX_ANG_VELOCITY = 30

LIN_MOVE_MULTIPLIER = 2
ANG_MOVE_MULTIPLIER = 20

PULLEY_DIA = 2.5476

def frame_to_observation(frame, vels, off_ang, goa_ang):
    obs = np.zeros((1, 16), dtype='float32')

    # Ball information
    obs[0,0] = -1 * (frame['ball']['x'] - BALL_X_CENTER) / FIELD_LENGTH
    obs[0,1] = (frame['ball']['y'] - BALL_Y_CENTER) / FIELD_WIDTH
    obs[0,2] = -1 * frame['ball']['xv'] / MAX_BALL_VELOCITY
    obs[0,3] = frame['ball']['yv'] / MAX_BALL_VELOCITY

    # Robot paddle information
    obs[0,4] = max(-1., min(1., (frame['robot']['offense']['loc'] - center_loc) / diff))
    obs[0,5] = vels[0] / MAX_LIN_VELOCITY
    obs[0,6] = off_ang / 180
    obs[0,7] = vels[1] / MAX_ANG_VELOCITY
    obs[0,8] = max(-1., min(1., (frame['robot']['goalie']['loc'] - center_loc) / diff))
    obs[0,9] = vels[2] / MAX_LIN_VELOCITY
    obs[0,10] = goa_ang / 180
    obs[0,11] = vels[3] / MAX_ANG_VELOCITY

    # opponent information
    obs[0,12] = max(-1., min(1., (frame['human']['offense']['loc'] - center_loc) / diff))
    obs[0,13] = -1 * frame['human']['offense']['ang'] / 180
    obs[0,14] = max(-1., min(1., (frame['human']['goalie']['loc'] - center_loc) / diff))
    obs[0,15] = -1 * frame['human']['goalie']['ang'] / 180

    return obs

def planner_ps(shutdown, infd, locfd, timerfd, outfd, inhwm, outhwm, model):
    context = zmq.Context()

    in_socket = context.socket(zmq.SUB)
    in_socket.setsockopt(zmq.RCVHWM, inhwm)
    in_socket.connect(infd)
    in_socket.subscribe("")

    loc_socket = context.socket(zmq.SUB)
    loc_socket.setsockopt(zmq.RCVHWM, 10)
    loc_socket.connect(locfd)
    loc_socket.subscribe("")

    timer_sock = context.socket(zmq.SUB)
    timer_sock.setsockopt(zmq.RCVHWM, 10)
    timer_sock.connect(timerfd)
    timer_sock.subscribe("")

    out_socket = context.socket(zmq.PUB)
    out_socket.setsockopt(zmq.SNDHWM, outhwm)
    out_socket.bind(outfd)

    poller = zmq.Poller()
    poller.register(in_socket, zmq.POLLIN)
    poller.register(loc_socket, zmq.POLLIN)
    poller.register(timer_sock, zmq.POLLIN)

    sess = ort.InferenceSession(model)

    # off_lin_vel = 0
    # off_ang_vel = 0
    # goa_lin_vel = 0
    # goa_ang_vel = 0

    # THESE ARE RELATIVE VELOCITIES!!!!!!!!!!!!
    vel = np.zeros((4, ), dtype='float32')
    curr_move = np.zeros((4, ), dtype='float32')

    # POSITIVE MEANS KICKING
    off_ang = 0
    goa_ang = 0

    while not shutdown.is_set():
        try:
            socks = dict(poller.poll())
        except KeyboardInterrupt:
            break

        if in_socket in socks:
            frame = in_socket.recv_pyobj()

            print(f"Processing frame {frame['frame']}")

            if frame['robot']['offense']['loc'] >= MAX_AXLE_LOC or frame['robot']['offense']['loc'] <= MIN_AXLE_LOC:
                vel[0] = 0

            if frame['robot']['goalie']['loc'] >= MAX_AXLE_LOC or frame['robot']['goalie']['loc'] <= MIN_AXLE_LOC:
                vel[2] = 0

            if frame['ball']['x'] == -1:
                vel[0:4] = 0
                curr_move[0:4] = 0
            else:
                obs = frame_to_observation(frame, vel, off_ang, goa_ang)
                inference = sess.run(None, {'vector_observation': obs})
                curr_move = inference[2][0]
        
        if loc_socket in socks:
            _, _, ga, oa = loc_socket.recv_pyobj()
            # RELATIVE ANGLE IS REVERSED!
            ga *= -(360 / 1600)
            oa *= -(360 / 1600)

            # mod between -180/180
            goa_ang = ((ga + 180) % 360) - 180
            off_ang = ((oa + 180) % 360) - 180

            print(f"Set angles to goalie: {goa_ang}, off: {off_ang}")

        if timer_sock in socks:
            _ = timer_sock.recv()

            off_lin_move = curr_move[0] * LIN_MOVE_MULTIPLIER
            if (abs(vel[0] + off_lin_move) > MAX_LIN_VELOCITY):
                spd = MAX_LIN_VELOCITY
                if (vel[0] < 0):
                    spd *= -1
                off_lin_move = spd - vel[0]

            vel[0] += off_lin_move

            off_ang_move = curr_move[1] * ANG_MOVE_MULTIPLIER
            if (abs(vel[1] + off_ang_move) > MAX_ANG_VELOCITY):
                spd = MAX_ANG_VELOCITY
                if (vel[1] < 0):
                    spd *= -1
                off_ang_move = spd - vel[1]

            vel[1] += off_ang_move

            goa_lin_move = curr_move[2] * LIN_MOVE_MULTIPLIER
            if (abs(vel[2] + goa_lin_move) > MAX_LIN_VELOCITY):
                spd = MAX_LIN_VELOCITY
                if (vel[2] < 0):
                    spd *= -1
                goa_lin_move = spd - vel[2]

            vel[2] += goa_lin_move

            goa_ang_move = curr_move[3] * ANG_MOVE_MULTIPLIER
            if (abs(vel[3] + goa_ang_move) > MAX_ANG_VELOCITY):
                spd = MAX_ANG_VELOCITY
                if (vel[3] < 0):
                    spd *= -1
                goa_ang_move = spd - vel[3]

            vel[3] += goa_ang_move

            # velocities aligned!

            off_lin_spd = int((vel[0] / (PULLEY_DIA / 2)) * (800 / np.pi))
            goa_lin_spd = int((vel[2] / (PULLEY_DIA / 2)) * (800 / np.pi))
            off_ang_spd = int(-vel[1] * (800 / np.pi))
            goa_ang_spd = int(-vel[3] * (800 / np.pi))

            try:
                out_socket.send_pyobj({
                    'command': 'set_all_speeds',
                    'goalie_lin': goa_lin_spd,
                    'offense_lin': off_lin_spd,
                    'goalie_ang': goa_ang_spd,
                    'offense_ang': off_ang_spd
                })
            except zmq.error.Again:
                print("oops")

            try:
                out_socket.send_pyobj({'command': 'get_all_positions'}, flags=zmq.NOBLOCK)
            except zmq.error.Again:
                print("oops")

    out_socket.send_pyobj({'command': 'set_all_speeds', 'goalie_lin': 0, 'offense_lin': 0, 'goalie_ang': 0, 'offense_ang': 0})
                

class Planner:
    inhwm = 1
    outhwm = 10

    def __init__(self, infd, locfd, timerfd, outfd, model):
        self.infd = infd
        self.outfd = outfd
        self.locfd = locfd
        self.timerfd = timerfd
        self.shutdown = mp.Event()
        self.psargs = (self.shutdown, self.infd, self.locfd, self.timerfd, self.outfd, self.inhwm, self.outhwm, model)
        self.ps = None

    def start(self):
        if self.ps is not None:
            raise RuntimeError("Planner already running!")

        self.ps = mp.Process(target=planner_ps, args=self.psargs)
        self.ps.daemon = True
        self.ps.start()
        print(self)

    def stop(self):
        if self.ps is None:
            raise RuntimeError("Planner not running")

        self.shutdown.set()
        self.ps.join()
        self.ps = None
        self.shutdown.clear()

    def __repr__(self):
        rpr = "-------Planner-------\n"
        rpr += f"IN: {self.infd}\n"
        rpr += f"OUT: {self.outfd}\n"
        rpr += f"INHWM: {self.inhwm}\n"
        rpr += f"OUTHWM: {self.outhwm}\n"

        return rpr