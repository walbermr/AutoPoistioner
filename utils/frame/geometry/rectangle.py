from .point import Point

class Rectangle():
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.xx = x + w
        self.yy = y + h

        hw, hh = w//2, h//2
        cx, cy = x+hw, y+hh

        self.center = Point(cx, cy)
        self.limits = [
            Point(x, y),  #tl
            Point(x+w, y+h),  #br
        ]

        self.valid = self.updateValid()

    def contains(self, p:Point):
        return p.x >= self.x and p.y >= self.y and p.x <= self.xx and p.y <= self.yy
    
    def update_x(self, x):
        self.x = x

    def update_y(self, y):
        self.y = y

    def update_xx(self, xx):
        self.xx = xx
        self.w = self.xx - self.x

    def update_yy(self, yy):
        self.yy = yy
        self.h = self.yy - self.y

    def isValid(self):
        return self.valid
    
    def setValid(self, valid):
        self.valid = valid

    def updateValid(self):
        self.valid = self.h > 0 and self.w > 0

    @property
    def cx(self):
        return self.center.x

    @property
    def cy(self):
        return self.center.y
    
    def __str__(self):
        return "Rectangle (%d, %d), (%d, %d)" %(self.x, self.y, self.xx, self.yy)