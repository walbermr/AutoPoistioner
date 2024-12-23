import numpy as np
import onnxruntime as ort

from .utils import non_max_suppression

class ONNXModel:
    def __init__(self, model_path="./models/bacteria-l.onnx"):
        self.ort_sess = ort.InferenceSession(model_path)

    def inference(self, inputFrmae, score_thr):
        samples = np.array(inputFrmae)[np.newaxis,:].transpose(0,3,1,2).astype(np.float32) / 255
        outputs = self.ort_sess.run(None, {'input': samples})
        outputs = np.array(outputs[0])
        # NMS
        outputs = non_max_suppression(outputs, score_thr, 0.45)

        return outputs