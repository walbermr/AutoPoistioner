import datetime
from typing import List
from PIL import Image

from .entities import Colony


def data_to_yolo(data: List[Colony]):
    str_data = []

    for c in data:
        str_data.append("0 %f %f %f %f"%(c._detection.x, c._detection.y, c._detection.h, c._detection.w))

    return str_data


def serial_to_xy(data: List[str]):
    data = [d.split(",") for d in data]
    return [(float(d[0][1:]), float(d[1][1:])) for d in data]


def get_timehash():
    return str(datetime.datetime.now()).replace(":", "-").replace(".", "-")


def save_yolo(data, path):
    str_data = data_to_yolo(data)
    with open(path) as f:
        f.writelines(str_data)


def save_xy_center(data, path):
    str_data = serial_to_xy(data)
    with open(path) as f:
        f.writelines(str_data)


def save_image(data, path):
    img = Image.fromarray(data)
    img.save(path)
