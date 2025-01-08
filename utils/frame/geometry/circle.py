import numpy as np

from .point import Point

class Circle():
    def __init__(self, x, y, r):
        self.x = x
        self.y = y
        self.r = r

        self._center = Point(x, y)
        self._area = np.pi * (r**2)

    @property
    def area(self):
        return self._area

    @property
    def center(self):
        return self._center