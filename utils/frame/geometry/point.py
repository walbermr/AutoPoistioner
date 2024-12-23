import math

class Point():
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __iter__(self):
        return iter([self.x, self.y])
    
    def __add__(self, val):
        if isinstance(val, Point):
            new_x = self.x + val.x
            new_y = self.y + val.y
        else:
            raise ValueError("err")

        return Point(new_x, new_y)
    
    def __sub__(self, val):
        if isinstance(val, Point):
            new_x = self.x - val.x
            new_y = self.y - val.y
        else:
            raise ValueError("err")

        return Point(new_x, new_y)
    
    def abs(self) -> float:
        return math.sqrt(self.x**2 + self.y**2)
    
    def __str__(self) -> str:
        return f"{self.x}, {self.y}"