# -*- coding: utf-8 -*-

import cv2

class Camera(object):
    # capture = cv2.VideoCapture(0)
    def __init__(self):
        self.capture = cv2.VideoCapture(0)

    def openCamera(self):
        """
        Open camera and return status and image that read from camera
        """
        try:
            ret, frame = self.capture.read()
            return ret, frame
        except:
            print('camera open failed!, please check connection or camera driver...')
            return False, False

    def cameraFPS(self):
        """
        Return camera fps.
        """
        return int(self.capture.get(cv2.CAP_PROP_FPS))

    def cameraSize(self):
        """
        Return camera size, width and height
        """
        return int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH)), int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
