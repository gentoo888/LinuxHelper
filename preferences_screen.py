import tkinter as tk
from tkinter import ttk
from theme import COLORS, FONTS, make_card


# Question definitions - displayed in a vertical scrollable list
QUESTIONS = [
    {
        "key": "usage",
        "label": "What's your primary use case?",
        "type": "radio",
        "options": [
            ("office", "Office & general productivity"),
            ("development", "Software development"),
            ("gaming", "Gaming"),
            ("creative", "Creative work (video, music, design)"),
        ],
        "default": "office",
    },
    {
        "key": "experience",
        "label": "How experienced are you with Linux?",
        "type": "radio",
        "options": [
            ("beginner", "Beginner — first time or just curious"),
            ("intermediate", "Intermediate — used Linux before"),
            ("advanced", "Advanced — comfortable with terminals and configs"),
        ],
        "default": "beginner",
    },
    {
        "key": "visual",
        "label": "Is a polished visual design important to you?",
        "type": "radio",
        "options": [
            ("yes", "Yes, I value how it looks"),
            ("no", "No, performance over appearance"),
        ],
        "default": "no",
    },
    {
        "key": "windows_like",
        "label": "Do you want a Windows-like interface?",
        "type": "radio",
        "options": [
            ("yes", "Yes, similar to Windows"),
            ("no", "No, I'm open to anything"),
        ],
        "default": "no",
    },
    {
        "key": "update_pref",
        "label": "How do you prefer software updates?",
        "type": "radio",
        "options": [
            ("stable", "Stable — fewer updates, no surprises"),
            ("balanced", "Balanced — modern, but tested"),
            ("cutting_edge", "Cutting-edge — always the latest"),
        ],
        "default": "balanced",
    },
    {
        "key": "gaming_intensity",
        "label": "How serious is your gaming?",
        "type": "radio",
        "options": [
            ("none", "I don't game"),
            ("casual", "Casual / indie / older titles"),
            ("serious", "Modern AAA titles, regularly"),
        ],
        "default": "none",
    },
    {
        "key": "battery_priority",
        "label": "Is battery efficiency a priority? (laptops)",
        "type": "radio",
        "options": [
            ("yes", "Yes, I care about battery life"),
            ("no", "No / I use a desktop"),
        ],
        "default": "no",
    },
    {
        "key": "privacy",
        "label": "Is privacy and minimal telemetry important?",
        "type": "radio",
        "options": [
            ("yes", "Yes, I prefer privacy-respecting distros"),
            ("no", "Not particularly"),
        ],
        "default": "no",
    },
    {
        "key": "free_software_only",
        "label": "Do you want a fully-free-software experience?",
        "type": "radio",
        "options": [
            ("yes", "Yes, prefer no proprietary blobs"),
            ("no", "No, proprietary drivers/codecs are fine"),
        ],
        "default": "no",
    },
    {
        "key": "desktop_pref",
        "label": "Preferred desktop environment (optional)",
        "type": "combo",
        "options": ["any", "GNOME", "KDE", "Cinnamon", "XFCE", "LXQt", "Pantheon"],
        "default": "any",
    },
]


class PreferencesScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLORS["bg"])
        self.controller = controller
        self.vars = {}

        # Header
        header = tk.Frame(self, bg=COLORS["bg"])
        header.pack(fill="x", padx=40, pady=(20, 6))
        tk.Label(header, text="Tell us a bit about yourself",
                 font=FONTS["title"], bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(anchor="w")
        tk.Label(header, text="The more we know, the better the recommendation.",
                 font=FONTS["small"], bg=COLORS["bg"],
                 fg=COLORS["text_muted"]).pack(anchor="w")

        # Scrollable area
        scroll_outer = tk.Frame(self, bg=COLORS["bg"])
        scroll_outer.pack(fill="both", expand=True, padx=40, pady=(8, 0))

        canvas = tk.Canvas(scroll_outer, bg=COLORS["bg"], highlightthickness=0, width=820)
        scrollbar = ttk.Scrollbar(scroll_outer, orient="vertical", command=canvas.yview)
        self.inner = tk.Frame(canvas, bg=COLORS["bg"])
        self.inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        self._canvas_window = canvas.create_window((0, 0), window=self.inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Make inner frame stretch to canvas width
        def _on_canvas_resize(e, c=canvas):
            c.itemconfig(self._canvas_window, width=e.width)
        canvas.bind("<Configure>", _on_canvas_resize)
        # Initial expand
        self.after(50, lambda: canvas.itemconfig(self._canvas_window, width=canvas.winfo_width()))

        # Mouse wheel scroll (cross-platform)
        def _on_mw(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mw)

        # Build questions
        for q in QUESTIONS:
            self._render_question(q)

        # Warning label
        self.warn = tk.Label(self, text="", fg=COLORS["danger"],
                             bg=COLORS["bg"], font=FONTS["small"])
        self.warn.pack(anchor="w", padx=40)

        # Footer
        footer = tk.Frame(self, bg=COLORS["bg"])
        footer.pack(fill="x", padx=40, pady=14)
        ttk.Button(footer, text="Back", style="Secondary.TButton",
                   command=lambda: controller.show_frame("HardwareScreen")).pack(side="left")
        ttk.Button(footer, text="Show recommendations", style="Primary.TButton",
                   command=self._on_next).pack(side="right")

    def _render_question(self, q):
        # Card
        outer, card = make_card(self.inner, padx=18, pady=12)
        outer.pack(fill="x", pady=6)

        tk.Label(card, text=q["label"], font=FONTS["body_b"],
                 bg=COLORS["surface"], fg=COLORS["text"],
                 anchor="w", wraplength=620, justify="left").pack(anchor="w", pady=(0, 6))

        var = tk.StringVar(value=q.get("default", ""))
        self.vars[q["key"]] = var

        if q["type"] == "radio":
            for value, text in q["options"]:
                rb = tk.Radiobutton(card, text=text, value=value, variable=var,
                                    bg=COLORS["surface"], fg=COLORS["text"],
                                    activebackground=COLORS["surface"],
                                    selectcolor=COLORS["surface"],
                                    font=FONTS["body"], anchor="w",
                                    highlightthickness=0)
                rb.pack(anchor="w", pady=1)
        elif q["type"] == "combo":
            cb = ttk.Combobox(card, textvariable=var, values=q["options"],
                              state="readonly", width=24)
            cb.pack(anchor="w")

    def _on_next(self):
        prefs = {k: v.get() for k, v in self.vars.items()}
        # Sanity: usage and visual must be set
        if not prefs.get("usage"):
            self.warn.config(text="Please answer the primary use case question.")
            return
        self.warn.config(text="")
        # Save into state
        for k, v in prefs.items():
            self.controller.state[k] = v
        self.controller.show_frame("RecommendationScreen")
