from typing import List, Tuple

from .geometry.rectangle import Rectangle
from .geometry.boundingbox import BoundingBox


def getBboxes(outputs, frame_resolution, score_thr, removable_area:List[Rectangle]):
    rects:List[Tuple[int]] = []
    boxes:List[Rectangle] = []

    for output in outputs:
        for box in output:
            if len(box) == 0: continue

            box = [
                max(box[0], frame_resolution[1]),
                max(box[1], frame_resolution[0]),
                max(box[2], frame_resolution[1]),
                max(box[3], frame_resolution[0]),
                box[4],
                box[5],
            ]   # transform from tupleto lix, avoiding modifying the underlying data

            x1, y1, x2, y2, score, index = box
            if score > score_thr:
                x, y, h, w = int(x1), int(y1), int(abs(x1-x2)), int(abs(y1-y2))
                bbox = BoundingBox(x, y, h, w)
                remove_box = False
                if len(removable_area) > 0:
                    for area in removable_area:
                        remove_box |= area.contains(bbox.center)

                if not remove_box:
                    boxes.append(bbox)
                    rects.append((x, y, x+w, y+h))
    
    if len(boxes) == 0:
        print("No detections.")

    return rects, boxes


def drawBoxes(boxes:List[Rectangle], frame):
    for bbox in boxes:
        bbox.print_bbox(frame)