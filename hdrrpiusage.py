#!/usr/bin/env python

import cv2
import time
import numpy
from fractions import Fraction
from picamera import PiCamera
from timelapse import AbstractCameraProxy
from timelapse import TimeLapse


GPU_COMPATIBLE_RESOLUTION = (2592, 1944)
#SHUTTER_SPEED_FACTORS = [4, 2, 1, 0.5, 0.25]
SHUTTER_SPEED_FACTORS = [4, 1, 0.25]


class HDRRPiCameraProxy(AbstractCameraProxy):
    def __init__(self):
        AbstractCameraProxy.__init__(self, "Python PiCamera with CV2 HDR postprocessing")
        self.camera = None
        self.resolution = None

    def init_camera(self, resolution):
        self.camera = PiCamera()
        self.resolution = resolution
        self.camera.resolution = GPU_COMPATIBLE_RESOLUTION

    def take_picture(self, image_name):
        exposure_speed = self.camera.exposure_speed
        images = []
        for factor in SHUTTER_SPEED_FACTORS:
            shutter_speed = exposure_speed*factor
            images.append(self.capture_picture_with_shutter_speed(shutter_speed))
        hdr_image = HDRRPiCameraProxy.create_hdr_image(images)
        scaled_image = self.scale_and_crop_image(hdr_image)
        cv2.imwrite(image_name, scaled_image)
        self.camera.shutter_speed = 0

    def close_camera(self):
        self.camera.stop_preview()
        self.camera.close()

    def capture_picture_with_shutter_speed(self, shutter_speed):
        self.camera.shutter_speed = shutter_speed
        resolution = self.camera.resolution
        image = numpy.empty((resolution[0] * resolution[1] * 3), dtype=numpy.uint8)
        self.camera.capture(image, format='bgr', use_video_port=False)
        return image.reshape((resolution[1], resolution[0], 3))

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
