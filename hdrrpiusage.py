#!/usr/bin/env python

import cv2
import time
import numpy
from fractions import Fraction
from picamera import PiCamera
from timelapse import AbstractCameraProxy
from timelapse import TimeLapse


KEY_EXPOSURE_LOWEST = 'lowest'
KEY_EXPOSURE_LOW = 'low'
KEY_EXPOSURE_MEDIUM = 'medium'
KEY_EXPOSURE_HIGH = 'high'
KEY_EXPOSURE_HIGHEST = 'highest'
SHUTTER_SPEEDS = {
    KEY_EXPOSURE_LOWEST: Fraction(1, 2),
    KEY_EXPOSURE_LOW: Fraction(1, 1),
    KEY_EXPOSURE_MEDIUM: Fraction(5, 1),
    KEY_EXPOSURE_HIGH: Fraction(10, 1),
    KEY_EXPOSURE_HIGHEST: Fraction(15, 1)
}
AWB_GAINS = {
    KEY_EXPOSURE_LOWEST: (Fraction(1, 1), Fraction(1, 1)),
    KEY_EXPOSURE_LOW: (Fraction(1, 1), Fraction(1, 1)),
    KEY_EXPOSURE_MEDIUM: (Fraction(2, 2), Fraction(2, 2)),
    KEY_EXPOSURE_HIGH: (Fraction(3, 3), Fraction(3, 3)),
    KEY_EXPOSURE_HIGHEST: (Fraction(1, 1), Fraction(1, 1))
}
GPU_COMPATIBLE_RESOLUTION = (2592, 1944)
BRIGHTNESS_THRESHOLD_EXPOSURE_SPEED = 60000


class HDRRPiCameraProxy(AbstractCameraProxy):
    def __init__(self):
        AbstractCameraProxy.__init__(self, "Python PiCamera with CV2 HDR postprocessing")
        self.camera = None
        self.resolution = None

    def init_camera(self, resolution):
        self.camera = PiCamera()
        self.resolution = resolution
        self.camera.resolution = GPU_COMPATIBLE_RESOLUTION
        self.camera.exposure_mode = 'off'
        self.camera.awb_mode = 'off'

    def take_picture(self, image_name):
        too_bright = self.check_brightness()
        images = []
        if not too_bright:
            images.append(self.capture_picture_with_exposure(KEY_EXPOSURE_LOWEST))
            images.append(self.capture_picture_with_exposure(KEY_EXPOSURE_LOW))
        images.append(self.capture_picture_with_exposure(KEY_EXPOSURE_MEDIUM))
        images.append(self.capture_picture_with_exposure(KEY_EXPOSURE_HIGH))
        images.append(self.capture_picture_with_exposure(KEY_EXPOSURE_HIGHEST))
        hdr_image = HDRRPiCameraProxy.create_hdr_image(images)
        scaled_image = self.scale_and_crop_image(hdr_image)
        cv2.imwrite(image_name, scaled_image)

    def close_camera(self):
        self.camera.stop_preview()
        self.camera.close()

    def check_brightness(self):
        self.camera.shutter_speed = 0
        self.camera.exposure_mode = 'auto'
        self.camera.awb_mode = 'auto'
        time.sleep(2)
        exposure_speed = self.camera.exposure_speed
        self.camera.exposure_mode = 'off'
        self.camera.awb_mode = 'off'
        return exposure_speed < BRIGHTNESS_THRESHOLD_EXPOSURE_SPEED

    def capture_picture_with_exposure(self, exposure_key):
        self.set_exposure_settings(exposure_key)
        resolution = self.camera.resolution
        image = numpy.empty((resolution[0] * resolution[1] * 3), dtype=numpy.uint8)
        self.camera.capture(image, format='bgr', use_video_port=False)
        return image.reshape((resolution[1], resolution[0], 3))

    def set_exposure_settings(self, exposure_key):
        self.camera.shutter_speed = SHUTTER_SPEEDS[exposure_key]
        self.camera.awb_gains = AWB_GAINS[exposure_key]

    def scale_and_crop_image(self, image):
        if self.resolution is None:
            return image.copy()

        r_width = self.resolution[0]
        r_height = self.resolution[1]
        i_height, i_width, channels = image.shape

        if r_width == i_width and r_height == i_height:
            return image.copy()

        if r_width < i_width and r_height < i_height:
            r_aspect = float(r_width)/float(r_height)
            i_aspect = float(i_width)/float(i_height)
            if r_aspect < i_aspect:
                scaled_width = r_width
                scaled_height = int(r_width/i_aspect + 0.5)
                w_diff = 0
                h_diff = scaled_height - r_height
            else:
                scaled_width = int(r_height*i_aspect + 0.5)
                scaled_height = r_height
                w_diff = scaled_width - r_width
                h_diff = 0
            resized_image = cv2.resize(image, (int(scaled_width + 0.5), int(scaled_height + 0.5)))
            cropped_image = resized_image[w_diff/2:r_width, h_diff/2:r_height]
            return cropped_image

        return image.copy()

    @staticmethod
    def create_hdr_image(images):
        merge_mertens = cv2.createMergeMertens()
        return merge_mertens.process(images)


def main():
    camera_proxy = HDRRPiCameraProxy()
    timelapse = TimeLapse(camera_proxy)
    timelapse.auto_record_and_upload()


if __name__ == '__main__':
    main()
