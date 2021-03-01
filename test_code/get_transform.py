import numpy as np
import cv2

tl = [200, 80]
tr = [1004, 95]
bl = [199, 646]
br = [990, 662]

rect = np.array([tl, tr, br, bl], dtype='float32')

# widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
# widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
# maxWidth = max(int(widthA), int(widthB))
# # compute the height of the new image, which will be the
# # maximum distance between the top-right and bottom-right
# # y-coordinates or the top-left and bottom-left y-coordinates
# heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
# heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
# maxHeight = max(int(heightA), int(heightB))
# # now that we have the dimensions of the new image, construct
# # the set of destination points to obtain a "birds eye view",
# # (i.e. top-down view) of the image, again specifying points
# # in the top-left, top-right, bottom-right, and bottom-left
# # order
dst = np.array([
    [0, 0],
    [500 - 1, 0],
    [500 - 1, 353 - 1],
    [0, 353 - 1]], dtype = "float32")

M = cv2.getPerspectiveTransform(rect, dst)

# map_x = np.zeros((720, 1280), dtype='float64')
# max_y = np.zeros((720, 1280), dtype='float64')

# for y in range(720):
#     for x in range(1280):
#         w = M[2,0]*x + M[2,1] * y + M[2,2]
#         w = 1. / w if w != 0. else 0.

#         new_x = (M[0,0]*x + M[0,1]*y + M[0,2]) * w
#         new_y = (M[1,0]*x + M[1,1]*y + M[1,2]) * w

#         map_x[y, x] = new_x
#         map_y[y, x] = new_y

# print(map_x.tobytes())
# print(map_y.tobytes())

np.set_printoptions(suppress=True)
np.set_printoptions(precision=20)
print(', '.join(hex(i) for i in M.tobytes()))
print(M.dtype)