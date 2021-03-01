import cv2
import imutils
import time

from imutils.video import VideoStream

camera = VideoStream(src="nvarguscamerasrc ! video/x-raw(memory:NVMM), "\
                        "width=(int)1280, height=(int)720, format=(string)NV12, " \
                        "framerate=(fraction)50/1 ! nvvidconv flip-method=2 ! video/x-raw, " \
                        "format=(string)BGRx ! videoconvert ! video/x-raw, " \
                        "format=(string)BGR ! appsink").start()

time.sleep(2.0)

image = camera.read()
#image = imutils.resize(image, width=500)
print(image.shape)

cv2.imwrite("foosball.png", image)