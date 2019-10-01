import logging

import cv2
import numpy as np

logger = logging.getLogger('vk_grabber')


class Detector:
    def __init__(self, path_to_weights):
        self._detector = cv2.CascadeClassifier(path_to_weights)

    @staticmethod
    def get_image(response):
        frame = np.asarray(bytearray(response), dtype="uint8")
        img = cv2.imdecode(frame, cv2.IMREAD_COLOR)
        return img

    def get_crops(self, img, min_size):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        crops = self._detector.detectMultiScale(
            gray,
            scaleFactor=1.05,
            minNeighbors=12,
            minSize=min_size
        )
        return crops

    @staticmethod
    def write_crop(dest, crop):
        res = cv2.imwrite(dest, crop)
        logger.debug(f'Save crop to {dest} {"ok" if res else "failed"}')
