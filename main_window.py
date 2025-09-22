# Okay this part is probably not needed because we already got the main.py file, but whatever. Just in case.
import tkinter as tk
from ui.gui.welcome_screen import WelcomeScreen
from ui.gui.hardware_screen import HardwareScreen
from ui.gui.preferences_screen import PreferencesScreen
from ui.gui.recommendation_screen import RecommendationScreen

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("SelfLinux Recommender")
        self.geometry("800x500")

        self.frames = {}

        screens = [WelcomeScreen, HardwareScreen, PreferencesScreen, RecommendationScreen]
        for ScreenClass in screens:
            frame = ScreenClass(parent=self, controller=self)
            self.frames[ScreenClass.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("WelcomeScreen")

    def show_frame(self, name):
        frame = self.frames[name]
        frame.tkraise()

