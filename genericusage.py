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

    def take_picture(self, imageName):
        retval, image = self.camera.read()
        scaledImage = self.scale_and_crop_image(image)
        cv2.imwrite(imageName, scaledImage)

    def close_camera(self):
        self.camera.release()

    def scale_and_crop_image(self, image):
        if self.resolution is None:
            return image.copy()

        rWidth = self.resolution[0]
        rHeight = self.resolution[1]
        iHeight, iWidth, channels = image.shape

        if rWidth == iWidth and rHeight == iHeight:
            return image.copy()

        if rWidth < iWidth and rHeight < iHeight:
            rAspect = float(rWidth)/float(rHeight)
            iAspect = float(iWidth)/float(iHeight)
            if rAspect < iAspect:
                scaledWidth = rWidth
                scaledHeight = int(rWidth/iAspect + 0.5)
                wDiff = 0
                hDiff = scaledHeight - rHeight
            else:
                scaledWidth = int(rHeight*iAspect + 0.5)
                scaledHeight = rHeight
                wDiff = scaledWidth - rWidth
                hDiff = 0
            resizedImage = cv2.resize(image, (int(scaledWidth + 0.5), int(scaledHeight + 0.5)))
            croppedImage = resizedImage[wDiff/2:rWidth, hDiff/2:rHeight]
            return croppedImage

        return image.copy()


def main():
    cameraProxy = GenericCV2CameraProxy(0)
    timelapse = TimeLapse(cameraProxy)
    timelapse.auto_record_and_upload()


if __name__ == '__main__':
    main()
