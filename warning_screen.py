# This code is responsible for showing the warning screen about the risks and information for using SelfLinux. And it's important as main.py is! :D

import tkinter as tk

class WarningScreen(tk.Frame):
    """
    Warning screen about the risks and information for using SelfLinux.
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Title
        tk.Label(
            self,
            text="WARNING",
            font=("Arial", 20),
            fg="red"
        ).pack(pady=(12, 8))

        # General Warning text
        tk.Label(
            self,
            text=(
                "SelfLinux is currently an experimental project. It may cause data loss or system instability.\n\n"
                "What SelfLinux does is extract a preferred Linux distribution's ISO to the USB you provide.\n"
                "It recommends a distribution by scanning your hardware and categorizing the specs.\n"
                "It also asks you a few basic questions to make a better recommendation.\n\n"
                "If you are new to Linux, SelfLinux strongly recommends that you do a quick research first.\n"
                "SelfLinux is an open-source project that anyone can develop or modify. However, the developer "
                "of SelfLinux is not responsible for any malware added by others.\n"
                "If SelfLinux gives error about library loss, you need to install the required libraries. \n"
                "Check SelfLinux's Github site for installation and using steps.\n\n"
            ),
            font=("Arial", 11),
            justify="center",
            wraplength=760
        ).pack(pady=(0, 12))

        # Critical Warning (red text)
        tk.Label(
            self,
            text=(
                "IMPORTANT:\n"
                "DON'T give SelfLinux the 'C' drive letter when selecting a USB!\n"
                "The 'C' drive is usually reserved for your main hard drive.\n"
                "If you select it, SelfLinux will overwrite your system and you will lose ALL your data!"
            ),
            font=("Arial", 11, "bold"),
            fg="red",
            justify="center",
            wraplength=760
        ).pack(pady=(0, 12))
        tk.Label(
            self,
            text=(
                "Do you agree with this warning and want to proceed?"
            ),
            font=("Arial", 11, "bold"),
            justify="center",
            wraplength=760
        ).pack(pady=(0, 12))
        tk.Button(
            self,
            # Yippee we going forward :D
            text="I read the warning and agree. Proceed.",
            command=lambda: controller.show_frame("HardwareScreen")
        ).pack(pady=(0, 12))
        tk.Button(
            self,
            # Oh boi we going down the exit route ;(
            text="I do NOT agree. Exit SelfLinux.",
            command=controller.quit
        ).pack(pady=(0, 12))
