# LinuxHelper is back with it's updated version! This version has a much better gui, sha verification, url resolving (instead of downloading iso from my google drive lmao) and much more!

import os
import platform
import shutil
import subprocess
import sys
import threading
import time
import tkinter as tk
import urllib.error
import urllib.request
from tkinter import filedialog, messagebox, ttk

from battery_probe import probe_battery
from cpu_probe import probe_cpu
from gpu_probe import probe_gpu
from hardware_screen import HardwareScreen
from iso_resolver import resolve_iso
from preferences_screen import PreferencesScreen
from ram_probe import probe_ram
from recommendation_screen import RecommendationScreen
from sha_verify import ShaVerifyDialog, fetch_expected_hash
from storage_probe import probe_storage_type
from theme import COLORS, FONTS, apply_theme
from warning_screen import WarningScreen
from welcome_screen import WelcomeScreen

# Windows specific imports
if os.name == "nt":
    try:
        import ctypes
        import winreg
    except Exception:
        winreg = None
else:
    winreg = None


# Ensure script is running as Administrator (Windows only)
if os.name == "nt":
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        is_admin = False
    if not is_admin:
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit()


USER_AGENT = "SelfLinux-Recommender/1.0"


def get_downloads_folder():
    """Return Downloads folder."""
    if os.name == "nt" and winreg is not None:
        try:
            reg_key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders",
            )
            downloads_path = winreg.QueryValueEx(
                reg_key, "{374DE290-123F-4565-9164-39C4925E467B}"
            )[0]
            winreg.CloseKey(reg_key)
            return downloads_path
        except Exception:
            return os.path.join(os.path.expanduser("~"), "Downloads")
    else:
        return os.path.join(os.path.expanduser("~"), "Downloads")


