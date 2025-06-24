import tkinter as tk
import cv2

class CVDetector:
    def __init__(self):
        self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
    
    def inference(self, inputFrmae, *args, **kwargs):
        gray = cv2.cvtColor(inputFrmae, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        thresh = cv2.threshold(edges, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

        opening = 255 - cv2.morphologyEx(thresh, cv2.MORPH_OPEN, self.kernel, iterations=2)

        contours, hier = cv2.findContours(opening, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        valid = []
        i = 0

        # draw a bounding box around each contour
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h
            if 0 < area < 200:
                valid.append((x, y, x+w, y+h, 1.0, i))
                i += 1

        return valid