# theme.py
# Centralized, minimal, clean theme. No animations, no glow effects.

import tkinter as tk
from tkinter import ttk

# Color palette (light, neutral)
COLORS = {
    "bg":         "#f5f6fa",
    "surface":    "#ffffff",
    "border":     "#dde2eb",
    "text":       "#1f2d3d",
    "text_muted": "#5a6477",
    "primary":    "#2563eb",   # blue
    "primary_hover": "#1e4fd1",
    "primary_text":  "#ffffff",
    "success":    "#1b6e2c",
    "warn":       "#7a5b00",
    "danger":     "#b00020",
    "danger_bg":  "#fdecef",
    "warn_bg":    "#fff7e0",
    "info_bg":    "#e8f0fe",
    "card_shadow":"#e6e9f0",
}

FONTS = {
    "title":    ("Segoe UI", 20, "bold"),
    "h1":       ("Segoe UI", 16, "bold"),
    "h2":       ("Segoe UI", 13, "bold"),
    "body":     ("Segoe UI", 10),
    "body_b":   ("Segoe UI", 10, "bold"),
    "small":    ("Segoe UI", 9),
    "mono":     ("Consolas", 9),
    "btn":      ("Segoe UI", 10, "bold"),
}


def apply_theme(root: tk.Tk):
    """Apply consistent theme to ttk widgets and root."""
    root.configure(bg=COLORS["bg"])
    style = ttk.Style(root)
    # Use a neutral built-in theme as base
    try:
        style.theme_use("clam")
    except Exception:
        pass

    style.configure("TFrame", background=COLORS["bg"])
    style.configure("Card.TFrame", background=COLORS["surface"], borderwidth=1, relief="solid")
    style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["text"], font=FONTS["body"])
    style.configure("Title.TLabel", font=FONTS["title"], foreground=COLORS["text"], background=COLORS["bg"])
    style.configure("H1.TLabel", font=FONTS["h1"], foreground=COLORS["text"], background=COLORS["bg"])
    style.configure("H2.TLabel", font=FONTS["h2"], foreground=COLORS["text"], background=COLORS["bg"])
    style.configure("Muted.TLabel", foreground=COLORS["text_muted"], background=COLORS["bg"], font=FONTS["small"])
    style.configure("CardTitle.TLabel", font=FONTS["h2"], background=COLORS["surface"], foreground=COLORS["text"])
    style.configure("CardBody.TLabel", font=FONTS["body"], background=COLORS["surface"], foreground=COLORS["text"])
    style.configure("CardMuted.TLabel", font=FONTS["small"], background=COLORS["surface"], foreground=COLORS["text_muted"])

    # Buttons
    style.configure(
        "Primary.TButton",
        background=COLORS["primary"],
        foreground=COLORS["primary_text"],
        font=FONTS["btn"],
        borderwidth=0,
        focuscolor=COLORS["primary"],
        padding=(14, 8),
    )
    style.map("Primary.TButton",
              background=[("active", COLORS["primary_hover"]), ("disabled", "#9ab0e6")],
              foreground=[("disabled", "#eaeaea")])

    style.configure(
        "Secondary.TButton",
        background=COLORS["surface"],
        foreground=COLORS["text"],
        font=FONTS["btn"],
        borderwidth=1,
        bordercolor=COLORS["border"],
        padding=(12, 7),
        relief="flat",
    )
    style.map("Secondary.TButton",
              background=[("active", "#eef1f7")])

    style.configure(
        "Danger.TButton",
        background=COLORS["danger"],
        foreground="#ffffff",
        font=FONTS["btn"],
        borderwidth=0,
        padding=(12, 7),
    )
    style.map("Danger.TButton", background=[("active", "#8a0017")])

    style.configure("TProgressbar",
                    troughcolor="#e9ecf3",
                    background=COLORS["primary"],
                    bordercolor=COLORS["border"],
                    lightcolor=COLORS["primary"],
                    darkcolor=COLORS["primary"])

    style.configure("Card.TLabelframe",
                    background=COLORS["surface"],
                    foreground=COLORS["text"],
                    relief="solid",
                    borderwidth=1)
    style.configure("Card.TLabelframe.Label",
                    background=COLORS["surface"],
                    foreground=COLORS["text"],
                    font=FONTS["h2"])

    style.configure("TRadiobutton", background=COLORS["bg"], foreground=COLORS["text"], font=FONTS["body"])
    style.configure("TCheckbutton", background=COLORS["bg"], foreground=COLORS["text"], font=FONTS["body"])
    style.configure("TCombobox", fieldbackground=COLORS["surface"], background=COLORS["surface"])
    style.configure("TEntry", fieldbackground=COLORS["surface"])


def make_card(parent, padx=14, pady=12, bg=None):
    """Create a simple card frame (white surface with thin border)."""
    bg = bg or COLORS["surface"]
    outer = tk.Frame(parent, bg=COLORS["border"])
    inner = tk.Frame(outer, bg=bg, padx=padx, pady=pady)
    inner.pack(fill="both", expand=True, padx=1, pady=1)
    return outer, inner


def section_header(parent, text):
    lbl = tk.Label(parent, text=text, font=FONTS["h1"],
                   bg=COLORS["bg"], fg=COLORS["text"])
    return lbl
