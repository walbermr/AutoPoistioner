import cv2
import time
import numpy as np
import tkinter as tk
from collections import OrderedDict
from argparse import Namespace

from utils.ui import Controls

from traditional.watershed import WaterShed

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


class PetriDish(Controls):
    def __init__(self, root=None):
        self.diameter = tk.IntVar(value=10)

        super().__init__(root)

    def placeControls(self):
        tk.Label(self.controls_frame, text="Diâmetro da placa (mm):").pack()
        tk.Scale(
            self.controls_frame, 
            from_=5, 
            to=15, orient="horizontal", 
            variable=self.diameter,
            length=200
        ).pack()


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
    

class EllipseDrawer:
    closeEvent = threading.Event()

    def __init__(self, root):
        self.root = root
        self.root.title("Desenhando Elipse no Feed de Vídeo")
        self.resolution = Namespace(x=640, y=480)
        
        # Variáveis para os parâmetros da elipse
        # self.petriEllipse = EllipseController(self.resolution, root=self.root)
        self.petriController = PetriDish(root=self.root)
        self.frameController = FrameController(self.resolution.y, self.resolution.x, root=self.root)
        self.waterShed = WaterShed(self.root)

        # Interface gráfica
        # self.petriEllipse.placeControls()
        self.frameController.placeControls()
        self.petriController.placeControls()
        self.waterShed.placeControls()
        
        # Feed de vídeo da webcam
        self.cap = cv2.VideoCapture(0)  # Webcam padrão
        self.running = True
        
        # Iniciar a thread para atualizar o feed de vídeo
        self.video_thread = threading.Thread(target=self.updateVideoFeed)
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
            ret, frame = self.cap.read()

            frame = cv2.imread("./images/2019-06-25_02365_nocover.jpg")
            frame = cv2.resize(frame, (self.resolution.x, self.resolution.y))
            frame = frame[
                self.frameController.yTop:self.frameController.yDown,
                self.frameController.xLeft:self.frameController.xRight
            ]
            if not ret:
                continue
            
            # Parâmetros da elipse
            # center = (self.petriEllipse.centerX.get(), self.petriEllipse.centerY.get())
            # axes = (self.petriEllipse.axisX.get(), self.petriEllipse.axisY.get())
            # angle = self.petriEllipse.angle.get()
            
            # thickness = self.petriEllipse.thickness.get()

            # if DEBUG:
            #     frame = self.displayDebug(frame, varDict=self.getDebugVariables())
            
            # Desenha a elipse no quadro
            # cv2.ellipse(frame, center, axes, angle, 0, 360, (0, 255, 0), thickness)

            frame, _ = self.waterShed.process(frame)
            
            # Exibe o vídeo em uma janela do OpenCV
            cv2.imshow("Detection", frame)

            ellapsedTime = time.time() - startTime
            if ellapsedTime < 1/30:
                time.sleep(1/30 - ellapsedTime)
            
            # Encerra se a tecla 'q' for pressionada
            if EllipseDrawer.closeEvent.isSet() or cv2.waitKey(1) & 0xFF == ord('q'):
                self.running = False
                EllipseDrawer.closeEvent.clear()
                cv2.destroyAllWindows()
                # self.on_close()
                return
    
    def on_close(self):
        """Encerra o programa com segurança."""
        self.running = False
        EllipseDrawer.closeEvent.set()
        self.cap.release()

        self.root.destroy()

# Iniciar o programa
if __name__ == "__main__":
    root = tk.Tk()
    app = EllipseDrawer(root)
    root.mainloop()
