import cv2
import time
import numpy as np
import tkinter as tk
from collections import OrderedDict
from argparse import Namespace

from typing import List, Tuple

from utils.ui import Controls

from detection.traditional.watershed import WaterShed

from detection.deep.yolov6 import ONNXModel

from utils.frame.drawings import drawRectangles
from utils.frame.geometry import Circle, Rectangle, Point

import threading

DEBUG = True


class EllipseController(Controls):
    def __init__(self, resolution, root=None):
        self.resolution = resolution
        self.centerX = tk.IntVar(value=320)
        self.centerY = tk.IntVar(value=240)
        self.axisX = tk.IntVar(value=100)
        self.axisY = tk.IntVar(value=50)
        self.angle = tk.IntVar(value=0)
        self.thickness = tk.IntVar(value=2)

        super().__init__(root)

    def placeControls(self):
        """Cria os controles deslizantes e campos de entrada."""        
        # Centro X
        tk.Label(self.controls_frame, text="Centro X:").pack()
        tk.Scale(
            self.controls_frame, 
            from_=0, 
            to=self.resolution.x, 
            orient="horizontal", 
            variable=self.centerX,
            length=200
        ).pack()
        
        # Centro Y
        tk.Label(self.controls_frame, text="Centro Y:").pack()
        tk.Scale(
            self.controls_frame, 
            from_=0, 
            to=self.resolution.y,
            orient="horizontal", 
            variable=self.centerY,
            length=200
        ).pack()
        
        # Raio X
        tk.Label(self.controls_frame, text="Raio X:").pack()
        tk.Scale(
            self.controls_frame, 
            from_=10, 
            to=300, 
            orient="horizontal", 
            variable=self.axisX,
            length=200
        ).pack()
        
        # Raio Y
        tk.Label(self.controls_frame, text="Raio Y:").pack()
        tk.Scale(
            self.controls_frame, 
            from_=10, 
            to=300, 
            orient="horizontal", 
            variable=self.axisY,
            length=200
        ).pack()
        
        # Ângulo
        tk.Label(self.controls_frame, text="Ângulo:").pack()
        tk.Scale(
            self.controls_frame, 
            from_=0, 
            to=360, 
            orient="horizontal", 
            variable=self.angle,
            length=200
        ).pack()
        
        # Espessura
        tk.Label(self.controls_frame, text="Espessura:").pack()
        tk.Scale(
            self.controls_frame, 
            from_=1, 
            to=10, orient="horizontal", 
            variable=self.thickness,
            length=200
        ).pack()


class PetriDish():
    def __init__(self, diameter: float):
        self._segmentation = None

        self._pixelCentroid: Point = Point(0, 0)
        self._pixelRadius: float = 0
        self._pixelArea: float = 0

        self._diameter: float = diameter
        self._conversionFactor: float = 0

    def getCentroid(self) -> Point:
        return self._pixelCentroid

    def drawCentroid(self, frame):
        frame = cv2.line(
            frame, 
            (self._pixelCentroid.x, self._pixelCentroid.y), 
            (self._pixelCentroid.x, self._pixelCentroid.y), 
            (255,0,0), 
            10,
        )
        return frame
    
    def getConversionFactor(self) -> float:
        return self._conversionFactor
    
    def setDishDiameter(self, diameter: float) -> None:
        self._diameter = diameter

    def _updateConversionFactor(self) -> None:
        if self._diameter == 0:
            return
        
        realArea = np.pi * (self._diameter / 2.0) ** 2
        self._conversionFactor = realArea / self._pixelArea

    def findParameters(self) -> None:
        imageMoments = cv2.moments(self._segmentation)

        # Compute centroid
        cx = int(imageMoments["m10"]/imageMoments["m00"])
        cy = int(imageMoments["m01"]/imageMoments["m00"])

        self._pixelCentroid = Point(cx, cy)

        # Calculate radius
        self._pixelArea = self._segmentation.sum()
        self._pixelRadius = np.sqrt(self._pixelArea / np.pi)

        self._updateConversionFactor()
    
    def segmentDish(self, image) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

        # Morph open using elliptical shaped kernel
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
        opening = 255 - cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=3)

        dishSegmentationMask = opening[..., np.newaxis].repeat(3, axis=2)
        dishSegmentationMask[..., 0:2] = 0

        self._segmentation = (opening != 0).astype(float)

        return dishSegmentationMask