# Main Window
class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SelfLinux Recommender")
        self.geometry("960x640")
        self.minsize(900, 600)
        apply_theme(self)

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.state = {
            # User prefs (added more settings!)
            "visual": None,
            "usage": None,
            "experience": None,
            "update_pref": None,
            "privacy": None,
            "free_software_only": None,
            "battery_priority": None,
            "windows_like": None,
            "gaming_intensity": None,
            "desktop_pref": None,
            # CPU
            "cpu_model": None,
            "cpu_cat": None,
            "cpu_score": None,
            "cpu_gen": None,
            "cpu_vendor": None,
            "max_ghz": None,
            "cores": None,
            "threads": None,
            # RAM
            "ram_total_gb": None,
            "ram_avail_gb": None,
            "ram_used_percent": None,
            "ram_cat": None,
            "ram_speed_mhz": None,
            "ram_type": None,
            # GPU
            "gpu_name": None,
            "gpu_cat": None,
            "gpu_vram_mb": None,
            # Storage
            "storage_type": None,
            "storage_cat": None,
            "storage_size_gb": None,
            "storage_free_gb": None,
            # Battery (new!)
            "has_battery": False,
            "battery_percent": None,
            "battery_plugged": None,
        }

        self.container = tk.Frame(self, bg=COLORS["bg"])
        self.container.grid(row=0, column=0, sticky="nsew")
        self.container.rowconfigure(0, weight=1)
        self.container.columnconfigure(0, weight=1)

        self.frames = {}
        for ScreenClass in (
            WelcomeScreen,
            WarningScreen,
            HardwareScreen,
            PreferencesScreen,
            RecommendationScreen,
        ):
            frame = ScreenClass(parent=self.container, controller=self)
            self.frames[ScreenClass.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status = tk.Label(
            self,
            textvariable=self.status_var,
            anchor="w",
            bg="#eef0f5",
            fg=COLORS["text_muted"],
            font=FONTS["small"],
            padx=10,
            pady=4,
        )
        status.grid(row=1, column=0, sticky="ew")

        # Initial hardware checks
        self.refresh_ram_async()
        self.refresh_gpu_async()
        self.refresh_storage_async()
        self.refresh_cpu_async()
        self.refresh_battery_async()

        self.show_frame("WelcomeScreen")

    def show_frame(self, name: str):
        self.frames[name].tkraise()

    # ---------- Probe refresh ----------
    def _categorize_ram(self, total_gb):
        if total_gb is None:
            return "unknown"
        if total_gb <= 2.0:
            return "very_low"
        if total_gb <= 4.0:
            return "low"
        if total_gb <= 8.0:
            return "mid"
        if total_gb <= 16.0:
            return "good"
        return "high"

    def refresh_ram_async(self):
        def worker():
            d = probe_ram()
            if d and d.get("ok"):
                self.state["ram_total_gb"] = d.get("total_gb")
                self.state["ram_avail_gb"] = d.get("available_gb")
                self.state["ram_used_percent"] = d.get("used_percent")
                self.state["ram_cat"] = self._categorize_ram(d.get("total_gb"))
                self.state["ram_speed_mhz"] = d.get("speed_mhz")
                self.state["ram_type"] = d.get("type")
            else:
                self.state["ram_cat"] = "unknown"
            try:
                self.after(0, self._update_statusbar)
            except Exception:
                pass

        threading.Thread(target=worker, daemon=True).start()

    def refresh_cpu_async(self, on_done=None):
        def worker():
            try:
                d = probe_cpu()
                if d and d.get("ok"):
                    self.state["cpu_model"] = d.get("model")
                    self.state["max_ghz"] = d.get("max_ghz")
                    self.state["cores"] = d.get("cores")
                    self.state["threads"] = d.get("threads")
                    self.state["cpu_cat"] = d.get("category")
                    self.state["cpu_score"] = d.get("score")
                    self.state["cpu_gen"] = d.get("generation")
                    self.state["cpu_vendor"] = d.get("vendor")
                else:
                    self.state["cpu_cat"] = "unknown"
            finally:
                if on_done:
                    try:
                        self.after(0, on_done)
                    except Exception:
                        pass

        threading.Thread(target=worker, daemon=True).start()

    def refresh_gpu_async(self):
        def worker():
            d = probe_gpu()
            if d and d.get("ok"):
                self.state["gpu_name"] = d.get("name")
                self.state["gpu_cat"] = d.get("category")
                self.state["gpu_vram_mb"] = d.get("vram_mb")
            else:
                self.state["gpu_cat"] = "nogpu"

        threading.Thread(target=worker, daemon=True).start()

    def refresh_storage_async(self):
        def worker():
            d = probe_storage_type()
            if d and d.get("ok"):
                self.state["storage_type"] = d.get("type")
                self.state["storage_cat"] = d.get("category")
                self.state["storage_size_gb"] = d.get("size_gb")
                self.state["storage_free_gb"] = d.get("free_gb")
            else:
                self.state["storage_cat"] = "unknown"

        threading.Thread(target=worker, daemon=True).start()

    def refresh_battery_async(self):
        def worker():
            d = probe_battery()
            if d and d.get("ok"):
                self.state["has_battery"] = d.get("has_battery", False)
                self.state["battery_percent"] = d.get("percent")
                self.state["battery_plugged"] = d.get("plugged")

        threading.Thread(target=worker, daemon=True).start()

    def _update_statusbar(self):
        ram = self.state.get("ram_total_gb")
        if ram:
            self.status_var.set(
                f"RAM: {self.state['ram_avail_gb']} GB free / {ram} GB total · "
                f"{self.state.get('ram_used_percent', 0)}% used"
            )

    # Install entry
    def write_distro_to_usb(self, distro_name: str):
        installer = InstallerWindow(self, distro_name)
        installer.grab_set()
        self.wait_visibility(installer)
        installer.geometry(
            "+%d+%d"
            % (
                self.winfo_rootx()
                + (self.winfo_width() - installer.winfo_width()) // 2,
                self.winfo_rooty()
                + (self.winfo_height() - installer.winfo_height()) // 2,
            )
        )


class InstallerWindow(tk.Toplevel):
    """
    Installer window:
    - Resolves the latest official ISO URL dynamically (handles redirects).
    - Downloads it with a real progress bar.
    - Verifies SHA after download.
    - Writes to USB (Windows: dd / diskpart fallback; Linux: dd).
    """

    def __init__(self, parent, distro_name):
        super().__init__(parent)
        self.title(f"Install — {distro_name}")
        self.geometry("760x640")
        self.minsize(720, 600)
        self.configure(bg=COLORS["bg"])
        apply_theme(self)

        self.parent = parent
        self.distro_name = distro_name
        self.iso_info = None  # {url, sha_url, sha_algo, filename}
        self.iso_path = None
        self.usb_drives = []
        self.selected_drive = None
        self._cancel_download = False

        self.columnconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)

        self._create_ui()
        self.after(100, self._resolve_async)
        self._refresh_usb_drives()

    # NEW UI!!
    def _create_ui(self):
        header = tk.Frame(self, bg=COLORS["bg"])
        header.grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 6))
        tk.Label(
            header,
            text=f"Install {self.distro_name}",
            font=FONTS["title"],
            bg=COLORS["bg"],
            fg=COLORS["text"],
        ).pack(anchor="w")
        self.url_label = tk.Label(
            header,
            text="Resolving latest ISO URL…",
            font=FONTS["small"],
            bg=COLORS["bg"],
            fg=COLORS["text_muted"],
            wraplength=720,
            justify="left",
        )
        self.url_label.pack(anchor="w", pady=(2, 0))

        # Progress card
        prog_outer = tk.Frame(self, bg=COLORS["border"])
        prog_outer.grid(row=1, column=0, sticky="ew", padx=18, pady=8)
        prog = tk.Frame(prog_outer, bg=COLORS["surface"], padx=14, pady=12)
        prog.pack(fill="x", padx=1, pady=1)

        top_row = tk.Frame(prog, bg=COLORS["surface"])
        top_row.pack(fill="x")
        tk.Label(
            top_row,
            text="Status:",
            font=FONTS["body_b"],
            bg=COLORS["surface"],
            fg=COLORS["text"],
        ).pack(side="left")
        self.status_var = tk.StringVar(value="Idle")
        tk.Label(
            top_row,
            textvariable=self.status_var,
            font=FONTS["body"],
            bg=COLORS["surface"],
            fg=COLORS["text"],
        ).pack(side="left", padx=(6, 0))

        self.progress = ttk.Progressbar(
            prog, orient="horizontal", mode="determinate", maximum=100, length=400
        )
        self.progress.pack(fill="x", pady=(8, 4))

        self.progress_text = tk.Label(
            prog,
            text="",
            font=FONTS["small"],
            bg=COLORS["surface"],
            fg=COLORS["text_muted"],
        )
        self.progress_text.pack(anchor="w")

        # USB drive selection
        drv_outer = tk.Frame(self, bg=COLORS["border"])
        drv_outer.grid(row=2, column=0, sticky="ew", padx=18, pady=4)
        drv = tk.Frame(drv_outer, bg=COLORS["surface"], padx=14, pady=12)
        drv.pack(fill="x", padx=1, pady=1)
        tk.Label(
            drv,
            text="USB drive",
            font=FONTS["body_b"],
            bg=COLORS["surface"],
            fg=COLORS["text"],
        ).pack(anchor="w")

        listbox_frame = tk.Frame(drv, bg=COLORS["surface"])
        listbox_frame.pack(fill="x", pady=(6, 4))
        self.drive_listbox = tk.Listbox(
            listbox_frame,
            height=4,
            bg="#fafbfd",
            fg=COLORS["text"],
            bd=1,
            relief="solid",
            highlightthickness=0,
            selectbackground=COLORS["primary"],
            selectforeground="#ffffff",
            font=FONTS["body"],
        )
        self.drive_listbox.pack(side="left", fill="x", expand=True)
        self.drive_listbox.bind("<<ListboxSelect>>", self._on_drive_select)
        sb = ttk.Scrollbar(
            listbox_frame, orient="vertical", command=self.drive_listbox.yview
        )
        sb.pack(side="right", fill="y")
        self.drive_listbox.configure(yscrollcommand=sb.set)

        ttk.Button(
            drv,
            text="Refresh drives",
            style="Secondary.TButton",
            command=self._refresh_usb_drives,
        ).pack(anchor="w", pady=(2, 0))

        # Action buttons
        actions = tk.Frame(self, bg=COLORS["bg"])
        actions.grid(row=3, column=0, sticky="ew", padx=18, pady=8)

        self.download_btn = ttk.Button(
            actions,
            text="Download ISO",
            style="Primary.TButton",
            command=self._download_iso,
        )
        self.download_btn.pack(side="left")
        self.verify_btn = ttk.Button(
            actions,
            text="Verify checksum",
            style="Secondary.TButton",
            command=self._verify_iso,
            state="disabled",
        )
        self.verify_btn.pack(side="left", padx=8)
        self.write_btn = ttk.Button(
            actions,
            text="Write to USB",
            style="Primary.TButton",
            command=self._write_to_usb,
            state="disabled",
        )
        self.write_btn.pack(side="left", padx=8)
        self.close_btn = ttk.Button(
            actions, text="Close", style="Secondary.TButton", command=self.destroy
        )
        self.close_btn.pack(side="right")

        # Log
        log_outer = tk.Frame(self, bg=COLORS["border"])
        log_outer.grid(row=4, column=0, sticky="nsew", padx=18, pady=(4, 16))
        log_frame = tk.Frame(log_outer, bg=COLORS["surface"], padx=10, pady=10)
        log_frame.pack(fill="both", expand=True, padx=1, pady=1)
        tk.Label(
            log_frame,
            text="Log",
            font=FONTS["body_b"],
            bg=COLORS["surface"],
            fg=COLORS["text"],
        ).pack(anchor="w")

        text_wrap = tk.Frame(log_frame, bg=COLORS["surface"])
        text_wrap.pack(fill="both", expand=True, pady=(6, 0))
        self.console = tk.Text(
            text_wrap,
            bg="#fafbfd",
            fg=COLORS["text"],
            font=FONTS["mono"],
            bd=1,
            relief="solid",
            wrap="word",
            height=8,
        )
        self.console.pack(side="left", fill="both", expand=True)
        sb2 = ttk.Scrollbar(text_wrap, orient="vertical", command=self.console.yview)
        sb2.pack(side="right", fill="y")
        self.console.config(yscrollcommand=sb2.set)

    def _log(self, msg):
        ts = time.strftime("%H:%M:%S")
        self.console.insert("end", f"[{ts}] {msg}\n")
        self.console.see("end")
        self.console.update_idletasks()

    # ISO resolution instead of installing from my google drive :D
    def _resolve_async(self):
        self._log(f"Resolving ISO URL for {self.distro_name}…")
        self.status_var.set("Resolving URL…")

        def worker():
            info = resolve_iso(self.distro_name)
            self.after(0, lambda: self._on_resolved(info))

        threading.Thread(target=worker, daemon=True).start()

    def _on_resolved(self, info):
        if not info or not info.get("url"):
            self.status_var.set("Resolution failed")
            self._log("Failed to resolve ISO URL automatically.")
            self.url_label.config(
                text=(
                    "Could not auto-resolve. You can still pick an ISO file "
                    "manually with 'Verify checksum' if you already have one."
                )
            )
            self._enable_manual_iso()
            return

        self.iso_info = info
        downloads = get_downloads_folder()
        self.iso_path = os.path.join(downloads, info["filename"])
        self.url_label.config(text=f"URL:  {info['url']}")
        self._log(f"Resolved → {info['url']}")
        if info.get("sha_url"):
            self._log(f"Checksum source: {info['sha_url']}")
        else:
            self._log("No checksum URL available; manual verification recommended.")
        self.status_var.set("Ready to download")

        # If file already present, offer to use it
        if os.path.exists(self.iso_path):
            self._log(f"Existing file detected: {self.iso_path}")
            if messagebox.askyesno(
                "ISO exists",
                f"An ISO already exists at:\n{self.iso_path}\n\nUse it as-is?",
            ):
                self._on_download_complete(success=True, skipped=True)
            else:
                try:
                    os.remove(self.iso_path)
                    self._log("Existing ISO removed.")
                except Exception as e:
                    self._log(f"Could not remove existing ISO: {e}")

    def _enable_manual_iso(self):
        """Allow user to pick a local ISO if URL resolution failed."""
        self.download_btn.configure(
            text="Pick local ISO…", command=self._pick_local_iso
        )

    def _pick_local_iso(self):
        f = filedialog.askopenfilename(
            filetypes=[("ISO files", "*.iso"), ("All files", "*.*")]
        )
        if f:
            self.iso_path = f
            self._log(f"Using local ISO: {f}")
            self._on_download_complete(success=True, skipped=True)

    # Downloading
    def _download_iso(self):
        if not self.iso_info:
            messagebox.showerror("Not ready", "ISO URL not resolved yet.")
            return
        self.download_btn.configure(state="disabled")
        self.write_btn.configure(state="disabled")
        self.verify_btn.configure(state="disabled")
        self.status_var.set("Downloading…")
        self._log(f"Downloading to {self.iso_path}")
        self._cancel_download = False
        threading.Thread(target=self._download_thread, daemon=True).start()

    def _download_thread(self):
        try:
            req = urllib.request.Request(
                self.iso_info["url"], headers={"User-Agent": USER_AGENT}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                total = int(resp.headers.get("Content-Length") or 0)
                self.after(0, lambda: self.progress.configure(maximum=max(1, total)))
                downloaded = 0
                start_time = time.time()
                tmp_path = self.iso_path + ".part"
                with open(tmp_path, "wb") as f:
                    while True:
                        if self._cancel_download:
                            raise RuntimeError("Cancelled by user")
                        chunk = resp.read(64 * 1024)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        elapsed = max(0.001, time.time() - start_time)
                        speed = downloaded / elapsed
                        self._update_progress(downloaded, total, speed)
                os.replace(tmp_path, self.iso_path)
            self.after(0, lambda: self._on_download_complete(True, False))
        except Exception as e:
            self.after(0, lambda: self._on_download_failed(str(e)))

    def _update_progress(self, downloaded, total, speed):
        def fmt_size(b):
            if b > 1024**3:
                return f"{b/1024**3:.2f} GB"
            if b > 1024**2:
                return f"{b/1024**2:.1f} MB"
            if b > 1024:
                return f"{b/1024:.1f} KB"
            return f"{b} B"

        def update():
            self.progress["value"] = downloaded
            pct = (downloaded / total) * 100 if total else 0
            self.progress_text.config(
                text=f"{fmt_size(downloaded)} / {fmt_size(total)}  ·  "
                f"{fmt_size(speed)}/s  ·  {pct:.1f}%"
            )
            self.status_var.set(f"Downloading… {pct:.1f}%")

        self.after(0, update)

    def _on_download_complete(self, success, skipped):
        if success:
            self.status_var.set("Download complete" if not skipped else "ISO ready")
            self._log("ISO file ready." if skipped else "Download finished.")
            self.progress["value"] = self.progress["maximum"] or 100
            self.progress_text.config(text=f"Saved to {self.iso_path}")
            self.download_btn.configure(state="normal")
            self.verify_btn.configure(state="normal")
            self._update_write_button()
            # Auto-prompt for verification
            if self.iso_info and self.iso_info.get("sha_url"):
                if messagebox.askyesno(
                    "Verify checksum",
                    "Download complete. Verify the SHA-256 checksum now? (recommended)",
                ):
                    self._verify_iso()

    def _on_download_failed(self, err):
        self.status_var.set("Download failed")
        self._log(f"Download error: {err}")
        self.download_btn.configure(state="normal")
        messagebox.showerror("Download failed", err)

    # SHA Verify for that "Don't download isos from random dudes" gng
    def _verify_iso(self):
        if not self.iso_path or not os.path.exists(self.iso_path):
            messagebox.showerror("No ISO", "ISO file not found.")
            return

        sha_url = (self.iso_info or {}).get("sha_url")
        algo = (self.iso_info or {}).get("sha_algo") or "sha256"
        expected = None
        if sha_url:
            self._log(f"Fetching expected hash from {sha_url}")
            expected = fetch_expected_hash(sha_url, self.iso_path, algo)
            if expected:
                self._log(f"Expected {algo}: {expected}")
            else:
                self._log("Could not parse expected hash from checksum file.")

        dlg = ShaVerifyDialog(
            self,
            self.iso_path,
            algo=algo,
            expected=expected,
            distro_name=self.distro_name,
        )
        dlg.grab_set()
        self.wait_window(dlg)
        if dlg.result is True:
            self._log("Checksum verified ✓")
        elif dlg.result is False:
            self._log("Checksum MISMATCH ✗ — do not write this ISO!")
            messagebox.showerror(
                "Checksum mismatch",
                "The ISO checksum does not match. "
                "It may be corrupted or tampered with. "
                "Please re-download.",
            )
            self.write_btn.configure(state="disabled")
        else:
            self._log("Verification complete (no reference available).")

    # USB
    def _refresh_usb_drives(self):
        self.drive_listbox.delete(0, "end")
        self.usb_drives = []
        try:
            if os.name == "nt":
                ps = """
                Get-Disk | Where-Object {$_.BusType -eq 'USB'} | ForEach-Object {
                    $disk = $_
                    $partitions = $disk | Get-Partition | Where-Object {$_.DriveLetter}
                    $letters = $partitions | ForEach-Object { $_.DriveLetter }
                    $size = [math]::Round($disk.Size / 1GB, 2)
                    "$($disk.Number)|$($letters -join ',')|$size GB|$($disk.FriendlyName)"
                }
                """
                result = subprocess.run(
                    ["powershell", "-Command", ps], capture_output=True, text=True
                )
                lines = [l.strip() for l in result.stdout.splitlines() if l.strip()]
                for line in lines:
                    parts = line.split("|")
                    if len(parts) >= 4:
                        disk_num = parts[0].strip()
                        letters = parts[1].strip() or "—"
                        size = parts[2].strip()
                        name = parts[3].strip()
                        text = f"Disk {disk_num}: {letters}  ·  {size}  ·  {name}"
                        self.usb_drives.append((disk_num, text))
                        self.drive_listbox.insert("end", text)
            else:
                # Linux/macOS: enumerate removable block devices
                if platform.system().lower() == "linux":
                    out = subprocess.run(
                        ["lsblk", "-d", "-o", "NAME,SIZE,RM,MODEL", "-n"],
                        capture_output=True,
                        text=True,
                    ).stdout
                    for line in out.splitlines():
                        parts = line.split(None, 3)
                        if len(parts) >= 3 and parts[2] == "1":
                            name = parts[0]
                            size = parts[1]
                            model = parts[3] if len(parts) > 3 else ""
                            text = f"/dev/{name}  ·  {size}  ·  {model}"
                            self.usb_drives.append((f"/dev/{name}", text))
                            self.drive_listbox.insert("end", text)

            if not self.usb_drives:
                self.drive_listbox.insert("end", "No USB drives detected")
                self._log("No USB drives detected")
            else:
                self._log(f"Found {len(self.usb_drives)} USB drive(s)")
        except Exception as e:
            self._log(f"USB scan error: {e}")
        self._update_write_button()

    def _on_drive_select(self, event):
        sel = self.drive_listbox.curselection()
        if sel and sel[0] < len(self.usb_drives):
            self.selected_drive = self.usb_drives[sel[0]][0]
            self._log(f"Selected: {self.usb_drives[sel[0]][1]}")
        else:
            self.selected_drive = None
        self._update_write_button()

    def _update_write_button(self):
        if self.iso_path and os.path.exists(self.iso_path) and self.selected_drive:
            self.write_btn.configure(state="normal")
        else:
            self.write_btn.configure(state="disabled")

    def _write_to_usb(self):
        if not (self.iso_path and os.path.exists(self.iso_path)):
            messagebox.showerror("No ISO", "No ISO file available.")
            return
        if not self.selected_drive:
            messagebox.showerror("No drive", "No USB drive selected.")
            return

        sel_text = next(
            (t for d, t in self.usb_drives if d == self.selected_drive),
            self.selected_drive,
        )
        if not messagebox.askyesno(
            "Confirm write", f"This will ERASE all data on:\n\n{sel_text}\n\nContinue?"
        ):
            return

        self.download_btn.configure(state="disabled")
        self.verify_btn.configure(state="disabled")
        self.write_btn.configure(state="disabled")
        self.close_btn.configure(state="disabled")
        self.status_var.set("Writing to USB…")
        self.progress["value"] = 0
        threading.Thread(target=self._write_thread, daemon=True).start()

    def _write_thread(self):
        try:
            if os.name == "nt":
                self._write_windows()
            else:
                self._write_unix()
        except Exception as e:
            self._log(f"Write error: {e}")
            self.after(0, lambda: self.status_var.set(f"Error: {str(e)[:60]}"))
        finally:
            self.after(0, self._reset_buttons)

    def _reset_buttons(self):
        self.download_btn.configure(state="normal")
        self.verify_btn.configure(state="normal")
        self.write_btn.configure(state="normal")
        self.close_btn.configure(state="normal")

    def _write_unix(self):
        usb = self.selected_drive
        self._log(f"Writing via dd to {usb}")
        cmd = [
            "sudo",
            "dd",
            f"if={self.iso_path}",
            f"of={usb}",
            "bs=4M",
            "status=progress",
            "oflag=sync",
        ]
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )
        for line in proc.stdout:
            self._log(line.strip())
        proc.wait()
        if proc.returncode == 0:
            self.after(0, lambda: self.status_var.set("Write complete"))
        else:
            self.after(0, lambda: self.status_var.set("Write failed"))

    def _write_windows(self):
        usb_path = f"\\\\.\\PHYSICALDRIVE{self.selected_drive}"
        dd_path = shutil.which("dd")
        if dd_path:
            self._log(f"Writing via dd to {usb_path}")
            cmd = [
                dd_path,
                f"if={self.iso_path}",
                f"of={usb_path}",
                "bs=4M",
                "--progress",
            ]
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
            )
            for line in proc.stdout:
                self._log(line.strip())
            proc.wait()
            if proc.returncode == 0:
                self.after(0, lambda: self.status_var.set("Write complete"))
                return
            self._log("dd failed; falling back to diskpart copy.")

        # diskpart fallback (file copy)
        self._log("Using diskpart + ISO file copy fallback")
        script = os.path.join(os.environ.get("TEMP", "."), "selflinux_dp.txt")
        with open(script, "w") as f:
            f.write(
                f"select disk {self.selected_drive}\nclean\n"
                f"create partition primary\nselect partition 1\nactive\n"
                f"format fs=fat32 quick\nassign\nexit\n"
            )
        subprocess.run(["diskpart", "/s", script], check=False)
        self._log(
            "Drive prepared; please copy ISO contents manually if dd is unavailable."
        )
        self.after(
            0, lambda: self.status_var.set("Drive prepared (manual copy required)")
        )


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
