import cv2

import numpy as np

from collections import deque

from utils.frame.geometry import Circle, Rectangle, Point
from utils.frame.drawings import Color


class ConversionFactor:
    def __init__(self, value=0):
        self._factor = 0
        self._linear_factor = 0
        self.update(value)

    def update(self, value: float):
        self._factor = value
        self._linear_factor = np.sqrt(self._factor / np.pi)

    @property
    def linear(self) -> float:
        return self._linear_factor

    def __mul__(self, num) -> float:
        return self._factor * num


class PetriDish():
    def __init__(self, diameter: float):
        self._segmentation = None

        self._pixelCentroid: Point = Point(0, 0)
        self._pixelRadius: float = 0
        self._pixelArea: float = 0

        self._diameter: float = diameter
        self._conversionFactor: float = ConversionFactor()

        self.center: Circle = None

    def getCentroid(self) -> Point:
        return self._pixelCentroid

    def drawCentroid(self, frame):
        frame = cv2.line(
            frame, 
            (self._pixelCentroid.x, self._pixelCentroid.y), 
            (self._pixelCentroid.x, self._pixelCentroid.y), 
            (255,0,0), 
            10,
        )
        return frame
    
    def drawMask(self, frame, color=Color.CYAN, alpha=0.2):
        colored_mask = np.zeros_like(frame)
        
        colored_mask[self._segmentation == 1, 0] = color[0]
        colored_mask[self._segmentation == 1, 1] = color[1]
        colored_mask[self._segmentation == 1, 2] = color[2]

        frame = cv2.addWeighted(frame, 1.0-alpha, colored_mask, alpha, 0)

        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

        return frame
    
    def getConversionFactor(self) -> ConversionFactor:
        return self._conversionFactor
    
    def setDishDiameter(self, diameter: float) -> None:
        self._diameter = diameter

    def _updateConversionFactor(self) -> None:
        if self._diameter == 0:
            return
        
        realArea = np.pi * (self._diameter / 2.0) ** 2
        self._conversionFactor.update(realArea / self._pixelArea)

    def findCentroid(self):
        imageMoments = cv2.moments(self._segmentation)

        # Compute centroid
        cx = int(imageMoments["m10"]/imageMoments["m00"])
        cy = int(imageMoments["m01"]/imageMoments["m00"])

        self._pixelCentroid = Point(cx, cy)
        self.center = Circle(cx, cy, 2)

    def findParameters(self, estimate) -> None:
        # Calculate radius
        self._segmentation = self._clearSegmentation(
            estimate, self._segmentation,
        )

        self.findCentroid()

        self._pixelArea = self._segmentation.sum()
        self._pixelRadius = np.sqrt(self._pixelArea / np.pi)

        self._updateConversionFactor()

    def _clearSegmentation(self, centroid, seg):
        newMat = np.zeros_like(seg)
        N, M = len(seg), len(seg[0])
        directions = [(-1,0), (0,-1), (1,0), (0,1)]
        queue = deque([centroid])
        seen = set([centroid])

        valid = lambda a, b: 0 <= a < N and 0 <= b < M and seg[a][b]

        while queue:
            x, y = queue.popleft()
            
            newMat[x][y] = 1

            for d in directions:
                xx, yy = x + d[0], y + d[1]

                if (xx, yy) in seen: continue

                if valid(xx, yy):
                    queue.append((xx, yy))

                seen.add((xx, yy))

        return newMat
    
    def segmentDish(self, image) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

        # Morph open using elliptical shaped kernel
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
        opening = 255 - cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=3)

        dishSegmentationMask = opening[..., np.newaxis].repeat(3, axis=2)
        dishSegmentationMask[..., 0:2] = 0

        self._segmentation = (opening != 0).astype(float)

        return dishSegmentationMask
    
    def isSegmented(self):
        return self.center is not None


class Colony():
    def __init__(self, detection: Rectangle, dishPixelCenter: Point, conversionFactor: ConversionFactor):
        self._conversionFactor: ConversionFactor = conversionFactor
        self._detection: Rectangle = detection
        self._coordinateZero: Point = dishPixelCenter
        
        self._limits = Circle(
            self._detection.cx, 
            self._detection.cy, 
            (self._detection.h + self._detection.w) / 2,
        )

    def getPixelOffset(self) -> Point:
        return self._limits.center

    def getOffset(self) -> Point:
        return (self._limits.center - self._coordinateZero) * self._conversionFactor.linear

    def getConversionFactor(self) -> ConversionFactor:
        return self._conversionFactor
    
    def setConversionFactor(self, factor: ConversionFactor) -> None:
        self._conversionFactor = factor

    def getPixelArea(self) -> float:
        '''
            Returns the area in pixels.
        '''
        return self._limits.area
    
    def getArea(self) -> float:
        '''
            Returns the real area after convertion.
        '''
        return self._limits.area * self._conversionFactor

