#!/usr/bin/env python

import time
import cv2
from timelapse import AbstractCameraProxy
from timelapse import TimeLapse


class GenericCV2CameraProxy(AbstractCameraProxy):
    def __init__(self, camera_id):
        AbstractCameraProxy.__init__(self, "Generic CV2 Camera")
        self.camera_id = camera_id
        self.camera = None
        self.resolution = None

    def init_camera(self, resolution):
        self.camera = cv2.VideoCapture(self.camera_id)
        self.resolution = resolution
        time.sleep(2)

    def take_picture(self, image_name):
        retval, image = self.camera.read()
        scaled_image = self.scale_and_crop_image(image)
        cv2.imwrite(image_name, scaled_image)

    def close_camera(self):
        self.camera.release()

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


def main():
    camera_proxy = GenericCV2CameraProxy(0)
    timelapse = TimeLapse(camera_proxy)
    timelapse.auto_record_and_upload()


if __name__ == '__main__':
    main()
