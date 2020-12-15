import numpy as np
import cv2

def color_tracking(frame):
    # determine which pixels fall within the blue boundaries
    # and then blur the binary image
    global blueLower, blueUpper

    blue = cv2.inRange(frame, blueLower, blueUpper)
    blue = cv2.GaussianBlur(blue, (3, 3), 0)

    # find contours in the image
    cnts = cv2.findContours(blue.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    #cnts = cnts[1]
    cnts = imutils.grab_contours(cnts)

    # check to see if any contours were found
    if len(cnts) > 0:
        # sort the contours and find the largest one -- we
        # will assume this contour correspondes to the area
        # of my phone
        cnt = sorted(cnts, key = cv2.contourArea, reverse = True)[0]

        # compute the (rotated) bounding box around then
        # contour and then draw it		
        rect = np.int32(cv2.boxPoints(cv2.minAreaRect(cnt)))
        cv2.drawContours(frame, [rect], -1, (0, 255, 0), 2)

    # show the frame and the binary image
    #cv2.imshow("Tracking", frame)
    #cv2.imshow("Binary", blue)
    return frame

def rotate_bound(image, angle):
    # grab the dimensions of the image and then determine the
    # center
    (h, w) = image.shape[:2]
    (cX, cY) = (w // 2, h // 2)
    # grab the rotation matrix (applying the negative of the
    # angle to rotate clockwise), then grab the sine and cosine
    # (i.e., the rotation components of the matrix)
    M = cv2.getRotationMatrix2D((cX, cY), -angle, 1.0)
    cos = np.abs(M[0, 0])
    sin = np.abs(M[0, 1])
    # compute the new bounding dimensions of the image
    nW = int((h * sin) + (w * cos))
    nH = int((h * cos) + (w * sin))
    # adjust the rotation matrix to take into account translation
    M[0, 2] += (nW / 2) - cX
    M[1, 2] += (nH / 2) - cY
    # perform the actual rotation and return the image
    return cv2.warpAffine(image, M, (nW, nH))

def face_detection(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # find faces in the image
    fd = FaceDetector("cascades/haarcascade_frontalface_default.xml")
    faceRects = fd.detect(gray, scaleFactor = 1.1, minNeighbors = 5,minSize = (30, 30))
    # loop over the faces and draw a rectangle around each
    for (x, y, w, h) in faceRects:
	    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
    return frame

def resize(frame, scale_percent):
    width = int(frame.shape[1] * scale_percent / 100)
    height = int(frame.shape[0] * scale_percent / 100)
    dsize = (width,height)
    return cv2.resize(frame, dsize)

def resize_video(frame, width, height, scale_percent):
    dsize = (int(width), int(height))
    return cv2.resize(frame, dsize)
