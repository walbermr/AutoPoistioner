import cv2

import numpy as np

houghColor = (0, 0, 255)

def nothing(_):
    """
    Callback function for the createTrackbar function;
    this does nothing.
    @param _: no purpose.
    """

    pass # Nothing

def crop_image(img, mask):
    """
    Crops the given image by fitting a bounding box using
    the given circular mask; This makes the output more
    presentable.
    @param img: Image to be cropped.
    @param mask: Circular mask retrieved from Hough Transform.
    @Returns: Cropped (hopefully square) input image.
    """

    output = img

    # if the height is greater than the width;
    # i.e. portrait image
    if img.shape[0] > img.shape[1]:

        # Retrieve the coordinates & radius from circular mask
        x_pos, y_pos, radius = mask

        # Find the coordinates for the bottom left & top right of box
        x_bot = int(x_pos - radius)    # Bottom Left X
        y_bot = int(y_pos - radius)    # Bottom Left Y
        x_top = int(x_pos + radius)    # Top Right X
        y_top = int(y_pos + radius)    # Top Right Y

        # Find min distance from the edge of the box to the image border
        min_x_dist = min((img.shape[1] - x_top), (img.shape[1] - (img.shape[1] - x_bot)))
        min_y_dist = min((img.shape[0] - y_top), (img.shape[0] - (img.shape[0] - y_bot)))
        min_dist = min(min_x_dist, min_y_dist)

        # Apply remainder
        x_bot = (x_bot - min_dist)    # Bottom Left X
        y_bot = (y_bot - min_dist)    # Bottom Left Y
        x_top = (x_top + min_dist)    # Top Right X
        y_top = (y_top + min_dist)    # Top Right Y

        # Crop image using the new mask
        output = output[y_bot:y_top, x_bot:x_top]

    return output