class Colony():
    def __init__(self, detection: Rectangle, dishPixelCenter: Point, conversionFactor: float):
        self._conversionFactor: float = conversionFactor
        self._detection: Rectangle = detection
        self._coordinateZero: Point = dishPixelCenter
        
        self._limits = Circle(
            self._detection.cx, 
            self._detection.cy, 
            (self._detection.h + self._detection.w) / 2,
        )

    def getPixelOffset(self) -> Point:
        return self._limits.center

    def getOffset(self) -> Point:
        return (self._limits.center - self._coordinateZero) * np.sqrt(self._conversionFactor)

    def getConversionFactor(self) -> float:
        return self._conversionFactor
    
    def setConversionFactor(self, factor: float) -> None:
        self._conversionFactor = factor

    def getPixelArea(self) -> float:
        '''
            Returns the area in pixels.
        '''
        return self._limits.area
    
    def getArea(self) -> float:
        '''
            Returns the real area after convertion.
        '''
        return self._limits.area * self._conversionFactor


class PetriDishController(Controls):
    def __init__(self, root=None):
        self._diameter = tk.IntVar(value=100)
        self._valueList = [50 + 10*i for i in range(11)]

        super().__init__(root)

    def _scaleValuecheck(self, value):
        newvalue = min(self._valueList, key=lambda x:abs(x-float(value)))
        self.slider.set(newvalue)

    def placeControls(self):
        tk.Label(self.controls_frame, text="Diâmetro da placa (mm):").pack()
        self.slider = tk.Scale(
            self.controls_frame,
            from_=min(self._valueList),
            to=max(self._valueList),
            orient="horizontal",
            variable=self._diameter,
            command=self._scaleValuecheck,
            length=200
        )

        self.slider.pack()

    @property
    def diameter(self):
        return self._diameter.get()


class FrameController(Controls):
    def __init__(self, height, width, root=None):
        self.cropXLeft = tk.IntVar(value=0)
        self.cropXRight = tk.IntVar(value=width)
        self.cropYTop = tk.IntVar(value=0)
        self.cropYDown = tk.IntVar(value=height)
        self.resolution = Namespace(x=width, y=height)

        super().__init__(root)

    def placeControls(self):
        tk.Label(self.controls_frame, text="Crop x left:").pack()
        tk.Scale(
            self.controls_frame, 
            from_=0, 
            to=self.resolution.x,
            orient="horizontal", 
            variable=self.cropXLeft,
            length=200
        ).pack()

        tk.Label(self.controls_frame, text="Crop x right:").pack()
        tk.Scale(
            self.controls_frame, 
            from_=0, 
            to=self.resolution.x,
            orient="horizontal", 
            variable=self.cropXRight,
            length=200
        ).pack()

        tk.Label(self.controls_frame, text="Crop y top:").pack()
        tk.Scale(
            self.controls_frame, 
            from_=0, 
            to=self.resolution.y,
            orient="horizontal", 
            variable=self.cropYTop,
            length=200
        ).pack()

        tk.Label(self.controls_frame, text="Crop y down:").pack()
        tk.Scale(
            self.controls_frame, 
            from_=0, 
            to=self.resolution.y,
            orient="horizontal", 
            variable=self.cropYDown,
            length=200
        ).pack()

    @property
    def xLeft(self):
        return self.cropXLeft.get()
    
    @property
    def xRight(self):
        return self.cropXRight.get()
    
    @property
    def yTop(self):
        return self.cropYTop.get()
    
    @property
    def yDown(self):
        return self.cropYDown.get()


class YoloController(Controls):
    def __init__(self, root):
        self.threshold = tk.DoubleVar(value=0.1)

        super().__init__(root)

    def placeControls(self):
        tk.Label(self.controls_frame, text="Limiar de detecção:").pack()
        tk.Scale(
            self.controls_frame,
            from_=0.0,
            to=1.0,
            orient="horizontal",
            variable=self.threshold,
            resolution=0.01,
            length=200
        ).pack()


