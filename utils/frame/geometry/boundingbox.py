import cv2

from .rectangle import Rectangle

class BoundingBox(Rectangle):
    def draw(self, frame, color=(0, 255, 0)):
        p1, p2 = list(self.limits[0]), list(self.limits[1])
        frame = cv2.rectangle(frame, p1, p2, color, 2)

        if self.idx is not None:
            frame = cv2.putText(
                frame, 
                "%d"%(self.idx), 
                p1, 
                cv2.FONT_HERSHEY_SIMPLEX, 
                1, 
                color, 
                2, 
                cv2.LINE_AA
            )

        return frame