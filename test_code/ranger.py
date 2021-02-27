from imutils.video import VideoStream
import imutils
import cv2
import time
from operator import xor


def callback(value):
    pass


def setup_trackbars(range_filter):
    cv2.namedWindow("Trackbars", 0)

    for i in ["MIN", "MAX"]:
        v = 0 if i == "MIN" else 255

        for j in range_filter:
            cv2.createTrackbar("%s_%s" % (j, i), "Trackbars", v, 255, callback)


def get_trackbar_values(range_filter):
    values = []

    for i in ["MIN", "MAX"]:
        for j in range_filter:
            v = cv2.getTrackbarPos("%s_%s" % (j, i), "Trackbars")
            values.append(v)

    return values


def main():
    range_filter = 'HSV'

    camera = VideoStream(src="nvarguscamerasrc wbmode=4 aelock=true gainrange=\"8 8\" ispdigitalgainrange=\"1 1\" exposuretimerange=\"5000000 5000000\" ! video/x-raw(memory:NVMM), "\
                         "width=(int)1280, height=(int)720, format=(string)NV12, " \
                         "framerate=(fraction)50/1 ! nvvidconv flip-method=2 ! video/x-raw, " \
                         "format=(string)BGRx ! videoconvert ! video/x-raw, " \
                         "format=(string)BGR ! appsink").start()
    time.sleep(2.0)
    # camera = cv2.VideoCapture(0)

    setup_trackbars(range_filter)

    while True:
        image = camera.read()
        image = imutils.resize(image, width=500)

        frame_to_thresh = cv2.GaussianBlur(image, (11, 11), 0)
        frame_to_thresh = cv2.cvtColor(frame_to_thresh, cv2.COLOR_BGR2HSV)

        v1_min, v2_min, v3_min, v1_max, v2_max, v3_max = get_trackbar_values(range_filter)

        thresh = cv2.inRange(frame_to_thresh, (v1_min, v2_min, v3_min), (v1_max, v2_max, v3_max))
        #thresh = cv2.erode(thresh, None, iterations=2)
        #thresh = cv2.dilate(thresh, None, iterations=2)

        # if args['preview']:
        #     preview = cv2.bitwise_and(image, image, mask=thresh)
        #     cv2.imshow("Preview", preview)
        # else:
        cv2.imshow("Original", image)
        cv2.imshow("Thresh", thresh)

        if cv2.waitKey(1) & 0xFF is ord('q'):
            break


if __name__ == '__main__':
    main()
