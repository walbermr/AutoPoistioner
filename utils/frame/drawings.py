from typing import List, Tuple

from .geometry.rectangle import Rectangle
from .geometry.boundingbox import BoundingBox
from .geometry.circle import Circle


class Color:
    RED = (4,0,255)
    GREEN = (40,255,0)
    BLUE = (255,0,85)
    YELLOW = (0,255,236)
    CYAN = (255,192,0)


def getBboxes(outputs, frame_resolution, score_thr, removable_area:List[Rectangle]):
    rects:List[Tuple[int]] = []
    boxes:List[Rectangle] = []

    for output in outputs:
        for box in output:
            print(box)
            if len(box) == 0: continue

            box = [
                min(box[0], frame_resolution[1]),
                min(box[1], frame_resolution[0]),
                min(box[2], frame_resolution[1]),
                min(box[3], frame_resolution[0]),
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

    print(boxes, rects)

    return rects, boxes


def drawBoxes(boxes:List[BoundingBox], frame):
    for bbox in boxes:
        bbox.draw(frame, color=Color.GREEN)
