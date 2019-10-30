# -*- coding: utf-8 -*-

import cv2
import camera
import os
import sys

class videoProcess():
    def __init__(self, filePath):
        self.facePath = os.path.join(filePath, 'faces')
        self.initFaceSaveDir()
        self.faceDetector = cv2.CascadeClassifier('/data/haarcascade_frontalface_default.xml')
        self.windowName = ('Video Monitor', cv2.WINDOW_AUTOSIZE)


    def initFaceSaveDir(self):
        """
        init dir where face image will save
        """
        if not os.path.exists(self.facePath):
            os.mkdir(self.facePath)

    def faceDetect(self):
        pass