#!/usr/bin/env python

import json
import math
import datetime
import time
import os
from picamera import PiCamera

SETTINGS_FILE_PATH = 'settings.json'
LOG_FILE_PATH = "auto_record.log"
KEY_WIDTH = 'width'
KEY_HEIGHT = 'height'
KEY_FRAME_RATE = 'frameRate'
KEY_TIME_SCALE = 'timeScale'
KEY_LATITUDE = 'latitude'
KEY_LONGITUDE = 'longitude'
KEY_DAWN_BUFFER = 'dawnBufferMinutes'
KEY_DUSK_BUFFER = 'duskBufferMinutes'
KEY_IMAGE_TEMPLATE = 'imageTemplate'
KEY_LOG_FORMAT = "logFormat"
KEY_CREATE_VIDEO_COMMAND = "createVideoCommand"
KEY_UPLOAD_VIDEO_COMMAND = "uploadVideoCommand"

ECLIPTIC_INCLINATION = 28127./216000.*math.pi
ECLIPTIC_FACTOR = math.tan(ECLIPTIC_INCLINATION)


class TimeLapse:
    def __init__(self):
        self.settings = None
        self.camera = None
        self.running = False
        self.log = open(LOG_FILE_PATH, "w")

    def init_camera(self):
        self.log_message("Initializing PiCamera")
        self.camera = PiCamera()
        width = int(self.get_settings()[KEY_WIDTH])
        height = int(self.get_settings()[KEY_HEIGHT])
        self.camera.resolution = (width, height)
        self.log_message("Resolution set to {}x{}".format(width, height))
        self.camera.start_preview()
        time.sleep(2)
        self.log_message("Camera initialized")

    def get_camera(self):
        if self.camera is None:
            self.init_camera()
        return self.camera

    def get_settings(self):
        if self.settings is None:
            with open(SETTINGS_FILE_PATH) as settingsFile:
                self.settings = json.load(settingsFile)
        return self.settings

    def take_picture(self, imgName):
        self.get_camera().capture(imgName)
        self.log_message("Created image {}".format(imgName))

    def auto_record_and_upload(self):
        self.auto_record()
        self.create_video()
        self.upload_video()

    def auto_record(self):
        self.running = True
        latitude = float(self.get_settings()[KEY_LATITUDE])
        longitude = float(self.get_settings()[KEY_LONGITUDE])
        dawnBuffer = float(self.get_settings()[KEY_DAWN_BUFFER])
        duskBuffer = float(self.get_settings()[KEY_DUSK_BUFFER])
        curentTime = datetime.datetime.now()
        dayLimits = TimeLapse.get_day_limits(latitude, longitude)
        recordStartHour = dayLimits[0]-dawnBuffer/60
        recordEndHour = dayLimits[1]+duskBuffer/60
        midnightTime = datetime.datetime(curentTime.year, curentTime.month, curentTime.day, 0, 0, 0, 0)
        midnight = time.mktime(midnightTime.timetuple())
        recordStart = midnight + 3600*recordStartHour
        recordEnd = midnight + 3600*recordEndHour
        self.log_message("Starting auto-daylight recording from {} to {}".format(recordStartHour, recordEndHour))

        frameRate = float(self.get_settings()[KEY_FRAME_RATE])
        timeScale = float(self.get_settings()[KEY_TIME_SCALE])
        framePeriod = timeScale * 1./frameRate
        self.log_message("Recording every {} seconds for framerate {} at 1:{} timescale".format(framePeriod, frameRate, timeScale))

        imgTemplate = self.get_settings()[KEY_IMAGE_TEMPLATE]
        testFile = imgTemplate % 0
        outputDir = os.path.dirname(testFile)
        if not os.path.exists(outputDir):
            os.makedirs(outputDir)
            self.log_message("Created output directory: {}".format(outputDir))

        initTime = time.time()
        if initTime < recordStart or initTime > recordEnd:
            if initTime > recordEnd:
                recordStart += 86400
                recordEnd += 86400
            delay = recordStart - initTime
            self.log_message("Delaying start for {} seconds until dawn".format(delay))
            time.sleep(delay)

        self.log_message("Starting recording session")
        imgIndex = 1
        startTime = time.time()
        while self.running:
            imgName = imgTemplate % imgIndex
            self.take_picture(imgName)
            if time.time() < recordEnd:
                imgIndex += 1
                time.sleep(framePeriod - ((time.time() - startTime) % framePeriod))
            else:
                self.running = False
                self.log_message("Ending recording session")

    def create_video(self):
        createVideoCommand = self.get_settings()[KEY_CREATE_VIDEO_COMMAND]
        self.log_message("Creating video with command '{}'".format(createVideoCommand))
        os.system(createVideoCommand)

    def upload_video(self):
        uploadVideoCommand = self.get_settings()[KEY_UPLOAD_VIDEO_COMMAND]
        self.log_message("Uploading video with command '{}'".format(uploadVideoCommand))
        os.system(uploadVideoCommand)

    def log_message(self, message):
        logMessage = (self.get_settings()[KEY_LOG_FORMAT]).format(time=datetime.datetime.now(), message=message)
        print logMessage
        print >>self.log, logMessage
        self.log.flush()

    @staticmethod
    def get_day_limits(latitude, longitude):
        currentDate = datetime.datetime.now()
        springEquinox = datetime.datetime(currentDate.year, 3, 20)
        equinoxOffset = (currentDate-springEquinox).days

        longitudinalOffset = longitude/15.
        timezoneOffset = time.localtime().tm_hour - time.gmtime().tm_hour
        middayOffset = timezoneOffset - longitudinalOffset

        dayLength = 12
        if latitude < 90:
            aCosArg = -math.sin(equinoxOffset/356.*2.*math.pi)*math.tan(math.radians(latitude))*ECLIPTIC_FACTOR
            if aCosArg > 1:
                return (12+middayOffset, 12+middayOffset)
            elif aCosArg < -1:
                return (0, 24)
            else:
                dayLength = 24*math.acos(aCosArg)/math.pi
        else:
            if math.sin(equinoxOffset/365.*2.*math.pi)*latitude > 0:
                return (12 + middayOffset, 12 + middayOffset)
            else:
                return (0, 24)

        dayStart = 12+middayOffset-dayLength/2
        dayEnd = dayStart+dayLength
        return (dayStart, dayEnd)


def main():
    timelapse = TimeLapse()
    timelapse.init_camera()
    timelapse.auto_record_and_upload()


if __name__ == '__main__':
    main()
