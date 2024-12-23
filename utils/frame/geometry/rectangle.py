from .point import Point

class Rectangle():
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

        hw, hh = w//2, h//2
        cx, cy = x+hw, y+hh

        self.center = Point(cx, cy)
        self.limits = [
            Point(x, y),  #tl
            Point(x+w, y+h),  #br
        ]

    @property
    def cx(self):
        return self.center.x

    @property
    def cy(self):
        return self.center.y