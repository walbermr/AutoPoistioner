from typing import List

from .geometry.rectangle import Rectangle
from .geometry.boundingbox import BoundingBox


def drawRectangles(outputs, frame_resolution, score_thr, frame):
    rects = []

    for output in outputs:
        output[:, 0].clip(0, frame_resolution[1])  # x1
        output[:, 1].clip(0, frame_resolution[0])  # y1
        output[:, 2].clip(0, frame_resolution[1])  # x2
        output[:, 3].clip(0, frame_resolution[0])  # y2

        boxes:List[Rectangle] = []
        for box in output:
            x1, y1, x2, y2, score, index = box
            if score > score_thr:
                x, y, h, w = int(x1), int(y1), int(abs(x1-x2)), int(abs(y1-y2))
                bbox = BoundingBox(x, y, h, w)
                bbox.print_bbox(frame)
                boxes.append(bbox)

                rects.append((x, y, x+w, y+h))

    return rects, boxes