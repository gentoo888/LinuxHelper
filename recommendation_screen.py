import os
import tkinter as tk
from tkinter import ttk

from theme import COLORS, FONTS, make_card
from recommender_engine import recommend


class RecommendationScreen(tk.Frame):
    """
    Score-based recommendation list with detail card.
    Shows hardware score + tier and a ranked list of distros.
    """
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLORS["bg"])
        self.controller = controller
        self.images = {}

        # Header
        header = tk.Frame(self, bg=COLORS["bg"])
        header.pack(fill="x", padx=40, pady=(20, 6))
        tk.Label(header, text="Your recommendations",
                 font=FONTS["title"], bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(anchor="w")
        self.subtitle = tk.Label(header, text="",
                                 font=FONTS["small"], bg=COLORS["bg"],
                                 fg=COLORS["text_muted"])
        self.subtitle.pack(anchor="w")

        # Body: left list + right details
        body = tk.Frame(self, bg=COLORS["bg"])
        body.pack(fill="both", expand=True, padx=40, pady=(8, 8))
        body.columnconfigure(0, weight=1, uniform="rec")
        body.columnconfigure(1, weight=1, uniform="rec")
        body.rowconfigure(0, weight=1)

        # Left: list of recommendations
        left_outer = tk.Frame(body, bg=COLORS["border"])
        left_outer.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left = tk.Frame(left_outer, bg=COLORS["surface"], padx=12, pady=12)
        left.pack(fill="both", expand=True, padx=1, pady=1)

        tk.Label(left, text="Top matches", font=FONTS["h2"],
                 bg=COLORS["surface"], fg=COLORS["text"]).pack(anchor="w")

        list_wrap = tk.Frame(left, bg=COLORS["surface"])
        list_wrap.pack(fill="both", expand=True, pady=(8, 0))
        canvas = tk.Canvas(list_wrap, bg=COLORS["surface"], highlightthickness=0)
        sb = ttk.Scrollbar(list_wrap, orient="vertical", command=canvas.yview)
        self.list_frame = tk.Frame(canvas, bg=COLORS["surface"])
        self.list_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.list_frame, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # Right: detail panel
        right_outer = tk.Frame(body, bg=COLORS["border"])
        right_outer.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        self.detail = tk.Frame(right_outer, bg=COLORS["surface"], padx=18, pady=16)
        self.detail.pack(fill="both", expand=True, padx=1, pady=1)
        self._render_detail_placeholder()

        # Footer
        footer = tk.Frame(self, bg=COLORS["bg"])
        footer.pack(fill="x", padx=40, pady=14)
        ttk.Button(footer, text="Back",
                   style="Secondary.TButton",
                   command=lambda: controller.show_frame("PreferencesScreen")
                   ).pack(side="left")

        self.recommendations = []
        self.selected_idx = 0

    def _render_detail_placeholder(self):
        for w in self.detail.winfo_children():
            w.destroy()
        tk.Label(self.detail, text="Select a distribution from the list",
                 font=FONTS["body"], bg=COLORS["surface"],
                 fg=COLORS["text_muted"]).pack(expand=True)

    def tkraise(self):
        super().tkraise()
        self._render()

    def _render(self):
        s = self.controller.state
        prefs = {
            "usage": s.get("usage") or "office",
            "visual": s.get("visual") or "no",
            "experience": s.get("experience") or "beginner",
            "update_pref": s.get("update_pref") or "balanced",
            "privacy": s.get("privacy") or "no",
            "free_software_only": s.get("free_software_only") or "no",
            "battery_priority": s.get("battery_priority") or "no",
            "windows_like": s.get("windows_like") or "no",
            "gaming_intensity": s.get("gaming_intensity") or "none",
            "desktop_pref": (s.get("desktop_pref") or "any").lower(),
        }
        result = recommend(s, prefs, top_n=8)
        self.recommendations = result["recommendations"]
        hw_score = result["hardware_score"]
        tier = result["tier"]
        self.subtitle.config(
            text=f"Hardware score: {hw_score}/100 ({tier.replace('_', ' ')})  ·  "
                 f"Showing top {len(self.recommendations)} matches."
        )

        # Clear list
        for w in self.list_frame.winfo_children():
            w.destroy()

        # Render list items
        if not self.recommendations:
            tk.Label(self.list_frame, text="No matches found.",
                     font=FONTS["body"], bg=COLORS["surface"],
                     fg=COLORS["text_muted"]).pack(pady=20)
            return

        max_score = self.recommendations[0]["score"] or 1.0
        for i, rec in enumerate(self.recommendations):
            self._render_item(rec, i, max_score)

        self._show_detail(0)

    def _render_item(self, rec, idx, max_score):
        item = tk.Frame(self.list_frame, bg=COLORS["surface"],
                        cursor="hand2", padx=10, pady=10)
        item.pack(fill="x", pady=2)
        sep = tk.Frame(self.list_frame, bg=COLORS["border"], height=1)
        sep.pack(fill="x")

        top = tk.Frame(item, bg=COLORS["surface"])
        top.pack(fill="x")
        tk.Label(top, text=f"{idx + 1}.", font=FONTS["body_b"],
                 bg=COLORS["surface"], fg=COLORS["text_muted"],
                 width=2, anchor="w").pack(side="left")
        tk.Label(top, text=rec["name"], font=FONTS["h2"],
                 bg=COLORS["surface"], fg=COLORS["text"]).pack(side="left", padx=(4, 0))

        # Score bar
        bar_outer = tk.Frame(item, bg=COLORS["surface"])
        bar_outer.pack(fill="x", pady=(6, 0))
        # Compute width fraction
        frac = max(0.05, min(1.0, rec["score"] / max_score))
        bar_bg = tk.Frame(bar_outer, bg="#e9ecf3", height=6)
        bar_bg.pack(fill="x")
        bar_bg.pack_propagate(False)

        def update_bar(b=bar_bg, f=frac):
            w = b.winfo_width()
            for c in b.winfo_children():
                c.destroy()
            fill = tk.Frame(b, bg=COLORS["primary"], height=6)
            fill.place(x=0, y=0, width=int(w * f), height=6)
        bar_bg.bind("<Configure>", lambda e: update_bar())

        tk.Label(item, text=rec["summary"], font=FONTS["small"],
                 bg=COLORS["surface"], fg=COLORS["text_muted"],
                 wraplength=320, justify="left", anchor="w").pack(fill="x", pady=(6, 0))

        # Click bindings
        def on_click(e=None, i=idx):
            self._show_detail(i)
        for w in (item, top, bar_outer):
            w.bind("<Button-1>", on_click)
        for child in top.winfo_children():
            child.bind("<Button-1>", on_click)

    def _show_detail(self, idx):
        if not (0 <= idx < len(self.recommendations)):
            return
        self.selected_idx = idx
        rec = self.recommendations[idx]

        for w in self.detail.winfo_children():
            w.destroy()

        tk.Label(self.detail, text=rec["name"], font=FONTS["title"],
                 bg=COLORS["surface"], fg=COLORS["text"]).pack(anchor="w")
        tk.Label(self.detail, text=f"Match score: {rec['score']:.1f}",
                 font=FONTS["small"], bg=COLORS["surface"],
                 fg=COLORS["text_muted"]).pack(anchor="w", pady=(2, 12))

        tk.Label(self.detail, text=rec["summary"], font=FONTS["body"],
                 bg=COLORS["surface"], fg=COLORS["text"],
                 wraplength=380, justify="left", anchor="w").pack(anchor="w", pady=(0, 12))

        # Details list
        details_frame = tk.Frame(self.detail, bg=COLORS["surface"])
        details_frame.pack(fill="x")
        rows = [
            ("Desktop", rec.get("desktop", "—")),
            ("Package manager", rec.get("package_mgr", "—")),
            ("Minimum RAM", f"{rec.get('min_ram_gb', 0)} GB"),
            ("Recommended RAM", f"{rec.get('ideal_ram_gb', 0)} GB"),
        ]
        for k, v in rows:
            r = tk.Frame(details_frame, bg=COLORS["surface"])
            r.pack(fill="x", pady=1)
            tk.Label(r, text=k, font=FONTS["small"], bg=COLORS["surface"],
                     fg=COLORS["text_muted"], width=18, anchor="w").pack(side="left")
            tk.Label(r, text=v, font=FONTS["body"], bg=COLORS["surface"],
                     fg=COLORS["text"], anchor="w").pack(side="left")

        # Why this distro
        if rec.get("reasons"):
            tk.Label(self.detail, text="Why this match",
                     font=FONTS["body_b"], bg=COLORS["surface"],
                     fg=COLORS["text"]).pack(anchor="w", pady=(14, 4))
            for r in rec["reasons"][:5]:
                tk.Label(self.detail, text=f"  •  {r}", font=FONTS["small"],
                         bg=COLORS["surface"], fg=COLORS["text"],
                         anchor="w").pack(anchor="w")

        # Action buttons
        btn_frame = tk.Frame(self.detail, bg=COLORS["surface"])
        btn_frame.pack(fill="x", pady=(18, 0))
        ttk.Button(btn_frame, text="Download & Install",
                   style="Primary.TButton",
                   command=lambda n=rec["name"]: self.controller.write_distro_to_usb(n)
                   ).pack(side="left")
