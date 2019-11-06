# -*- coding: utf-8 -*-

import os
import threading
import camera
import video
import faceDetect

def monitorRun(filePath):
    """
    Major code, program will run until press ctrl+c to exit
    """
    videoCamera = camera.Camera()
    videoWriter = video.CameraVideo(filePath)
    faceDetector = faceDetect.videoProcess(filePath)

    try:
        while(True):
            ret, frame = videoCamera.openCamera()
            if ret:
                faceDetector.faceDetect(frame)
                t = threading.Thread(target = videoWriter.writeVideo, args = (frame))
    except KeyboardInterrupt:
        print('video monitor closed!')


if __name__ == '__main__':
    filePath='F:\\HomeMonitor'
    monitorRun(filePath)
