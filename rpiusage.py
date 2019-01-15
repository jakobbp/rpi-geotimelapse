#!/usr/bin/env python

import time
from picamera import PiCamera
from timelapse import AbstractCameraProxy
from timelapse import TimeLapse


class RPiCameraProxy(AbstractCameraProxy):
    def __init__(self):
        AbstractCameraProxy.__init__(self, "Python PiCamera")
        self.camera = None

    def init_camera(self, resolution):
        self.camera = PiCamera()
        self.camera.resolution = resolution
        self.camera.start_preview()
        time.sleep(2)

    def take_picture(self, image_name):
        self.camera.capture(image_name)

    def close_camera(self):
        self.camera.stop_preview()
        self.camera.close()


def main():
    camera_proxy = RPiCameraProxy()
    timelapse = TimeLapse(camera_proxy)
    timelapse.auto_record_and_upload()


if __name__ == '__main__':
    main()
