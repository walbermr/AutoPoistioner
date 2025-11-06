import cv2

from .rectangle import Rectangle

class BoundingBox(Rectangle):
    def draw(self, frame, color=(0, 255, 0)):
        return cv2.rectangle(frame, list(self.limits[0]), list(self.limits[1]), color, 2)