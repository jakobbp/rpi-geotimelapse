#!/usr/bin/env python

import cv2
import time
import numpy
from fractions import Fraction
from picamera import PiCamera
from timelapse import AbstractCameraProxy
from timelapse import TimeLapse


KEY_EXPOSURE_LOW = "low"
KEY_EXPOSURE_MEDIUM = "medium"
KEY_EXPOSURE_HIGH = "high"
SHUTTER_SPEEDS = {
    KEY_EXPOSURE_LOW: Fraction(1, 10),
    KEY_EXPOSURE_MEDIUM: Fraction(5, 1),
    KEY_EXPOSURE_HIGH: Fraction(15, 1)
}
AWB_GAINS = {
    KEY_EXPOSURE_LOW: (Fraction(1, 1), Fraction(1, 1)),
    KEY_EXPOSURE_MEDIUM: (Fraction(2, 2), Fraction(2, 2)),
    KEY_EXPOSURE_HIGH: (Fraction(3, 3), Fraction(3, 3))
}


class HDRRPiCameraProxy(AbstractCameraProxy):
    def __init__(self):
        AbstractCameraProxy.__init__(self, "Python PiCamera with CV2 HDR postprocessing")
        self.camera = None

    def init_camera(self, resolution):
        self.camera = PiCamera()
        self.camera.resolution = resolution
        self.camera.exposure_mode = 'off'
        self.camera.awb_mode = 'off'

    def take_picture(self, image_name):
        image_low = self.capture_picture_with_exposure(KEY_EXPOSURE_LOW)
        image_medium = self.capture_picture_with_exposure(KEY_EXPOSURE_MEDIUM)
        image_high = self.capture_picture_with_exposure(KEY_EXPOSURE_HIGH)
        self.create_hdr_image(image_name, [image_low, image_medium, image_high])

    def close_camera(self):
        self.camera.stop_preview()
        self.camera.close()

    def capture_picture_with_exposure(self, exposure_key):
        self.set_exposure_settings(exposure_key)
        resolution = self.camera.resolution
        image = numpy.empty((resolution[0] * resolution[1] * 3), dtype=numpy.uint8)
        self.camera.capture(image, 'bgr')
        return image.reshape((resolution[1], resolution[0], 3))

    def set_exposure_settings(self, exposure_key):
        self.camera.shutter_speed = SHUTTER_SPEEDS[exposure_key]
        self.camera.awb_gains = AWB_GAINS[exposure_key]

    def create_hdr_image(self, image_name, images):
        merge_mertens = cv2.createMergeMertens()
        hdr_image = merge_mertens.process(images)
        cv2.imwrite(image_name, hdr_image)


def main():
    camera_proxy = HDRRPiCameraProxy()
    timelapse = TimeLapse(camera_proxy)
    timelapse.auto_record_and_upload()


if __name__ == '__main__':
    main()
