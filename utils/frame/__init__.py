def center_crop(frame, crop_resolution):
    center = frame.shape[0] / 2, frame.shape[1] / 2

    h = crop_resolution[0]
    w = crop_resolution[1]

    y = center[0] - h/2
    x = center[1] - w/2

    return frame[int(y):int(y + h), int(x):int(x + w)]