class MainWindow:
    closeEvent = threading.Event()

    def __init__(self, root):
        self.root = root
        self.root.title("Desenhando Elipse no Feed de Vídeo")
        self.resolution: Namespace = Namespace(x=640, y=640)
        self.detector: ONNXModel = ONNXModel(model_path="./models/bacteria-filtered-smallbox.onnx", custom_export=True)
        
        # Variáveis para os parâmetros da elipse
        # self.petriEllipse = EllipseController(self.resolution, root=self.root)
        self.petriController: PetriDishController = PetriDishController(root=self.root)
        self.petri: PetriDish = PetriDish(self.petriController.diameter)
        self.frameController: FrameController = FrameController(self.resolution.y, self.resolution.x, root=self.root)
        self.waterShed: WaterShed = WaterShed(self.root)
        self.yoloController: YoloController = YoloController(self.root)
        self.colonies: List[Colony] = []

        # Interface gráfica
        # self.petriEllipse.placeControls()
        self.frameController.placeControls()
        self.petriController.placeControls()
        self.waterShed.placeControls()
        self.yoloController.placeControls()
        
        # Feed de vídeo da webcam
        self.cap = cv2.VideoCapture(0)  # Webcam padrão
        self.running = True
        
        # Iniciar a thread para atualizar o feed de vídeo
        self.video_thread: threading.Thread = threading.Thread(target=self.updateVideoFeed)
        self.video_thread.start()
        
        # Fechar janela com segurança
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def getDebugVariables(self):
        varDict = OrderedDict()
        varDict["ellipsis pixel area"] = np.pi * self.petriEllipse.axisX.get() * self.petriEllipse.axisY.get()
        varDict["petri area (mm)"] = np.pi * self.petriController.diameter.get() ** 2
        return varDict

    def displayDebug(self, frame, varDict:OrderedDict):
        for i, key in enumerate(varDict.keys()):
            frame = cv2.putText(
                frame, 
                "%s: %f"%(key, varDict[key]), 
                (50, 50 + 30 * i), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                1, 
                (255, 0, 0), 
                2, 
                cv2.LINE_AA
            )
        return frame
    
    def updateVideoFeed(self):
        """Atualiza o feed de vídeo com a elipse desenhada."""
        while self.running:
            startTime = time.time()
            # ret, frame = self.cap.read()

            # frame = cv2.imread("./images/316_jpg.rf.4c49cf826e0c9700da5e7f4019a844d6.jpg")
            # frame = cv2.imread("./images/17111_jpg.rf.512a1a293c6b3a381bbcd6abc1e1b4fc.jpg")
            frame = cv2.imread("./microbial-dataset-generation/data/style_dishes/6/2019-06-25_02365_nocover.jpg")
            
            frame = cv2.resize(frame, (self.resolution.x, self.resolution.y))
            frame = frame[
                self.frameController.yTop:self.frameController.yDown,
                self.frameController.xLeft:self.frameController.xRight
            ]
            # if not ret:
            #     continue
            
            # Parâmetros da elipse
            # center = (self.petriEllipse.centerX.get(), self.petriEllipse.centerY.get())
            # axes = (self.petriEllipse.axisX.get(), self.petriEllipse.axisY.get())
            # angle = self.petriEllipse.angle.get()
            
            # thickness = self.petriEllipse.thickness.get()

            # if DEBUG:
            #     frame = self.displayDebug(frame, varDict=self.getDebugVariables())
            
            # Desenha a elipse no quadro
            # cv2.ellipse(frame, center, axes, angle, 0, 360, (0, 255, 0), thickness)

            # frame, _ = self.waterShed.process(frame)
            
            nms_thr = self.yoloController.threshold.get()
            output = self.detector.inference(frame, nms_thr)
            
            self.petri.setDishDiameter(self.petriController.diameter)
            frame = self.petri.segmentDish(frame)
            self.petri.findParameters()
            frame = self.petri.drawCentroid(frame)

            _, bboxes = drawRectangles(output, (self.resolution.x, self.resolution.y), nms_thr, frame)
            
            self.colonies = [Colony(r, self.petri.getCentroid(), self.petri.getConversionFactor()) for r in bboxes]

            for c in self.colonies:
                print("Area(mm^2): ", c.getArea(), " - Pixel Area(px^2): ", c.getPixelArea(), " - Offset(mm): ", c.getOffset())
            
            # Exibe o vídeo em uma janela do OpenCV

            cv2.imshow("Detection", frame)

            ellapsedTime = time.time() - startTime
            if ellapsedTime < 1/30:
                time.sleep(1/30 - ellapsedTime)
            
            # Encerra se a tecla 'q' for pressionada
            if MainWindow.closeEvent.isSet() or cv2.waitKey(1) & 0xFF == ord('q'):
                self.running = False
                MainWindow.closeEvent.clear()
                cv2.destroyAllWindows()
                # self.on_close()
                return
    
    def on_close(self):
        """Encerra o programa com segurança."""
        self.running = False
        MainWindow.closeEvent.set()
        self.cap.release()

        self.root.destroy()

# Iniciar o programa
if __name__ == "__main__":
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()
