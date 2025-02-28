import cv2

def center_crop(frame, crop_resolution):
    frame_h, frame_w = frame.shape[0], frame.shape[1]

    if frame_h < 640 or frame_w < 640:
        ratio = max(crop_resolution[0] / frame_h, frame_w / crop_resolution[1])
        frame = cv2.resize(frame, (int(frame_w * ratio), int(frame_h * ratio)))
        frame_h, frame_w = frame.shape[0], frame.shape[1]

    center = frame_h / 2, frame_w / 2

    h = crop_resolution[0]
    w = crop_resolution[1]

    y = center[0] - h/2
    x = center[1] - w/2

    frame = frame[int(y):int(y + h), int(x):int(x + w)]

    return frame