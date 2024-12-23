import cv2
import tkinter as tk

import numpy as np

from .utils import nothing, crop_image, houghColor

import sys

sys.path.append("..")
from utils.ui import Controls


class PlaterFinder(Controls):
    def __init__(self, root):
        self.plateRadius = tk.IntVar(value=0)
        self.plateOffset = tk.IntVar(value=0)
        super().__init__(root)

    def placeControls(self):
        tk.Label(self.controls_frame, text="Plate Radius").pack()
        tk.Scale(
            self.controls_frame, 
            from_=0, 
            to=50,
            orient="horizontal", 
            variable=self.plateRadius,
            length=200
        ).pack()

        tk.Label(self.controls_frame, text="Radius offset").pack()
        tk.Scale(
            self.controls_frame, 
            from_=0, 
            to=200,
            orient="horizontal", 
            variable=self.plateOffset,
            length=200
        ).pack()
    
    def process(self, img_ori, img_bin):
        """
        Identifies the plate with input from the user using the Hough Circle Transform.
        @param img_ori: Original image.
        @param img_bin: Binary thresholded image.
        @Returns: (Plate mask, circle).
        """

        # Define the max possible plate radius as
        # half the image size
        max_possible_radius = int(min(img_bin.shape) / 2)
        circle = 0

        # Loop to keep the window open
        # Read the parameters from the GUI
        radius_scale = self.plateRadius.get() / 100
        max_radius = int((max_possible_radius * radius_scale) + (max_possible_radius * 0.5))
        min_radius = max_radius - 10

        radius_offset = self.plateOffset.get() / 100

        # Find plate in the image with Hough Circle Transform
        circles = cv2.HoughCircles(img_bin, cv2.HOUGH_GRADIENT, 1, 20, param1=100,
                                    param2=10, minRadius=min_radius, maxRadius=max_radius)

        img_show = img_ori.copy()

        if circles is not None:

            # Return data of the smallest circle found
            circles = (circles[0, :]).astype("float")
            max_c = np.argmax(circles, axis=0)
            indx = max_c[2]
            circle = circles[indx]
            circle = (int(circle[0]), int(circle[1]), int(radius_offset * circle[2]))

            # Draw the outer circle
            cv2.circle(img_show, (circle[0], circle[1]), circle[2], houghColor, 2)

            # Draw the center of the circle
            cv2.circle(img_show, (circle[0], circle[1]), 2, houghColor, 3)

        # Create plate mask:
        plate_mask = np.zeros(img_bin.shape, np.uint8)
        plate_mask = cv2.circle(plate_mask, (circle[0], circle[1]), circle[2], (255, 255, 255),
                                thickness=-1)

        return plate_mask, circle


class WaterShed(Controls):
    def __init__(self, root=None):
        super().__init__(root)
        self.invertPlate = tk.IntVar(False)
        self.invertMask = tk.IntVar(False)
        self.processMore = tk.IntVar(False)

        self.plateFinder = PlaterFinder(root=root)


    def placeControls(self):
        self.plateFinder.placeControls()

        tk.Checkbutton(
            self.controls_frame,
            text="Invert Plate",
            variable=self.invertPlate
        ).pack()
        tk.Checkbutton(
            self.controls_frame,
            text="Invert Mask",
            variable=self.invertMask
        ).pack()
        tk.Checkbutton(
            self.controls_frame,
            text="Process more",
            variable=self.processMore
        ).pack()


    def preprocess(self, img_ori):
        """
        Preprocesses the input image so that it can be used in the different algorithms.
        @param img_ori: Original input image.
        @Returns: (original image - cropped, preprocessed image).
        """

        # Kernal to be used for strong laplace filtering
        kernal_strong = np.array([
            [1, 1, 1],
            [1, -8, 1],
            [1, 1, 1]],
            dtype=np.float32)

        # Kernal to be used for weak laplace filtering
        kernal_weak = np.array([
            [0, 1, 0],
            [1, -4, 1],
            [0, 1, 0]],
            dtype=np.float32)

        # Perform laplace filtering
        img_lap = cv2.filter2D(img_ori, cv2.CV_32F, kernal_weak)
        img_sharp = np.float32(img_ori) - img_lap

        # Convert to 8bits gray scale
        img_sharp = np.clip(img_sharp, 0, 255).astype('uint8')
        img_gray = cv2.cvtColor(img_sharp, cv2.COLOR_BGR2GRAY)

        # Binarize the greyscale image
        _, img_bin = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

        # Remove noise from the binary image
        img_bin = cv2.morphologyEx(img_bin, cv2.MORPH_OPEN, np.ones((2, 2), dtype=int))

        # Find the circular plate mask in the image
        plate_mask, circle = self.plateFinder.process(img_ori, img_bin)

        cv2.circle(img_ori, (int(circle[0]), int(circle[1])), int(circle[2]), houghColor, 2)

        # Crop the original image if needed
        img_ori = crop_image(img_ori, circle)

        # If the number of white pixels is greater than the number of black pixels
        # i.e. attempt to automatically detect the mask colour
        inv = 0
        if np.sum(img_bin == 255) > np.sum(img_bin == 0):
            inv = 1

        img_pro = np.copy(img_bin)

        # Apply circular mask
        img_pro[(plate_mask == False)] = 255 if bool(self.invertMask.get()) else 0

        # Crop the processed image if needed
        img_pro = crop_image(img_pro, circle)

        # Apply extra processing if needed
        if self.processMore.get():
            img_pro = cv2.erode(img_pro, None)
            img_pro = cv2.dilate(img_pro, None)
            img_pro = cv2.erode(img_pro, None)

        # Invert the colours of the image, or not
        inv = bool(self.invertPlate.get())
        if inv == 0:
            result = img_pro
        elif inv == 1:
            result = cv2.bitwise_not(img_pro)

        # Return the (cropped) original image and processed image
        return img_ori, result, circle

    def process(self, img_ori):
        """
        Colony identification using watershed transform.
        @param img_ori: Original image.
        @param img_pro: Processed image.
        @Returns: (output image, no. colonies).
        """

        colonyColor = (0, 0, 255)
        img_ori, img_pro, _ = self.preprocess(img_ori)

        # Create the border of the components
        border = cv2.dilate(img_pro, None)
        border = border - cv2.erode(border, None)

        # Create the seed(s) for the watershed transform
        dist = cv2.distanceTransform(img_pro, 2, 3)
        dist = ((dist - dist.min()) / (dist.max() - dist.min()) * 255).astype(np.uint8)
        _, dist = cv2.threshold(dist, 110, 255, cv2.THRESH_BINARY)

        # Find the markers for the watershed transform
        num_components, markers = cv2.connectedComponents(dist)

        # Completing the markers
        markers = markers * (255 / (num_components + 1))
        markers[border == 255] = 255
        markers = markers.astype(np.int32)

        # Perfoming the watershead transform
        cv2.watershed(img_ori, markers)

        # Make the markers pretty and apply them to the input image
        markers[markers == -1] = 0
        markers = markers.astype(np.uint8)
        result = 255 - markers
        result[result != 255] = 0
        result = cv2.dilate(result, None)
        img_ori[result == 255] = colonyColor

        return img_ori, num_components - 1