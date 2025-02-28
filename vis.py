import cv2
import time
import copy
import numpy as np
import tkinter as tk

from collections import OrderedDict, deque
from argparse import Namespace
from PIL import Image, ImageTk

from typing import List, Deque

from detection.traditional.watershed import WaterShed

from detection.deep.yolov6 import ONNXModel

from utils.frame.drawings import getBboxes, drawBoxes
from utils.entities import PetriDish, Colony
from utils.controllers import PetriDishController, FrameController, YoloController
from utils.frame.geometry import Rectangle, Point
from utils.frame import center_crop
from utils.camera import list_ports
from utils.serial import SerialWrapper

import threading

DEBUG = True


class MainWindow:
    closeEvent = threading.Event()
    processEvent = threading.Event()

    rectangleRemovingLock = threading.Lock()
    frameLock = threading.Lock()

    def __init__(self, root):
        self.root = root
        self.running = True
        self.root.title("Bacteria Detection")
        self.resolution: Namespace = Namespace(x=640, y=640)
        self.detector: ONNXModel = ONNXModel(
            model_path="./models/bacteria-filtered-smallbox.onnx", 
            custom_export=True,
        )
        
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
        self.serial = SerialWrapper()
        serial_options = self.serial.get_available_ports() #etc
        self.serial_var = tk.StringVar(self.root)
        
        if len(serial_options) != 0:
            self.serial_var.set(serial_options[0]) # default value
        else:
            self.serial_var.set("") # default value
            serial_options = [""]

        serial_dropdown = tk.OptionMenu(self.root, self.serial_var, *serial_options, command=self.on_serial_change)
        serial_dropdown.pack(side="left")
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
        self.bboxes = []

        camera_options = ["Camera %d" %(i) for i in list_ports()[1]] #etc
        self.camera_var = tk.StringVar(self.root)
        self.camera_var.set(camera_options[0]) # default value
        camera_dropdown = tk.OptionMenu(self.root, self.camera_var, *camera_options, command=self.on_camera_change)
        camera_dropdown.pack()
        
        # Feed de vídeo da webcam
        self.cap = cv2.VideoCapture(int(camera_options[0][-1]))  # Webcam padrão
        self.meanFrame:np.ndarray = np.array(0)
        self.frameBuffer:Deque[np.ndarray] = []
        
        # Iniciar a thread para atualizar o feed de vídeo
        self.detection_thread: threading.Thread = threading.Thread(target=self.detectionMain)
        self.video_thread: threading.Thread = threading.Thread(target=self.videoMain)
        self.serial_thread: threading.Thread = threading.Thread(target=self.serial.serialMain)

        self.detection_thread.start()
        self.serial_thread.start()
        self.video_thread.start()
        
        # Fechar janela com segurança
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_serial_change(self, value):
        print(value)
        if value != "":
            self.serial.open_serial(value)

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
    
    def videoMain(self):
        while self.running:
            startTime = time.time()
            ret, frame = self.cap.read()
            frame = center_crop(frame, (self.resolution.x, self.resolution.y))
            
            with MainWindow.frameLock:
                if len(self.frameBuffer) == 0:
                    self.frameBuffer = deque(frame[np.newaxis].repeat(10, 0))
                else:
                    self.frameBuffer.popleft()
                    self.frameBuffer.append(frame)

            if self.newArea.isValid():
                cv2.rectangle(frame, (self.newArea.x, self.newArea.y), (self.newArea.xx, self.newArea.yy), (0, 0, 0), -1)
 
            for area in self.removedAreas:
                cv2.rectangle(frame, (area.x, area.y), (area.xx, area.yy), (0, 0, 0), -1)

            drawBoxes(self.bboxes, frame)

            # Exibe o vídeo em uma janela do OpenCV
            imageFrame = self._arrayToImage(frame)
            self.canvas.create_image(0, 0, image=imageFrame, anchor="nw")
            self.canvas.image = imageFrame

            elapsedTime = time.time() - startTime
            if elapsedTime < 1/60:
                time.sleep(1/60 - elapsedTime)

            if MainWindow.closeEvent.isSet() or not self.running:
                MainWindow.processEvent.set()
                break

        self.root.quit()

    def detectionMain(self):
        """Atualiza o feed de vídeo com a elipse desenhada."""
        while self.running:
            MainWindow.processEvent.wait()
            # Encerra se a tecla 'q' for pressionada
            if MainWindow.closeEvent.isSet() or not self.running:
                return

            startTime = time.time()
            with MainWindow.frameLock:
                frame = np.mean(self.frameBuffer, axis=0).astype(np.uint8)
            
            if len(frame.shape) == 0:
                time.sleep(0.001)
                continue
            
            nms_thr = self.yoloController.threshold.get()
            output = self.detector.inference(frame, nms_thr)
            
            self.petri.setDishDiameter(self.petriController.diameter)
            _ = self.petri.segmentDish(frame)
            self.petri.findParameters()

            _, self.bboxes = getBboxes(
                output, 
                (self.resolution.x, self.resolution.y), 
                nms_thr, 
                self.removedAreas,
            )
            
            self.colonies = [
                Colony(
                    r, 
                    self.petri.getCentroid(), 
                    self.petri.getConversionFactor()
                ) 
                for r in self.bboxes
            ]
            self.serial.setPoints(self.colonies)

            elapsedTime = time.time() - startTime
            if elapsedTime < 1/30:
                time.sleep(1/30 - elapsedTime)
    
    def on_close(self):
        """Encerra o programa com segurança."""
        self.running = False
        MainWindow.closeEvent.set()
        MainWindow.processEvent.set()
        self.serial.closeEvent.set()

# Iniciar o programa
if __name__ == "__main__":
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()
    
    app.video_thread.join()
    app.serial_thread.join()
    app.detection_thread.join()
    app.cap.release()

    cv2.destroyAllWindows()
