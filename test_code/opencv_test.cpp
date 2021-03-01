#include <opencv2/opencv.hpp>
#include <zmq.hpp>
#include <iostream>
#include <string>

#include "zhelpers.hpp"

using namespace cv;
using namespace std;
using namespace zmq;

char warpBytes[72] = {0xc4, 0xcb, 0x57, 0x6f, 0x48, 0xdf, 0xe3, 0x3f, 0xde, 0x7a, 0xc, 0x7e, 0xec, 0xf9, 0x51, 0x3f, 0x47, 0x92, 0xe0, 0x47, 0x7f, 0x12, 0x5f, 0xc0, 0x9b, 0xd8, 0xfb, 0x10, 0x32, 0x57, 0x87, 0xbf, 0x36, 0x52, 0x39, 0xee, 0x39, 0x8c, 0xe3, 0x3f, 0xb0, 0x5a, 0xf3, 0x77, 0x86, 0x4b, 0x47, 0xc0, 0x5c, 0xbf, 0xd6, 0x6c, 0xef, 0xb1, 0xcb, 0x3e, 0xfb, 0xbe, 0x65, 0xb7, 0x7d, 0xd4, 0xfd, 0xbe, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0xf0, 0x3f};

int main (int argc, char** argv) {
    //Mat image = imread("ball_settings.png");
    context_t context(1);
    // socket_t socket(context, ZMQ_PUB);
    // socket.setsockopt(ZMQ_SNDHWM, 10);
    // socket.bind("ipc://camera");

    VideoCapture camera("nvarguscamerasrc wbmode=4 aelock=true gainrange=\"8 8\" ispdigitalgainrange=\"1 1\" exposuretimerange=\"5000000 5000000\" ! video/x-raw(memory:NVMM), width=(int)1280, height=(int)720, format=(string)NV12, framerate=(fraction)50/1 ! nvvidconv flip-method=2 ! video/x-raw, format=(string)BGRx ! videoconvert ! video/x-raw, format=(string)BGR ! appsink");

    if (!camera.isOpened()) {
        cout << "Error opening camera" << endl;
        return -1;
    }

    //namedWindow("camera test");
    namedWindow("before conversion");
    long long id = 0;

    Mat warpMat(3, 3, CV_64F, &warpBytes);
    Mat inverseWarpMat;
    invert(warpMat, inverseWarpMat);

    Mat map_x, map_y, srcTM;
    srcTM = inverseWarpMat.clone();

    map_x.create(Size(500, 353), CV_32FC1);
    map_y.create(Size(500, 353), CV_32FC1);

    double M11, M12, M13, M21, M22, M23, M31, M32, M33;
    M11 = srcTM.at<double>(0,0);
    M12 = srcTM.at<double>(0,1);
    M13 = srcTM.at<double>(0,2);
    M21 = srcTM.at<double>(1,0);
    M22 = srcTM.at<double>(1,1);
    M23 = srcTM.at<double>(1,2);
    M31 = srcTM.at<double>(2,0);
    M32 = srcTM.at<double>(2,1);
    M33 = srcTM.at<double>(2,2);

    for (int y = 0; y < 353; y++) {
        double fy = (double)y;
        for (int x = 0; x < 500; x++) {
            double fx = (double)x;
            double w = ((M31 * fx) + (M32 * fy) + M33);
            w = w != 0.0f ? 1.f / w : 0.0f;
            float new_x = (float)((M11 * fx) + (M12 * fy) + M13) * w;
            float new_y = (float)((M21 * fx) + (M22 * fy) + M23) * w;
            map_x.at<float>(y,x) = new_x;
            map_y.at<float>(y,x) = new_y;
        }
    }

    Mat trfm_x, trfm_y;

    trfm_x.create(Size(500, 353), CV_16SC2);
    trfm_y.create(Size(500, 353), CV_16UC1);
    convertMaps(map_x, map_y, trfm_x, trfm_y, false);

    while (true) {
        Mat frame;
        camera >> frame;

        if (frame.empty())
            break;
        
        //imshow("camera test", frame);

        Mat warped;
        //warpPerspective(frame, warped, inverseWarpMat, Size(500, 353), WARP_INVERSE_MAP | INTER_LINEAR);
        remap(frame, warped, trfm_x, trfm_y, INTER_LINEAR);

        // resize(frame, frame, Size(500, 353), 0, 0, INTER_LINEAR);

        imshow("before conversion", warped);

        GaussianBlur(frame, frame, Size(11, 11), 0);
        //imshow("before conversion", frame);
        cvtColor(frame, frame, COLOR_BGR2HSV);

        //imshow("camera test", frame);

        // message_t imageMsg(frame.data, frame.total() * frame.channels(), NULL, NULL);
        // socket.send(imageMsg, ZMQ_DONTWAIT | ZMQ_SNDMORE);

        // String s_id = to_string(id);
        // message_t idMsg(s_id.data(), s_id.length());
        // socket.send(idMsg, ZMQ_DONTWAIT);

        //cout << "Sent frame " << id << endl;
        
        // Mat thresh;
        // inRange(frame, Scalar(0, 0, 0), Scalar(255, 255, 255), thresh);
        // inRange(frame, Scalar(0, 0, 0), Scalar(255, 255, 255), thresh);
        // inRange(frame, Scalar(0, 0, 0), Scalar(255, 255, 255), thresh);

        //imshow("camera test", thresh);

        if (waitKey(1) >= 0)
            break;

        //id++;
    }

    destroyAllWindows();
    camera.release();

    return 0;
}
