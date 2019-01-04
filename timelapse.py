import json
import math
import datetime
from picamera import PiCamera
from time import sleep

SETTINGS_FILE_PATH = 'settings.json'
KEY_WIDTH = 'width'
KEY_HEIGHT = 'height'
KEY_LATITUDE = 'latitude'
KEY_LONGITUDE = 'longitude'
KEY_IMAGE_TEMPLATE= 'imageTemplate'

ECLIPTIC_INCLINATION = 28127./216000.*math.pi
ECLIPTIC_FACTOR = math.tan(ECLIPTIC_INCLINATION)


class TimeLapse:
    def __init__(self):
        self.settings = None
        self.camera = None
        self.running = False

    def init_camera(self):
        self.camera = PiCamera()
        self.camera.resolution = (int(self.get_settings()[KEY_WIDTH]), int(self.get_settings()[KEY_HEIGHT]))
        self.camera.start_preview()
        sleep(2)

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
        pass

    @staticmethod
    def get_day_limits(latitude, longitude):
        currentDate = datetime.datetime.now()
        springEquinox = datetime.datetime(currentDate.year, 3, 20)
        equinoxOffset = (currentDate-springEquinox).days
        dayLength = 12
        if latitude < 90:
            aCosArg = -math.sin(equinoxOffset/356*2*math.pi)*math.tan(math.radians(latitude))*ECLIPTIC_FACTOR
            if aCosArg > 1:
                print "1"
                dayLength = 0
            elif aCosArg < -1:
                print "2"
                dayLength = 24
            else:
                print "3"
                dayLength = 24*math.acos(aCosArg)/math.pi
                print aCosArg
                print dayLength
        else:
            if math.sin(equinoxOffset/365.*2*math.pi)*latitude > 0:
                print "4"
                dayLength = 0
            else:
                print "5"
                dayLength = 24

        middayOffset = 0
        print dayLength
        dayStart = (36+middayOffset-dayLength/2)%24
        dayEnd = dayStart+dayLength
        return (dayStart, dayEnd)


print TimeLapse.get_day_limits(45, 15)