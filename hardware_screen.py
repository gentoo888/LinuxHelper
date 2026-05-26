import tkinter as tk
from tkinter import ttk
from theme import COLORS, FONTS, make_card


class HardwareScreen(tk.Frame):
    """
    Card-based hardware overview with a computed hardware score.
    """
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLORS["bg"])
        self.controller = controller

        # Header
        header = tk.Frame(self, bg=COLORS["bg"])
        header.pack(fill="x", padx=40, pady=(20, 8))
        tk.Label(header, text="Hardware overview", font=FONTS["title"],
                 bg=COLORS["bg"], fg=COLORS["text"]).pack(anchor="w")
        tk.Label(header, text="Detected components and their evaluation.",
                 font=FONTS["small"], bg=COLORS["bg"],
                 fg=COLORS["text_muted"]).pack(anchor="w")

        # Score banner
        score_outer = tk.Frame(self, bg=COLORS["border"])
        score_outer.pack(fill="x", padx=40, pady=(8, 8))
        self.score_card = tk.Frame(score_outer, bg=COLORS["surface"], padx=18, pady=14)
        self.score_card.pack(fill="x", padx=1, pady=1)

        self.score_lbl = tk.Label(self.score_card, text="Hardware score: …",
                                  font=FONTS["h1"], bg=COLORS["surface"],
                                  fg=COLORS["text"], anchor="w")
        self.score_lbl.pack(fill="x")
        self.tier_lbl = tk.Label(self.score_card, text="",
                                 font=FONTS["small"], bg=COLORS["surface"],
                                 fg=COLORS["text_muted"], anchor="w")
        self.tier_lbl.pack(fill="x", pady=(2, 4))
        self.score_bar = ttk.Progressbar(self.score_card, mode="determinate",
                                         maximum=100, length=400)
        self.score_bar.pack(fill="x")

        # Cards container (2x2 grid)
        cards_wrap = tk.Frame(self, bg=COLORS["bg"])
        cards_wrap.pack(fill="both", expand=True, padx=40, pady=8)
        for i in range(2):
            cards_wrap.columnconfigure(i, weight=1, uniform="hw")
            cards_wrap.rowconfigure(i, weight=1)

        self.cpu_card = self._create_card(cards_wrap, "CPU", 0, 0)
        self.ram_card = self._create_card(cards_wrap, "Memory", 0, 1)
        self.gpu_card = self._create_card(cards_wrap, "Graphics", 1, 0)
        self.storage_card = self._create_card(cards_wrap, "Storage", 1, 1)

        # Footer
        footer = tk.Frame(self, bg=COLORS["bg"])
        footer.pack(fill="x", padx=40, pady=(0, 18))
        ttk.Button(footer, text="Re-scan", style="Secondary.TButton",
                   command=self._rescan_all).pack(side="left")
        ttk.Button(footer, text="Continue", style="Primary.TButton",
                   command=lambda: controller.show_frame("PreferencesScreen")).pack(side="right")

        self.after(300, self._tick)

    def _create_card(self, parent, title, row, col):
        outer = tk.Frame(parent, bg=COLORS["border"])
        outer.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)
        card = tk.Frame(outer, bg=COLORS["surface"], padx=16, pady=12)
        card.pack(fill="both", expand=True, padx=1, pady=1)
        tk.Label(card, text=title, font=FONTS["h2"], bg=COLORS["surface"],
                 fg=COLORS["text"]).pack(anchor="w")
        body = tk.Label(card, text="Scanning…", font=FONTS["body"],
                        bg=COLORS["surface"], fg=COLORS["text"],
                        justify="left", anchor="w", wraplength=300)
        body.pack(anchor="w", fill="x", pady=(6, 0))
        cat = tk.Label(card, text="", font=FONTS["small"],
                       bg=COLORS["surface"], fg=COLORS["text_muted"], anchor="w")
        cat.pack(anchor="w", pady=(8, 0))
        return {"outer": outer, "card": card, "body": body, "cat": cat}

    def _tick(self):
        s = self.controller.state

        # CPU
        if s.get("cpu_model"):
            cpu_text = (
                f"{s.get('cpu_model')}\n"
                f"{s.get('cores') or '?'} cores / {s.get('threads') or '?'} threads · "
                f"{s.get('max_ghz') or 0} GHz max"
            )
            self.cpu_card["body"].config(text=cpu_text)
            score = s.get("cpu_score") or 0
            cat = s.get("cpu_cat") or "?"
            gen = s.get("cpu_gen") or ""
            sub = f"Category: {cat}  ·  Score: {score}/100"
            if gen:
                sub += f"  ·  {gen}"
            self.cpu_card["cat"].config(text=sub)
        else:
            self.cpu_card["body"].config(text="Scanning…")

        # RAM
        if s.get("ram_total_gb") is not None:
            extra = ""
            if s.get("ram_speed_mhz"):
                extra = f" · {s['ram_speed_mhz']} MHz"
            if s.get("ram_type") and s["ram_type"] != "Unknown":
                extra = f" · {s['ram_type']}{extra}"
            self.ram_card["body"].config(
                text=(f"{s['ram_total_gb']} GB total{extra}\n"
                      f"{s['ram_avail_gb']} GB free  ·  {s['ram_used_percent']}% used")
            )
            self.ram_card["cat"].config(text=f"Category: {s.get('ram_cat') or '?'}")
        else:
            self.ram_card["body"].config(text="Scanning…")

        # GPU
        gpu_name = s.get("gpu_name") or "No discrete GPU detected"
        gpu_cat = s.get("gpu_cat") or "?"
        vram = s.get("gpu_vram_mb") or 0
        body = gpu_name
        if vram:
            body += f"\nVRAM: {vram} MB"
        self.gpu_card["body"].config(text=body)
        self.gpu_card["cat"].config(text=f"Category: {gpu_cat}")

        # Storage
        st_name = s.get("storage_type") or "Unknown"
        st_cat = s.get("storage_cat") or "?"
        size = s.get("storage_size_gb") or 0
        free = s.get("storage_free_gb") or 0
        body = f"{st_name}\n"
        if size:
            body += f"Size: {size} GB"
            if free:
                body += f"  ·  Free: {free} GB"
        self.storage_card["body"].config(text=body)
        self.storage_card["cat"].config(text=f"Category: {st_cat}")

        # Battery hint (append to RAM card or as small text)
        if s.get("has_battery"):
            self.ram_card["cat"].config(
                text=(self.ram_card["cat"].cget("text") +
                      f"  ·  Battery: {s.get('battery_percent', 0):.0f}%"
                      f"{' (charging)' if s.get('battery_plugged') else ''}")
            )

        # Update overall score
        try:
            from recommender_engine import compute_hardware_score, hardware_tier
            score = compute_hardware_score(s)
            tier = hardware_tier(score)
            self.score_lbl.config(text=f"Overall hardware score: {score}/100")
            tier_text = {
                "very_low": "Very low — only the lightest distributions will be comfortable.",
                "low": "Low — lightweight distributions recommended.",
                "mid_low": "Below average — works well with efficient desktops.",
                "mid": "Average — most distributions will run smoothly.",
                "mid_high": "Above average — handles modern desktops and most games.",
                "high": "High — runs anything, including demanding workloads.",
                "ultra": "Ultra — top-tier hardware, no compromises.",
            }.get(tier, "")
            self.tier_lbl.config(text=tier_text)
            self.score_bar["value"] = score
        except Exception:
            pass

        self.after(800, self._tick)

    def _rescan_all(self):
        self.controller.refresh_ram_async()
        self.controller.refresh_cpu_async()
        self.controller.refresh_gpu_async()
        self.controller.refresh_storage_async()
        self.controller.refresh_battery_async()
