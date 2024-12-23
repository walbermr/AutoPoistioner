import cv2

from .rectangle import Rectangle


class BoundingBox(Rectangle):
    def print_bbox(self, frame):
        return cv2.rectangle(frame, list(self.limits[0]), list(self.limits[1]), (0,255,0), 2)