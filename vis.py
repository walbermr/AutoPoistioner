import cv2
import time
import numpy as np
import tkinter as tk

from collections import OrderedDict
from argparse import Namespace
from PIL import Image, ImageTk

from typing import List

from detection.traditional.watershed import WaterShed

from detection.deep.yolov6 import ONNXModel

from utils.frame.drawings import drawRectangles
from utils.entities import PetriDish, Colony
from utils.controllers import PetriDishController, FrameController, YoloController
from utils.frame.geometry import Rectangle, Point
from utils.frame import center_crop
from utils.camera import list_ports

import threading

DEBUG = True


class MainWindow:
    closeEvent = threading.Event()
    rectangleRemovingLock = threading.Lock()

    def __init__(self, root):
        self.root = root
        self.root.title("Bacteria Detection")
        self.resolution: Namespace = Namespace(x=640, y=640)
        self.detector: ONNXModel = ONNXModel(model_path="./models/bacteria-filtered-smallbox.onnx", custom_export=True)
        
        # Variáveis para os parâmetros da elipse
        # self.petriEllipse = EllipseController(self.resolution, root=self.root)
        self.petriController: PetriDishController = PetriDishController(root=self.root)
        self.petri: PetriDish = PetriDish(self.petriController.diameter)
        # self.frameController: FrameController = FrameController(self.resolution.y, self.resolution.x, root=self.root)
        # self.waterShed: WaterShed = WaterShed(self.root)
        self.yoloController: YoloController = YoloController(self.root)
        self.colonies: List[Colony] = []

        # Interface gráfica
        # self.petriEllipse.placeControls()
        # self.frameController.placeControls()
        self.petriController.placeControls()
        # self.waterShed.placeControls()
        self.yoloController.placeControls()
        self.canvas = tk.Canvas(self.root, bg="black", width=self.resolution.x, height=self.resolution.y)
        self.canvas.pack(side="top", fill="both", expand=True)
        self.canvas.bind("<ButtonPress-1>", self.on_left_button_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_left_button_release)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonPress-3>", self.on_right_button_press)
        self.canvas.bind("<ButtonRelease-3>", self.on_right_button_release)
        self.canvas.pack()

        self.removedRect = None
        self.removedAreas: List[Rectangle] = []
        self.newArea = Rectangle(0,0,0,0)

        camera_options = ["Camera %d" %(i) for i in list_ports()[1]] #etc
        self.camera_var = tk.StringVar(self.root)
        self.camera_var.set(camera_options[0]) # default value
        camera_dropdown = tk.OptionMenu(self.root, self.camera_var, *camera_options, command=self.on_camera_change)
        camera_dropdown.pack()
        
        # Feed de vídeo da webcam
        self.cap = cv2.VideoCapture(int(camera_options[0][-1]))  # Webcam padrão
        self.running = True
        
        # Iniciar a thread para atualizar o feed de vídeo
        self.video_thread: threading.Thread = threading.Thread(target=self.updateVideoFeed)
        self.video_thread.start()
        
        # Fechar janela com segurança
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_camera_change(self, value):
        self.cap.release()
        self.cap = cv2.VideoCapture(int(value[-1]))  # Webcam padrão

    def on_right_button_press(self, event):
        self.deleteBoxPoint:Point = Point(event.x, event.y)

    def on_right_button_release(self, event):
        idxDelete = 0
        closestBox = None
        for i, box in enumerate(self.removedAreas):
            if box.contains(self.deleteBoxPoint):
                idxDelete = i
                if closestBox is None:
                    closestBox = box
                else:
                    if (closestBox.center - self.deleteBoxPoint).abs() > (box.center - self.deleteBoxPoint).abs():
                        closestBox = box
        if closestBox != None:
            self.removedAreas.pop(idxDelete)

    def on_left_button_press(self, event):
        # save mouse drag start position
        with MainWindow.rectangleRemovingLock:
            self.rect = None
            self.newArea.update_x(event.x)
            self.newArea.update_y(event.y)

        # create rectangle if not yet exist
        #if not self.rect:
        self.removedRect = self.canvas.create_rectangle(self.newArea.x, self.newArea.y, 1, 1, fill="black")

    def on_move_press(self, event):
        self.newArea.update_xx(event.x)
        self.newArea.update_yy(event.y)
        self.newArea.updateValid()

        # expand rectangle as you drag the mouse
        self.canvas.coords(self.removedRect, self.newArea.x, self.newArea.y, self.newArea.xx, self.newArea.yy)

    def on_left_button_release(self, event):
        self.removedAreas.append(self.newArea)
        self.newArea = Rectangle(0,0,0,0)
    
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
    
    def _arrayToImage(self, data: np.ndarray) -> tk.PhotoImage:
        data = cv2.cvtColor(data, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(data)
        return ImageTk.PhotoImage(image=image)

    def updateVideoFeed(self):
        """Atualiza o feed de vídeo com a elipse desenhada."""
        while self.running:
            startTime = time.time()
            ret, frame = self.cap.read()

            # frame = cv2.imread("./images/316_jpg.rf.4c49cf826e0c9700da5e7f4019a844d6.jpg")
            # frame = cv2.imread("./images/17111_jpg.rf.512a1a293c6b3a381bbcd6abc1e1b4fc.jpg")
            # frame = cv2.imread("./microbial-dataset-generation/data/style_dishes/6/2019-06-25_02365_nocover.jpg")
            frame = center_crop(frame, (640, 640))
            
            frame = cv2.resize(frame, (self.resolution.x, self.resolution.y))
            # frame = frame[
            #     self.frameController.yTop:self.frameController.yDown,
            #     self.frameController.xLeft:self.frameController.xRight
            # ]
            
            nms_thr = self.yoloController.threshold.get()
            output = self.detector.inference(frame, nms_thr)
            
            self.petri.setDishDiameter(self.petriController.diameter)
            _ = self.petri.segmentDish(frame)
            self.petri.findParameters()
            frame = self.petri.drawCentroid(frame)

            if self.newArea.isValid():
                cv2.rectangle(frame, (self.newArea.x, self.newArea.y), (self.newArea.xx, self.newArea.yy), (0, 0, 0), -1)
 
            for area in self.removedAreas:
                cv2.rectangle(frame, (area.x, area.y), (area.xx, area.yy), (0, 0, 0), -1)

            _, bboxes = drawRectangles(
                output, 
                (self.resolution.x, self.resolution.y), 
                nms_thr, 
                frame, 
                self.removedAreas,
            )
            
            self.colonies = [Colony(r, self.petri.getCentroid(), self.petri.getConversionFactor()) for r in bboxes]
            
            # Exibe o vídeo em uma janela do OpenCV

            imageFrame = self._arrayToImage(frame)
            self.canvas.create_image(0, 0, image=imageFrame, anchor="nw")
            self.canvas.image = imageFrame

            # cv2.imshow("Detection", frame)

            ellapsedTime = time.time() - startTime
            if ellapsedTime < 1/30:
                time.sleep(1/30 - ellapsedTime)
            
            # Encerra se a tecla 'q' for pressionada
            if MainWindow.closeEvent.isSet() or cv2.waitKey(1) & 0xFF == ord('q'):
                self.running = False
                MainWindow.closeEvent.clear()
                cv2.destroyAllWindows()
                self.root.quit()
                return
    
    def on_close(self):
        """Encerra o programa com segurança."""
        self.running = False
        MainWindow.closeEvent.set()
        self.cap.release()

# Iniciar o programa
if __name__ == "__main__":
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()
