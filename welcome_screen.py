# I mean let's greet the user first. Manners first :D

import tkinter as tk

class WelcomeScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        tk.Label(self, text="Welcome to SelfLinux Recommender!", font=("Arial", 20)).pack(pady=50)

        tk.Button(
            self,
            text="Start",
            font=("Arial", 14),
            command=lambda: controller.show_frame("WarningScreen")
        ).pack()

