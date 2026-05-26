import tkinter as tk
from tkinter import ttk
from theme import COLORS, FONTS, make_card


class WarningScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLORS["bg"])
        self.controller = controller

        wrapper = tk.Frame(self, bg=COLORS["bg"])
        wrapper.pack(fill="both", expand=True, padx=40, pady=24)

        tk.Label(wrapper, text="Important Information",
                 font=FONTS["title"], bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(anchor="w", pady=(0, 16))

        # General info card
        outer, card = make_card(wrapper, padx=20, pady=16)
        outer.pack(fill="x", pady=(0, 12))

        tk.Label(card, text="What this tool does",
                 font=FONTS["h2"], bg=COLORS["surface"],
                 fg=COLORS["text"]).pack(anchor="w")
        tk.Label(card,
                 text=("SelfLinux scans your hardware and asks a few questions to "
                       "recommend Linux distributions. After choosing one, it can "
                       "download the official ISO, verify its checksum, and write "
                       "it to a USB drive."),
                 font=FONTS["body"], bg=COLORS["surface"],
                 fg=COLORS["text"], wraplength=680, justify="left").pack(anchor="w", pady=(4, 0))

        # Critical warning card (subtle red border)
        warn_outer = tk.Frame(wrapper, bg=COLORS["danger"])
        warn_card = tk.Frame(warn_outer, bg=COLORS["danger_bg"], padx=20, pady=16)
        warn_card.pack(fill="both", padx=1, pady=1)
        warn_outer.pack(fill="x", pady=(0, 12))

        tk.Label(warn_card, text="⚠  Data loss warning",
                 font=FONTS["h2"], bg=COLORS["danger_bg"],
                 fg=COLORS["danger"]).pack(anchor="w")
        tk.Label(warn_card,
                 text=("Writing an ISO to a USB drive will erase ALL data on it. "
                       "Never select your system drive (typically C:). "
                       "Double-check the device before confirming. The developer of "
                       "SelfLinux is not responsible for accidental data loss."),
                 font=FONTS["body"], bg=COLORS["danger_bg"],
                 fg=COLORS["text"], wraplength=680, justify="left").pack(anchor="w", pady=(4, 0))

        # Buttons
        btns = tk.Frame(wrapper, bg=COLORS["bg"])
        btns.pack(fill="x", pady=(8, 0))
        ttk.Button(btns, text="I understand — continue",
                   style="Primary.TButton",
                   command=lambda: controller.show_frame("HardwareScreen")).pack(side="left")
        ttk.Button(btns, text="Cancel",
                   style="Secondary.TButton",
                   command=controller.quit).pack(side="left", padx=8)
