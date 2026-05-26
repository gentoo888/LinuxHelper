import tkinter as tk
from tkinter import ttk
from theme import COLORS, FONTS, make_card


class WelcomeScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLORS["bg"])
        self.controller = controller

        # Outer padding container
        wrapper = tk.Frame(self, bg=COLORS["bg"])
        wrapper.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(wrapper, text="SelfLinux Recommender",
                 font=FONTS["title"], bg=COLORS["bg"], fg=COLORS["text"]).pack(pady=(0, 6))
        tk.Label(wrapper,
                 text="Find the right Linux distribution for your machine.",
                 font=FONTS["body"], bg=COLORS["bg"], fg=COLORS["text_muted"]).pack(pady=(0, 24))

        # Feature card
        outer, card = make_card(wrapper, padx=24, pady=20)
        outer.pack(pady=(0, 24))

        features = [
            ("Hardware analysis",
             "Detects CPU, GPU, RAM, storage, and battery to score your system."),
            ("Smart recommendations",
             "Ranks distros via a weighted match against your preferences."),
            ("Verified downloads",
             "Resolves the latest official ISO and verifies its SHA checksum."),
        ]
        for i, (title, desc) in enumerate(features):
            row = tk.Frame(card, bg=COLORS["surface"])
            row.pack(fill="x", pady=4)
            tk.Label(row, text="•", bg=COLORS["surface"], fg=COLORS["primary"],
                     font=("Segoe UI", 14, "bold")).pack(side="left", padx=(0, 8))
            txt_frame = tk.Frame(row, bg=COLORS["surface"])
            txt_frame.pack(side="left", fill="x", expand=True)
            tk.Label(txt_frame, text=title, bg=COLORS["surface"],
                     fg=COLORS["text"], font=FONTS["body_b"], anchor="w").pack(anchor="w")
            tk.Label(txt_frame, text=desc, bg=COLORS["surface"],
                     fg=COLORS["text_muted"], font=FONTS["small"], anchor="w",
                     wraplength=460, justify="left").pack(anchor="w")

        ttk.Button(wrapper, text="Get Started", style="Primary.TButton",
                   command=lambda: controller.show_frame("WarningScreen")).pack()
