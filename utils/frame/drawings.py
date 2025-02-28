from typing import List

from .geometry.rectangle import Rectangle
from .geometry.boundingbox import BoundingBox


def drawRectangles(outputs, frame_resolution, score_thr, frame, removable_area:List[Rectangle]):
    rects = []
    boxes:List[Rectangle] = []

    for output in outputs:
        try:
            output[0].clip(0, frame_resolution[1])  # x1
            output[1].clip(0, frame_resolution[0])  # y1
            output[2].clip(0, frame_resolution[1])  # x2
            output[3].clip(0, frame_resolution[0])  # y2

            for box in output:
                x1, y1, x2, y2, score, index = box
                if score > score_thr:
                    x, y, h, w = int(x1), int(y1), int(abs(x1-x2)), int(abs(y1-y2))
                    bbox = BoundingBox(x, y, h, w)
                    remove_box = False
                    if len(removable_area) > 0:
                        for area in removable_area:
                            remove_box |= area.contains(bbox.center)

                    if not remove_box:
                        bbox.print_bbox(frame)
                        boxes.append(bbox)
                        rects.append((x, y, x+w, y+h))
        except:
            print("No detections.")

    return rects, boxes