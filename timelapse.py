import abc
import json
import math
import datetime
import time
import os

SETTINGS_FILE_PATH = 'settings.json'
LOG_FILE_PATH = "auto_record.log"
REPORT_TEMPLATE_FILE_PATH = "report_template.json"

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
KEY_REPORT_FILE_PATH = "reportFile"
KEY_DEVICE = "device"

ECLIPTIC_INCLINATION = 28127./216000.*math.pi
ECLIPTIC_FACTOR = math.tan(ECLIPTIC_INCLINATION)

ISO_DATE_FORMAT = "%Y-%m-%d"
ISO_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class TimeLapse:
    def __init__(self, camera_proxy):
        self.settings = None
        self.camera_proxy = camera_proxy
        self.running = False
        self.log = open(LOG_FILE_PATH, "w")

    def init_camera_proxy(self):
        self.log_message("Initializing camera proxy {}"+self.camera_proxy.implementation_type)
        width = int(self.get_settings()[KEY_WIDTH])
        height = int(self.get_settings()[KEY_HEIGHT])
        self.log_message("Setting resolution to {}x{}".format(width, height))
        self.camera_proxy.init_camera((width, height))
        self.log_message("Camera initialized")

    def get_settings(self):
        if self.settings is None:
            with open(SETTINGS_FILE_PATH) as settingsFile:
                self.settings = json.load(settingsFile)
        return self.settings

    def take_picture(self, imgName):
        self.camera_proxy.take_picture(imgName)
        self.log_message("Created image {}".format(imgName))

    def auto_record_and_upload(self):
        self.auto_record()
        self.create_video()
        self.upload_video()

    def auto_record(self):
        self.running = True
        self.init_camera_proxy()
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
        self.camera_proxy.close_camera()
        self.create_report(latitude, longitude, recordStart, recordEnd, timeScale, imgIndex)

    def create_report(self, latitude, longitude, startTime, endTime, timeScale, nImages):
        reportFilePath = self.get_settings()[KEY_REPORT_FILE_PATH]
        self.log_message("Creating report file {}".format(reportFilePath))
        reportFile = open(reportFilePath, "w")
        with open(REPORT_TEMPLATE_FILE_PATH) as templateFile:
            reportTemplate = json.load(templateFile)
        for i in xrange(len(reportTemplate)):
            reportDataKey = reportTemplate[str(i+1)]
            print reportDataKey
            print reportDataKey == "date"
            if reportDataKey == "date":
                print >>reportFile, "Date: {}".format(time.strftime(ISO_DATE_FORMAT, time.gmtime(startTime)))
            elif reportDataKey == "start":
                print >>reportFile, "Start: {} UTC".format(time.strftime(ISO_TIME_FORMAT, time.gmtime(startTime)))
            elif reportDataKey == "end":
                print >>reportFile, "End: {} UTC".format(time.strftime(ISO_TIME_FORMAT, time.gmtime(endTime)))
            elif reportDataKey == "exactCoordinates":
                print >>reportFile, "Coordinates: {}N, {}E".format(latitude, longitude)
            elif reportDataKey == "approxCoordinates":
                print >>reportFile, "Coordinates: {:.1f}N, {:.1f}E".format(latitude, longitude)
            elif reportDataKey == "timeScale":
                print >>reportFile, "Time scale: 1:{}".format(timeScale)
            elif reportDataKey == "device":
                print >>reportFile, "Recorded with: {}".format(self.get_settings()[KEY_DEVICE])
            elif reportDataKey == "nImages":
                print >>reportFile, "Number of images taken: {}".format(nImages)
        reportFile.close()

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

        if latitude < 90:
            aCosArg = -math.sin(equinoxOffset/356.*2.*math.pi)*math.tan(math.radians(latitude))*ECLIPTIC_FACTOR
            if aCosArg > 1:
                return (12+middayOffset, 12+middayOffset)
            elif aCosArg < -1:
                return (0, 24)
            else:
                dayLength = 24*math.acos(aCosArg)/math.pi
                dayStart = 12+middayOffset-dayLength/2
                dayEnd = dayStart+dayLength
                return (dayStart, dayEnd)
        else:
            if math.sin(equinoxOffset/365.*2.*math.pi)*latitude > 0:
                return (12 + middayOffset, 12 + middayOffset)
            else:
                return (0, 24)


class AbstractCameraProxy():
    __metaclass__ = abc.ABCMeta

    def __init__(self, implementation_type):
        self.implementation_type = implementation_type

    @abc.abstractmethod
    def take_picture(self, imgName):
        pass

    @abc.abstractmethod
    def init_camera(self, resolution):
        pass

    @abc.abstractmethod
    def close_camera(self):
        pass
