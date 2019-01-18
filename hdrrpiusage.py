#!/usr/bin/env python

import cv2
import numpy
from picamera import PiCamera
from multiprocessing import Process
from timelapse import AbstractCameraProxy
from timelapse import TimeLapse


GPU_COMPATIBLE_RESOLUTION = (2592, 1944)
#SHUTTER_SPEED_FACTORS = [4, 2, 1, 0.5, 0.25]
SHUTTER_SPEED_FACTORS = [4, 1, 0.25]


class HDRRPiCameraProxy(AbstractCameraProxy):
    def __init__(self):
        AbstractCameraProxy.__init__(self, "Python PiCamera with CV2 HDR postprocessing")
        self.camera = None

    def init_camera(self, resolution):
        self.camera = PiCamera()
        self.camera.resolution = resolution

    def take_picture(self, image_name):
        exposure_speed = self.camera.exposure_speed
        images = []
        for factor in SHUTTER_SPEED_FACTORS:
            shutter_speed = exposure_speed*factor
            images.append(self.capture_picture_with_shutter_speed(shutter_speed))
        self.camera.shutter_speed = 0
        hdr_process = HDRProcess(image_name, images)
        hdr_process.start()

    def close_camera(self):
        self.camera.stop_preview()
        self.camera.close()

    def capture_picture_with_shutter_speed(self, shutter_speed):
        self.camera.shutter_speed = shutter_speed
        resolution = self.camera.resolution
        image = numpy.empty((resolution[0] * resolution[1] * 3), dtype=numpy.uint8)
        self.camera.capture(image, format='bgr', use_video_port=False)
        return image.reshape((resolution[1], resolution[0], 3))


class HDRProcess(Process):
    def __init__(self, image_name, images):
        Process.__init__(self)
        self.image_name = image_name
        self.images = images

    def run(self):
        merge_mertens = cv2.createMergeMertens()
        hdr_image = merge_mertens.process(self.images)
        cv2.imwrite(self.image_name, hdr_image)


def main():
    camera_proxy = HDRRPiCameraProxy()
    timelapse = TimeLapse(camera_proxy)
    timelapse.auto_record_and_upload()


if __name__ == '__main__':
    main()
