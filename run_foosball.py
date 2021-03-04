import time

from foosball import Camera, Timer, Planner, Controller
from tableconfig import config

def main():
    cam = Camera("ipc://tracks", config)
    timer = Timer("ipc://timer")
    pl = Planner("ipc://tracks", "ipc://pos_ret", "ipc://timer", "ipc://cmds", "models/gmtrain.onnx")
    cont = Controller("ipc://cmds", "ipc://pos_ret")

    cam.start()
    time.sleep(5.0)

    timer.start()
    cont.start()
    time.sleep(1.0)

    pl.start()

    input("Press enter to stop")
    pl.stop()
    timer.stop()
    cam.stop()
    time.sleep(0.5)

    cont.stop()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pl.stop()
        timer.stop()
        cam.stop()
        time.sleep(0.5)

        cont.stop()