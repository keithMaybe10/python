# -*- coding: utf-8 -*-

import cv2
from camera import Camera
import os
import sys
from datetime import datetime
import threading

class videoProcess(Camera):
    def __init__(self, filePath):
        super().__init__()
        self.facePath = self.__initFaceSaveDir(filePath)
        self.faceDetector = cv2.CascadeClassifier('./data/haarcascade_frontalface_default.xml')
        self.windowName = 'Video Monitor'
        cv2.namedWindow(self.windowName, cv2.WINDOW_AUTOSIZE)

    def __initFaceSaveDir(self, filePath):
        """
        init dir where face image will save
        """
        facePath = os.path.join(filePath, 'faces')
        if not os.path.exists(facePath):
            os.mkdir(facePath)
        return facePath

    def __display(self, frame):
        """
        frame display function
        """
        fps = self.cameraFPS()
        currentTime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        textStr = str(currentTime + ' fps: ' + str(fps))
        cv2.putText(frame, textStr, (15, 30), cv2.FONT_HERSHEY_PLAIN,
                    1.0, (255, 255, 255), 1, 8, False)
        cv2.imshow(self.windowName, frame)
        if cv2.waitKey(5) == ord('q'):
            try:
                sys.exit()
            except:
                print('video monitor closed')

    def __saveFaceROI(self, face, frame):
        """
        when frame has faces, then save the face
        """
        x, y, w, h = face
        faceROI = frame[y:(y+w), x:(x+h)]
        faceName = datetime.now().strftime('%Y%m%d_%H%M%S') + '.png'
        cv2.imwrite(os.path.join(self.facePath, faceName), faceROI)

    def faceDetect(self, frame):
        """
        Check disk space and is the same day before face detect
        """
        frameGray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.faceDetector.detectMultiScale(frameGray, 1.3, 5)
        for face in faces:
            x, y, w, h = face
            cv2.rectangle(frame, (x, y), (x + h, y + w), (0, 255, 0), 2)
            t = threading.Thread(target=self.__saveFaceROI, args=(face, frame))
            t.start()
        self.__display(frame)
        