import tkinter as tk

from abc import abstractmethod

class Controls:
    def __init__(self, root):
        self.root = root

        self.controls_frame = tk.Frame(self.root)
        self.controls_frame.pack(side=tk.LEFT, padx=10)

    @abstractmethod
    def placeControls(self) -> None:
        pass