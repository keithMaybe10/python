# -*- coding:utf-8 -*-

import os
import cv2
from datetime import datetime
from camera import Camera
import platform
import sys
import ctypes
import threading

class CameraVideo(Camera):
    def __init__(self, videoPath):
        """
        initial some parameter
        """
        super().__init__()
        self.videoPath = self.__initVideoSaveDir(videoPath)
        self.fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.videoName = datetime.now().strftime('%Y%m%d_%H%M%S') + '.avi'
        self.videoNameList = []
        self.writer = cv2.VideoWriter(os.path.join(self.videoPath,self.videoName), self.fourcc,
                    self.cameraFPS(), (self.cameraWidth(), self.cameraHeight()))
        self.__createNewVideoFile()

    def __initVideoSaveDir(self, videoPath):
        """
        init dir where video will save
        """
        videoPath = os.path.join(videoPath, 'video')
        if not os.path.exists(videoPath):
            os.mkdir(videoPath)
        return videoPath

    def __updateVideoNameList(self, videoFileName):
        """
        update video list when create new video file
        """

        self.videoNameList.append(videoFileName)

    def __createNewVideoFile(self):
        """
        create new video file and add video file name to the list
        """
        videoFileName = datetime.now().strftime('%Y%m%d_%H%M%S') + '.avi'
        self.__updateVideoNameList(videoFileName)
        self.writer = cv2.VideoWriter(os.path.join(self.videoPath, videoFileName), self.fourcc,
            self.cameraFPS(), (self.cameraWidth(), self.cameraHeight()))


    def __deleteVideo(self, videoPath, videoNameList):
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

    def __checkDiskSpace(self):
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
            t = threading.Thread(target=self.__deleteVideo, args = (self.videoPath, self.videoNameList))
            t.start()

    def __isTheSameDay(self):
        """
        if the current time is the same day as the video file craete
        """
        if len(self.videoNameList):
            videoFileCreateTime = self.videoNameList[0].split('.')[0]
            videoFileCreateDay = datetime.strptime(videoFileCreateTime, '%Y%m%d_%H%M%S').day
            currentDay = datetime.now().day
            if currentDay is not videoFileCreateDay:
                self.createNewVideoFile()
    
    def __isMoreThan7Day(self):
        """
        If video save more than 7 based on date, then delete the earliest videofile
        """
        earliestVideoName = self.videoNameList[0].split('0')[0]
        earliestVideoDate = datetime.strptime(earliestVideoName, '%Y%m%d_%H%M%S')
        if (datetime.now() - earliestVideoDate).days > 7:
            t = threading.Thread(target=self.__deleteVideo, args=(self.videoPath, self.videoNameList[0]))
            t.start()
            self.__createNewVideoFile()


    def writeVideo(self, frame):
        """
        save video
        """
        # self.updateVideoNameList(self.videoName)
        self.__checkDiskSpace()
        self.__isTheSameDay()
        self.__isMoreThan7Day()
        self.writer.write(frame)
        cv2.waitKey(30)
