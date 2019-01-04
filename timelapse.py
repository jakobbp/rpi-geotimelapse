import json
import math
import datetime
import time
import os
from picamera import PiCamera

SETTINGS_FILE_PATH = 'settings.json'
KEY_WIDTH = 'width'
KEY_HEIGHT = 'height'
KEY_FRAME_RATE = 'frameRate'
KEY_TIME_SCALE = 'timeScale'
KEY_LATITUDE = 'latitude'
KEY_LONGITUDE = 'longitude'
KEY_IMAGE_TEMPLATE = 'imageTemplate'
KEY_LOG_FORMAT = "logFormat"

ECLIPTIC_INCLINATION = 28127./216000.*math.pi
ECLIPTIC_FACTOR = math.tan(ECLIPTIC_INCLINATION)


class TimeLapse:
    def __init__(self):
        self.settings = None
        self.camera = None
        self.running = False

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

    def take_picture(self, img_name):
        self.get_camera().capture(img_name)

    def auto_record(self):
        self.running = True
        latitude = float(self.get_settings()[KEY_LATITUDE])
        longitude = float(self.get_settings()[KEY_LONGITUDE])
        curentTime = datetime.datetime.now()
        dayLimits = TimeLapse.get_day_limits(latitude, longitude)
        midnightTime = datetime.datetime(curentTime.year, curentTime.month, curentTime.day, 0, 0, 0, 0)
        midnight = time.mktime(midnightTime.timetuple())
        dayStart = midnight + 3600*dayLimits[0]
        dayEnd = midnight + 3600*dayLimits[1]
        self.log_message("Starting auto-daylight recording from {} to {}".format(dayStart, dayEnd))

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
        if initTime < dayStart:
            delay = dayStart - initTime
            self.log_message("Delaying start for {} seconds until dawn".format(delay))
            time.sleep(delay)

        self.log_message("Starting")
        imgIndex = 1
        startTime = time.time()
        while self.running:
            imgName = imgTemplate % imgIndex
            self.take_picture(imgName)
            self.log_message("Created image {}".format(imgName))
            if time.time() < dayEnd:
                imgIndex += 1
                time.sleep(framePeriod - ((time.time() - startTime) % framePeriod))
            else:
                self.running = False
                self.log_message("Ending")

    def log_message(self, message):
        print (self.get_settings()[KEY_LOG_FORMAT]).format(time=datetime.datetime.now(), message=message)

    @staticmethod
    def get_day_limits(latitude, longitude):
        currentDate = datetime.datetime.now()
        springEquinox = datetime.datetime(currentDate.year, 3, 20)
        equinoxOffset = (currentDate-springEquinox).days
        dayLength = 12
        if latitude < 90:
            aCosArg = -math.sin(equinoxOffset/356.*2.*math.pi)*math.tan(math.radians(latitude))*ECLIPTIC_FACTOR
            if aCosArg > 1:
                dayLength = 0
            elif aCosArg < -1:
                dayLength = 24
            else:
                dayLength = 24*math.acos(aCosArg)/math.pi
        else:
            if math.sin(equinoxOffset/365.*2.*math.pi)*latitude > 0:
                dayLength = 0
            else:
                dayLength = 24

        longitudinalOffset = longitude/15.
        timezoneOffset = time.localtime().tm_hour - time.gmtime().tm_hour
        middayOffset = timezoneOffset - longitudinalOffset
        dayStart = (36+middayOffset-dayLength/2.) % 24
        dayEnd = dayStart+dayLength
        return (dayStart, dayEnd)


def main():
    timelapse = TimeLapse()
    timelapse.init_camera()
    timelapse.auto_record()


if __name__ == '__main__':
    main()
