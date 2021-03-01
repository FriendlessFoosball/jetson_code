from foosball.camera import Camera
from tableconfig import config

if __name__ == '__main__':
    cam = Camera("ipc://tracks", config)
    cam.start()

    input("Press enter to stop")
    cam.stop()