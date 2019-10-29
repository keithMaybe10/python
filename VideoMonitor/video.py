# -*- coding:utf-8 -*-

import os
import cv2
from datetime import datetime
from camera import Camera
import platform
import sys

class CameraVideo(Camera):
    def __init__(self, videoPath):
        super.__init__()
        self.videoPath = videoPath
        self.fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.videoName = datetime.now().strftime('%Y%m%d_%H%M%S') + '.avi'
        self.videoNameList = []
        self.writer = cv2.VideoWriter(os.path.join(videoPath,self.videoName), self.fourcc,
                    Camera.cameraFPS(), Camera.cameraSize())

    def updateVideoNameList(self, videoName):
        self.videoNameList.append(videoName)

    def createNewVideoFile(self):
        videoName = datetime.now().strftime('%Y%m%d_%H%M%S') + '.avi'
        self.updateVideoNameList(videoName)
        self.writer = cv2.VideoWriter(os.path.join(self.videoPath, videoName), self.fourcc,
                    Camera.cameraFPS(), Camera.cameraSize())


    def deleteVideo(self, videoPath, videoNameList):
        """
        If disk is lack of sapce or save more than 7 days video, it will delete the earliest file.

        """
        if not len(videoNameList):
            print('Has no video, and check disk space failed!\n')
            try:
                sys.exit()
            except:
                print('Please check your disk space, program exit...')
            
        if os.path.exists(os.path.join(videoPath, videoName)):
            try:
                os.remove(os.path.join(videoPath, videoName))
            except:
                print('Delete video %s failed' % videoName)

    def checkDiskSpace(self):
        """
        This function will check diskspace when write video.
        """

        diskSpcaceValue = 0
        if platform.system() == 'Windows':
            free_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(
                self.videoPath), None, None, ctypes.pointer(free_bytes))
            diskSpcaceValue = free_bytes.value/1024/1024/1024
        else:
            vfs = os.statvfs(self.videoPath)
            diskSpcaceValue = vfs[statvfs.F_BAVAIL] * \
                vfs[statvfs.F_BSIZE]/(1024 * 1024 * 1024)

        if diskSpcaceValue < 10:
            t = threading.Thread(target=self.deleteVideo(), args=(self.videoPath, self.videoNameList))
            t.start()

    def isTheSameDay(self):
        """
        if the current time is the same day as the video file craete
        """
        if len(self.videoNameList):
            videoFileCreateTime = self.videoNameList[-1].splite('.')[0]
            videoFileCreateDay = datetime.strptime(videoFileCreateTime, '%Y%m%d_%H%M%S').day
            currentDay = datetime.now().day
            if currentDay is not videoFileCreateDay:
                self.createNewVideoFile()

    def writeVideo(self):
        self.updateVideoNameList(self.videoName)
        self.checkDiskSpace()