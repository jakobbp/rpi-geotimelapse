#!/usr/bin/env python

import time
import cv2
from timelapse import *


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

    def take_picture(self, imgName):
        retval, image = self.camera.read()
        scaledImage = self.scale_and_crop_image(image)
        cv2.imwrite(imgName, scaledImage)

    def close_camera(self):
        self.camera.release()

    def scale_and_crop_image(self, image):
        if self.resolution is None:
            return image.copy()

        rWidth = self.resolution[0]
        rHeight = self.resolution[1]
        iHeight, iWidth, channels = image.shape

        if rWidth < iWidth and rHeight < iHeight:
            rAspect = float(rWidth)/float(rHeight)
            iAspect = float(iWidth)/float(iHeight)
            if rAspect < iAspect:
                scaledWidth = rWidth
                scaledHeight = rWidth/iAspect
                wDiff = 0
                hDiff = scaledHeight-rHeight
            else:
                scaledWidth = rHeight*iAspect
                scaledHeight = rHeight
                wDiff = scaledWidth-rWidth
                hDiff = 0
            resizedImage = cv2.resize(image, (scaledWidth, scaledHeight))
            croppedImage = resizedImage[wDiff/2:rWidth, hDiff/2:rHeight]
            return croppedImage

        return image.copy()


def main():
    cameraProxy = GenericCV2CameraProxy()
    timelapse = TimeLapse(cameraProxy)
    timelapse.auto_record_and_upload()


if __name__ == '__main__':
    main()
