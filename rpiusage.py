#!/usr/bin/env python

import time
from picamera import PiCamera
from timelapse import *


class RPiCameraProxy(AbstractCameraProxy):
    def __init__(self):
        AbstractCameraProxy.__init__(self, "Python PiCamera")
        self.camera = None

    def init_camera(self, resolution):
        self.camera = PiCamera()
        self.camera.resolution = resolution
        self.camera.start_preview()
        time.sleep(2)

    def take_picture(self, imgName):
        self.camera.capture(imgName)

    def close_camera(self):
        pass


def main():
    cameraProxy = RPiCameraProxy()
    timelapse = TimeLapse(cameraProxy)
    timelapse.auto_record_and_upload()


if __name__ == '__main__':
    main()
