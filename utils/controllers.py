import tkinter as tk

from argparse import Namespace
from .ui import Controls


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


class PetriDishController(Controls):
    def __init__(self, root=None):
        self._diameter = tk.IntVar(value=88)
        self._valueList = [50 + i for i in range(110)]

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


class ExclusionController(Controls):
    def __init__(self, root):
        super().__init__(root)

    def placeControls(self):
        return super().placeControls()
    

class SerialController(Controls):
    def __init__(self, root, options, on_serial_change, name):
        self.on_serial_change = on_serial_change

        self.serial_var = tk.StringVar(root)
        self.options = options
        
        if len(self.options) != 0:
            self.serial_var.set(self.options[0]) # default value
        else:
            self.serial_var.set("") # default value
            self.options = [""]

        self.label_name = name
        super().__init__(root)
    
    def placeControls(self):
        tk.Label(self.controls_frame, text=self.label_name + ":").pack()

        serial_dropdown = tk.OptionMenu(self.root, self.serial_var, *self.options, command=self.on_serial_change)
        serial_dropdown.pack(side="left")