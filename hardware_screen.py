import tkinter as tk

class HardwareScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        tk.Label(self, text="Hardware Scan", font=("Arial", 20)).pack(pady=20)

        # Info space
        self.info_label = tk.Label(self, text="Scanning hardware...", font=("Arial", 14), justify="left")
        self.info_label.pack(pady=10)

        # Rescan buttons
        btns = tk.Frame(self)
        btns.pack(pady=(0, 10))
        tk.Button(btns, text="Re-scan RAM",     command=self._rescan_ram).pack(side="left", padx=4)
        tk.Button(btns, text="Re-scan CPU",     command=self._rescan_cpu).pack(side="left", padx=4)   # <-- EK
        tk.Button(btns, text="Re-scan GPU",     command=self._rescan_gpu).pack(side="left", padx=4)
        tk.Button(btns, text="Re-scan Storage", command=self._rescan_storage).pack(side="left", padx=4)

        # Next button
        tk.Button(
            self,
            text="Next",
            font=("Arial", 14),
            command=lambda: controller.show_frame("PreferencesScreen")
        ).pack(pady=10)

        self.after(300, self._tick)

    def _tick(self):
        s = self.controller.state

        # RAM
        if s.get("ram_total_gb") is not None:
            ram_txt = (
                f"RAM total : {s['ram_total_gb']} GB\n"
                f"RAM free  : {s['ram_avail_gb']} GB\n"
                f"Used      : {s['ram_used_percent']}%\n"
                f"Category  : {s.get('ram_cat') or '?'}"
            )
        else:
            ram_txt = "RAM: scanning…"

        # CPU  
        if s.get("cpu_model") is not None or s.get("max_ghz") is not None:
            cpu_model = s.get("cpu_model") or "Unknown"
            cpu_cat   = s.get("cpu_cat")   or "?"
            max_ghz   = s.get("max_ghz")
            cores     = s.get("cores")
            threads   = s.get("threads")
            # None control
            max_ghz_str = f"{max_ghz} GHz" if isinstance(max_ghz, (int, float)) else "Unknown"
            ct_str      = f"{cores}C/{threads}T" if (cores and threads) else "?"
            cpu_txt = (
                f"CPU model : {cpu_model}\n"
                f"CPU spec  : {max_ghz_str} • {ct_str}\n"
                f"CPU Cat   : {cpu_cat}"
            )
        else:
            cpu_txt = "CPU: scanning…"

        # GPU
        gpu_name = s.get("gpu_name") or "Unknown"
        gpu_cat  = s.get("gpu_cat")  or "?"
        gpu_txt  = f"GPU       : {gpu_name}\nGPU Cat   : {gpu_cat}"

        # Storage
        st_name = s.get("storage_type") or "Unknown"
        st_cat  = s.get("storage_cat")  or "?"
        storage_txt = f"Storage   : {st_name}\nStorage Cat: {st_cat}"

        # LABEL — SUMMARIZE ALL
        self.info_label.config(text = ram_txt + "\n\n" + cpu_txt + "\n\n" + gpu_txt + "\n\n" + storage_txt)

        self.after(600, self._tick)

    # --- rescan buttons ---
    def _rescan_ram(self):
        self.controller.refresh_ram_async()

    def _rescan_cpu(self):   
        # fast feedback. We don't want the user to think the app is frozen :D
        self.info_label.config(text="CPU: scanning…")
        self.controller.refresh_cpu_async(on_done=self._tick)

    def _rescan_gpu(self):
        self.controller.refresh_gpu_async()

    def _rescan_storage(self):
        self.controller.refresh_storage_async()

