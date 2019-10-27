# -*- coding: utf-8 -*-

import sys
import cv2
import os
import ctypes
import platform
import numpy as np
from datetime import datetime
import time
import threading
import camera

def deleteVideo(videoPath, videoList):
    """
    If disk is lack of sapce or save more than 7 days video, it will delete the earliest file.

    """
    videoName = videoList[0]
    if os.path.exists(os.path.join(videoPath, videoName)):
        try:
            os.remove(os.path.join(videoPath, videoName))
        except:
            print('Delete video %s failed!' % videoName)

    videoList.pop([0])  # update videoList


def diskCheck(videoPath, videoList):
    """
    This function will check diskspace when write video.
    """

    diskSpcaceValue = 0
    if platform.system() == 'Windows':
        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(
            videoPath), None, None, ctypes.pointer(free_bytes))
        diskSpcaceValue = free_bytes.value/1024/1024/1024
    else:
        vfs = os.statvfs(videoPath)
        diskSpcaceValue = vfs[statvfs.F_BAVAIL] * \
            vfs[statvfs.F_BSIZE]/(1024 * 1024 * 1024)

    if diskSpcaceValue < 10:
        t = threading.Thread(target=deleteVideo, args=(videoPath, videoList))
        t.start()
        return True
    else:
        return False


def videoFileDetect(startTime, videoPath, videoList):
    """
    Check if the current time is the same day as the video file create.
    """
    currentTime = datetime.now()
    if currentTime.day != startTime.day:
        return True
    elif (currentTime - startTime).days > 7:
        deleteVideo(videoPath, videoList)
        return True
    else:
        return False


def saveVideo(video, frame):
    cv2.waitKey(30)
    video.write(frame)


def faceDetect(frame, faceROIPath):
    """detect face in the video

    This function will detect face based haarcascade_frontalface_default.xml

    """
    faceDetector = cv2.CascadeClassifier(
        'D:\Python3\install\Lib\site-packages\cv2\data\haarcascade_frontalface_default.xml')
    frameGray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = faceDetector.detectMultiScale(frameGray, 1.3, 5)
    for face in faces:
        x, y, w, h = face
        cv2.rectangle(frame, (x, y), (x + h, y + w), (0, 255, 0), 2)
        if True:
            faceROI = frame[y:(y+w), x:(x+h)]
            faceName = datetime.now().strftime('%Y%m%d_%H%M%S') + '.png'
            cv2.imwrite(os.path.join(faceROIPath, faceName), faceROI)


def displayVideo(frame, faceROIPath, width, height, fps):
    """Display the video
    
    This function will create a window based on width and height.
    At the same time, it will show video capture time on the top of the window.
    It also will detect people face in the vido.

    Args:
        frame: camer video
        faceROIPath: if detect a face in the video, where to save the face
        width,heigh, fps: video size and fp

    """
    cv2.namedWindow('Home Monitor', cv2.WINDOW_AUTOSIZE)
    localTime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    textstr = str(localTime + ' fps: ' + str(fps))
    cv2.putText(frame, textstr, (15, 30), cv2.FONT_HERSHEY_PLAIN,
                1.0, (255, 255, 255), 1, 8, False)
    faceDetect(frame, faceROIPath)
    cv2.imshow('Home Monitor', frame)
    if cv2.waitKey(5) == ord('q'):
        try:
            sys.exit()
        except:
            print('video monitor closed!')

def monitorRun(filePath):
    if not os.path.exists(filePath):
        os.mkdir(filePath)
    # get video and face path
    videoPath = os.path.join(filePath, 'video')
    if not os.path.exists(videoPath):
        os.mkdir(videoPath)

    faceROIPath = os.path.join(filePath, 'faces')
    if not os.path.exists(faceROIPath):
        os.mkdir(faceROIPath)

    videoNameList = []
    videoCamera = camera.Camera()
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    fps = videoCamera.cameraFPS()
    width, height = videoCamera.cameraSize()

    #save video file named on video create time
    videoName = datetime.now().strftime('%Y%m%d_%H%M%S') + '.avi'
    videoNameList.append(videoName)
    # startTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    startTime = datetime.now()
    video = cv2.VideoWriter(os.path.join(
        videoPath, videoName), fourcc, fps, (width, height))

    try:
        while(True):
            ret, frame = videoCamera.openCamera()
            if ret:
                displayVideo(frame, faceROIPath, width, height, fps)
                diskSpaceFreeFlag = diskCheck(videoPath, videoNameList)
                videoFileFlag = videoFileDetect(startTime, videoPath, videoNameList)
                if diskSpaceFreeFlag or videoFileFlag:
                    # create a new video file
                    videoName = datetime.now().strftime('%Y%m%d_%H%M%S') + '.avi'
                    videoNameList.append(videoName)
                    video = cv2.VideoWriter(os.path.join(videoPath, videoName), fourcc, fps, (width, height))
                saveVideo(video, frame)
    except KeyboardInterrupt:
        print('video monitor closed!')


if __name__ == '__main__':
    filePath='F:\\HomeMonitor'
    monitorRun(filePath)
