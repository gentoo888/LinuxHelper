# This is a completely rewritten version that avoids all querystring issues

import os
import sys
import re
import subprocess
import threading
import webbrowser
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import platform
import shutil
import time

# Local imports
from welcome_screen import WelcomeScreen
from hardware_screen import HardwareScreen
from preferences_screen import PreferencesScreen
from recommendation_screen import RecommendationScreen
from warning_screen import WarningScreen

from ram_probe import probe_ram
from gpu_probe import probe_gpu
from storage_probe import probe_storage_type
from cpu_probe import probe_cpu

# Windows specific imports
if os.name == 'nt':
    try:
        import ctypes
        import winreg
    except Exception:
        winreg = None
else:
    winreg = None

# Ensure script is running as Administrator (Windows only)
if os.name == 'nt':
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        is_admin = False
    if not is_admin:
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit()


# ---------------- ISO FILE IDS ----------------
# Store just the file IDs directly. Too lazy to write/copy paste every url XD. Oh and also avoids querystring issues.

DISTRO_FILE_IDS = {
    "Debian XFCE": "1x7Y6dMDRPXOeirObzlBdoB-wdYM2hrot",
    "Xubuntu": "1QAE1W7oA2V_n78TyfKDSU1z2aqMy2eVf",
    "Void (LXQt)": "1l9MNSDZF9dzLxTGOLxvm7vXwPH1qDztH",
    "Zorin OS Core": "1NEXuitr5lIzTgc-NuYkArTcK9Siw7FfO",
    "Linux Lite": "1tEk_RwA7rlxBgpctWq9nJSSeGGCOk2_l",
    "Peppermint": "1hgM4EwffHIY3OLb128Hz25s0yTuTld-J",
    "Linux Mint XFCE": "16Z-c-C44Rua4qnxXZ0BwcLfOAMBXoROu",
    "Lubuntu": "1VBSZMz72cAGVC3g70btJP4u2O7LuNIpA",
    "antiX": "1Z-d2tnojPKyBOMtIsY33jdba6u2g6r9-",
    "elementary OS": "1qyaVa2eGvYO67taoMv_e0rMAVhNjw3Zm",
    "Fedora Workstation": "17ayhQzAaMKj3la9a84EBcnt-B8-AfHF8",
    "Ubuntu LTS": "13KrL3SlaB1OmJA5d-Hcq0bOLIbeGmR9f",
    "KDE neon": "18K0ghaB0UYvUYq5gePsMVryzYnNWlzCS",
    "Linux Mint Cinnamon": "16Z-c-C44Rua4qnxXZ0BwcLfOAMBXoROu",
    "Pop!_OS": "1_0Yao3kCsWj1eA4d2IUZZKR4c2UMyBR6",
    "Nobara": "1OYNxxXp3DgkfmJcOYkFfFSEZbSKzrLYh",
    "openSUSE Tumbleweed": "1xVS-6WiJcE7NkjhydfZ-ZmKtWLk-VOpO"
}

# ---------------- ISO FILENAMES ----------------
# We will need these to find the ISO in the Downloads folder.
DISTRO_ISO_NAMES = {
    "Debian XFCE": "debian-live-13.1.0-amd64-xfce.iso",
    "Xubuntu": "xubuntu-24.04.3-desktop-amd64.iso",
    "Void (LXQt)": "fvoid-live-x86_64-20240328-lxqt.iso",
    "Zorin OS Core": "Zorin-OS-17.3-Lite-64-bit-r2.iso",
    "Linux Lite": "linux-lite-7.6-64bit.iso",
    "Peppermint": "PeppermintOS-Debian-64.iso",
    "Linux Mint XFCE": "linuxmint-22.1-xfce-64bit.iso",
    "Lubuntu": "lubuntu-24.04.3-desktop-amd64.iso",
    "antiX": "antiX-23.2_x64-full.iso",
    "elementary OS": "elementaryos-8.0-stable.20250314rc.iso",
    "Fedora Workstation": "Fedora-Workstation-Live-42-1.1.x86_64.iso",
    "Ubuntu LTS": "ubuntu-24.04.3-desktop-amd64.iso",
    "KDE neon": "neon-user-20250914-0826.iso",
    "Linux Mint Cinnamon": "linuxmint-22.1-cinnamon-64bit.iso",
    "Pop!_OS": "pop-os_24.04_amd64_intel_14.iso",
    "Nobara": "Nobara-42-Official-2025-05-13.iso",
    "openSUSE Tumbleweed": "openSUSE-Tumbleweed-DVD-x86_64-Snapshot20250912-Media.iso"
}


# ---------------- Helpers ----------------
def get_downloads_folder():
    """Return Downloads folder (from Windows registry if available, otherwise ~/Downloads)."""
    if os.name == 'nt' and winreg is not None:
        try:
            reg_key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
            )
            downloads_path = winreg.QueryValueEx(
                reg_key,
                "{374DE290-123F-4565-9164-39C4925E467B}"
            )[0]
            winreg.CloseKey(reg_key)
            return downloads_path
        except Exception:
            return os.path.join(os.path.expanduser("~"), "Downloads")
    else:
        return os.path.join(os.path.expanduser("~"), "Downloads")


# ---------------- MAIN WINDOW ----------------
class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SelfLinux Recommender")
        self.geometry("800x500")

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.state = {
            "visual": None,
            "usage": None,
            "ram_cat": None,
            "cpu_cat": None,
            "gpu_cat": None,
            "gpu_name": None,
            "storage_cat": None,
            "storage_type": None,
            "cpu-info": None,
            "ram_info": None,
            "ram_total_gb": None,
            "ram_avail_gb": None,
            "ram_used_percent": None,
        }

        self.container = tk.Frame(self)
        self.container.grid(row=0, column=0, sticky="nsew")
        self.container.rowconfigure(0, weight=1)
        self.container.columnconfigure(0, weight=1)

        self.frames = {}
        for ScreenClass in (WelcomeScreen, WarningScreen, HardwareScreen, PreferencesScreen, RecommendationScreen):
            frame = ScreenClass(parent=self.container, controller=self)
            self.frames[ScreenClass.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.status_var = tk.StringVar(value="RAM: scanning…")
        status = tk.Label(self, textvariable=self.status_var, anchor="w")
        status.grid(row=1, column=0, sticky="ew")

        # Initial hardware checks
        self.refresh_ram_async()
        self.refresh_gpu_async()
        self.refresh_storage_async()
        self.refresh_cpu_async()

        # We start with the welcome screen.
        self.show_frame("WelcomeScreen")

    def show_frame(self, name: str):
        self.frames[name].tkraise()

    def _categorize_ram(self, total_gb: float) -> str:
        if total_gb is None:
            return "unknown"
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
            self.state["ram_info"] = d
            if d and d.get("ok"):
                self.state["ram_total_gb"] = d.get("total_gb")
                self.state["ram_avail_gb"] = d.get("available_gb")
                self.state["ram_used_percent"] = d.get("used_percent")
                self.state["ram_cat"] = self._categorize_ram(d.get("total_gb"))
            else:
                self.state["ram_total_gb"] = None
                self.state["ram_avail_gb"] = None
                self.state["ram_used_percent"] = None
                self.state["ram_cat"] = "unknown"
            # FIX: Use a thread-safe way to schedule GUI update. This was a problem I was facing for days lol.
            if self.winfo_exists():  # Check if window still exists
                self.after(0, self._update_statusbar)
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
                else:
                    self.state["cpu_model"] = None
                    self.state["max_ghz"] = None
                    self.state["cores"] = None
                    self.state["threads"] = None
                    self.state["cpu_cat"] = "unknown"
            finally:
                if on_done and self.winfo_exists():
                    self.after(0, on_done)
        threading.Thread(target=worker, daemon=True).start()

    def refresh_gpu_async(self):
        def worker():
            d = probe_gpu()
            if d and d.get("ok"):
                self.state["gpu_name"] = d.get("name")
                self.state["gpu_cat"] = d.get("category")
            else:
                self.state["gpu_name"] = None
                self.state["gpu_cat"] = "nogpu"
        threading.Thread(target=worker, daemon=True).start()

    def refresh_storage_async(self):
        def worker():
            d = probe_storage_type()
            if not d:
                self.state["storage_type"] = None
                self.state["storage_cat"] = "unknown"
                return
            if d.get("ok"):
                self.state["storage_type"] = d.get("type")
                self.state["storage_cat"] = d.get("category")
            else:
                self.state["storage_type"] = None
                self.state["storage_cat"] = "unknown"
        threading.Thread(target=worker, daemon=True).start()

    def _update_statusbar(self):
        d = self.state.get("ram_info")
        if not d or not d.get("ok"):
            self.status_var.set("RAM: unavailable")
        else:
            self.status_var.set(
                f"RAM: {d.get('available_gb')} GB free / {d.get('total_gb')} GB total  |  {d.get('used_percent')}% used"
            )

    def write_distro_to_usb(self, distro_name: str):
        """Write distro to USB using a completely new approach."""
        # Get the file ID and ISO filename
        file_id = DISTRO_FILE_IDS.get(distro_name)
        if not file_id:
            messagebox.showerror("Error", f"No file ID found for {distro_name}")
            return
            
        iso_filename = DISTRO_ISO_NAMES.get(distro_name)
        downloads_dir = get_downloads_folder()
        iso_path = os.path.join(downloads_dir, iso_filename)
        
        # Create the installer window
        installer = InstallerWindow(self, distro_name, file_id, iso_path)
        installer.grab_set()  # Make it modal
        
        # Position the window
        self.wait_visibility(installer)
        installer.geometry("+%d+%d" % (
            self.winfo_rootx() + (self.winfo_width() - installer.winfo_width()) // 2,
            self.winfo_rooty() + (self.winfo_height() - installer.winfo_height()) // 2
        ))


class InstallerWindow(tk.Toplevel):
    """A separate window for the installation process to avoid querystring issues."""
    
    def __init__(self, parent, distro_name, file_id, iso_path):
        super().__init__(parent)
        self.title(f"Install {distro_name}")
        self.geometry("700x600")
        self.minsize(600, 500)
        
        # Store parameters
        self.parent = parent
        self.distro_name = distro_name
        self.file_id = file_id
        self.iso_path = iso_path
        
        # Store USB drive information
        self.usb_drives = []  # List of (disk_num, display_text) tuples
        self.selected_drive = None
        
        # Configure the grid
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)  # Make the console expand
        
        # Create the UI elements
        self._create_ui()
        
        # Populate the USB drives list
        self._refresh_usb_drives()
        
        # Check if ISO already exists
        self._check_iso_exists()
        
    def _create_ui(self):
        """Create all UI elements."""
        # Header
        header_frame = tk.Frame(self)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        header_label = tk.Label(
            header_frame, 
            text=f"Installing {self.distro_name}", 
            font=("Arial", 16, "bold")
        )
        header_label.pack(side=tk.LEFT)
        
        # Status and progress
        status_frame = tk.Frame(self)
        status_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        status_frame.columnconfigure(1, weight=1)
        
        tk.Label(status_frame, text="Status:").grid(row=0, column=0, sticky="w")
        self.status_var = tk.StringVar(value="Ready")
        status_label = tk.Label(status_frame, textvariable=self.status_var, anchor="w")
        status_label.grid(row=0, column=1, sticky="ew", padx=5)
        
        tk.Label(status_frame, text="Progress:").grid(row=1, column=0, sticky="w")
        self.progress_var = tk.IntVar(value=0)
        self.progress_bar = ttk.Progressbar(
            status_frame, 
            orient="horizontal",
            mode="determinate", 
            variable=self.progress_var,
            length=200
        )
        self.progress_bar.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        # USB drive selection
        drive_frame = tk.LabelFrame(self, text="USB Drive Selection")
        drive_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        drive_frame.columnconfigure(0, weight=1)
        
        self.drive_listbox = tk.Listbox(drive_frame, height=5)
        self.drive_listbox.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.drive_listbox.bind('<<ListboxSelect>>', self._on_drive_select)
        
        drive_buttons = tk.Frame(drive_frame)
        drive_buttons.grid(row=1, column=0, sticky="ew")
        
        refresh_btn = tk.Button(
            drive_buttons, 
            text="Refresh Drives", 
            command=self._refresh_usb_drives
        )
        refresh_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Console output
        console_frame = tk.LabelFrame(self, text="Log")
        console_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=5)
        console_frame.rowconfigure(0, weight=1)
        console_frame.columnconfigure(0, weight=1)
        
        self.console = tk.Text(console_frame, height=10, bg="black", fg="white")
        self.console.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        console_scroll = tk.Scrollbar(console_frame, command=self.console.yview)
        console_scroll.grid(row=0, column=1, sticky="ns", pady=5)
        self.console.config(yscrollcommand=console_scroll.set)
        
        # Action buttons
        button_frame = tk.Frame(self)
        button_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=10)
        
        self.download_btn = tk.Button(
            button_frame, 
            text="Download ISO", 
            command=self._download_iso,
            width=15
        )
        self.download_btn.pack(side=tk.LEFT, padx=5)
        
        self.write_btn = tk.Button(
            button_frame, 
            text="Write to USB", 
            command=self._write_to_usb,
            width=15,
            state=tk.DISABLED  # Disabled it for now because no ISO or drive selected
        )
        self.write_btn.pack(side=tk.LEFT, padx=5)
        
        self.close_btn = tk.Button(
            button_frame, 
            text="Close", 
            command=self.destroy,
            width=10
        )
        self.close_btn.pack(side=tk.RIGHT, padx=5)
        
        # Initial log message
        self._log(f"Ready to install {self.distro_name}")
        self._log(f"ISO will be saved to: {self.iso_path}")
        
    def _log(self, message):
        """Add a message to the console log."""
        timestamp = time.strftime("%H:%M:%S")
        self.console.insert(tk.END, f"[{timestamp}] {message}\n")
        self.console.see(tk.END)
        self.console.update_idletasks()
        
    def _check_iso_exists(self):
        """Check if the ISO file already exists."""
        if os.path.exists(self.iso_path):
            self._log(f"ISO file already exists: {self.iso_path}")
            self.status_var.set("ISO file ready")
            self.progress_var.set(100)
            self._update_write_button()
        else:
            self._log("ISO file not found. Please download it.")
            self.status_var.set("ISO not found")
            self.progress_var.set(0)
            
    def _refresh_usb_drives(self):
        """Refresh the list of USB drives."""
        self.drive_listbox.delete(0, tk.END)
        self.usb_drives = []
        
        try:
            if os.name == 'nt':  # Windows
                self._log("Scanning for USB drives...")
                
                # Use PowerShell to get USB drives
                ps_cmd = """
                Get-Disk | Where-Object {$_.BusType -eq 'USB'} | ForEach-Object {
                    $disk = $_
                    $partitions = $disk | Get-Partition | Where-Object {$_.DriveLetter}
                    $letters = $partitions | ForEach-Object { $_.DriveLetter }
                    $size = [math]::Round($disk.Size / 1GB, 2)
                    "$($disk.Number)|$($letters -join ',')|$size GB|$($disk.FriendlyName)"
                }
                """
                
                result = subprocess.run(
                    ["powershell", "-Command", ps_cmd],
                    capture_output=True, text=True
                )
                
                drives = result.stdout.strip().split('\n')
                drives = [d for d in drives if d.strip()]
                
                for drive in drives:
                    if drive.strip():
                        parts = drive.split('|')
                        if len(parts) >= 4:
                            disk_num = parts[0].strip()
                            letters = parts[1].strip()
                            size = parts[2].strip()
                            name = parts[3].strip()
                            
                            # Format for display
                            if letters:
                                display_text = f"Disk {disk_num}: {letters} - {size} - {name}"
                            else:
                                display_text = f"Disk {disk_num}: (No drive letter) - {size} - {name}"
                            
                            self.usb_drives.append((disk_num, display_text))
                            self.drive_listbox.insert(tk.END, display_text)
            
            
            if not self.usb_drives:
                self._log("No USB drives detected")
                self.drive_listbox.insert(tk.END, "No USB drives detected")
            else:
                self._log(f"Found {len(self.usb_drives)} USB drive(s)")
                
        except Exception as e:
            self._log(f"Error scanning USB drives: {e}")
            self.drive_listbox.insert(tk.END, "Error detecting USB drives")
            
        self._update_write_button()
            
    def _on_drive_select(self, event):
        """Handle USB drive selection."""
        selection = self.drive_listbox.curselection()
        if selection and selection[0] < len(self.usb_drives):
            self.selected_drive = self.usb_drives[selection[0]][0]
            self._log(f"Selected drive: {self.usb_drives[selection[0]][1]}")
            self._update_write_button()
        else:
            self.selected_drive = None
            self._update_write_button()
            
    def _update_write_button(self):
        """Update the state of the Write button based on ISO and drive selection."""
        if os.path.exists(self.iso_path) and self.selected_drive is not None:
            self.write_btn.config(state=tk.NORMAL)
        else:
            self.write_btn.config(state=tk.DISABLED)
            
    def _download_iso(self):
        """Download the ISO file."""
        # Check if file already exists
        if os.path.exists(self.iso_path):
            if messagebox.askyesno("File Exists", 
                                  f"ISO file already exists at {self.iso_path}.\nDo you want to use the existing file?"):
                self._log("Using existing ISO file")
                self.status_var.set("ISO file ready")
                self.progress_var.set(100)
                self._update_write_button()
                return
            else:
                # Delete existing file. Because the user chose not to use it. I mean we don't want to use much space right? XD
                self._log("Deleting existing ISO file")
                try:
                    os.remove(self.iso_path)
                    self._log(f"Deleted existing file: {self.iso_path}")
                except Exception as e:
                    self._log(f"Failed to delete existing file: {e}")
                    return
        
        # Open browser for manual download
        download_url = f"https://drive.google.com/file/d/{self.file_id}/view?usp=sharing" # Direct link to avoid querystring issues. (yup too lazy to write every url XD)
        webbrowser.open(download_url)
        
        self._log("Browser opened for manual download")
        self._log(f"Please download the file and save it as: {self.iso_path}")
        
        # Show instructions
        messagebox.showinfo("Manual Download", 
                           f"Please download the ISO file from the browser window that just opened.\n\n"
                           f"1. Click the Download button in Google Drive\n"
                           f"2. Save the file as: {os.path.basename(self.iso_path)}\n"
                           f"3. Save it to your Downloads folder\n\n"
                           f"Click 'ok' AFTER the downloading proccess is completed.") # This is important. The ok button needs to be clicked only after the download is complete. Because after clicking it the program will check if the file exists.
        
        # Check if file exists after manual download
        if os.path.exists(self.iso_path):
            self._log("ISO file downloaded successfully")
            self.status_var.set("ISO file ready")
            self.progress_var.set(100)
        else:
            self._log("ISO file not found after download")
            self.status_var.set("Download failed")
            
            # Ask if user saved to a different location
            if messagebox.askyesno("File Not Found", 
                                  f"Could not find the ISO file at {self.iso_path}.\n\n"
                                  f"Did you save it to a different location?\n\n"
                                  f"Or did you press the 'ok' button before the download was completed?"):
                # Let user select the ISO file
                selected_iso = filedialog.askopenfilename(
                    title="Select the downloaded ISO file",
                    filetypes=[("ISO files", "*.iso"), ("All files", "*.*")]
                )
                
                if selected_iso:
                    self.iso_path = selected_iso
                    self._log(f"Using ISO file from: {self.iso_path}")
                    self.status_var.set("ISO file ready")
                    self.progress_var.set(100)
        
        self._update_write_button()
            
    def _write_to_usb(self):
        """Write the ISO to the selected USB drive."""
        if not os.path.exists(self.iso_path):
            self._log("ISO file not found")
            return
            
        if self.selected_drive is None:
            self._log("No USB drive selected")
            return
            
        # Get the physical drive path or device name
        if os.name == 'nt':  # Windows
            usb_drive = f"\\\\.\\PHYSICALDRIVE{self.selected_drive}"
            
        # Confirm with user
        selected_text = ""
        for disk_num, display_text in self.usb_drives:
            if disk_num == self.selected_drive:
                selected_text = display_text
                break
                
        if not messagebox.askyesno("Confirm USB Write", 
                                 # Better warn the user again. We already warned them in the warning screen but better be safe than sorry ;-)
                                 f"WARNING: This will erase ALL data on the selected USB drive.\n\n"
                                 f"Selected drive: {selected_text}\n\n"
                                 f"Are you ABSOLUTELY SURE you want to continue?"):
            self._log("USB write cancelled by user")
            return
            
        # Disable buttons during write
        self.download_btn.config(state=tk.DISABLED)
        self.write_btn.config(state=tk.DISABLED)
        self.close_btn.config(state=tk.DISABLED)
        
        self.status_var.set("Writing ISO to USB...")
        self.progress_var.set(0)
        
        # Start the write process in a separate thread
        threading.Thread(target=self._write_thread, args=(usb_drive,), daemon=True).start()
        
    def _write_thread(self, usb_drive):
        """Thread function to write the ISO to USB."""
        try:
            if os.name == 'nt':  # Windows
                self._log(f"Writing ISO to {usb_drive}")
                
                # First try using dd.exe if available
                dd_path = shutil.which("dd")
                if dd_path:
                    self._log("Using dd to write ISO directly")
                    
                    cmd = [dd_path, f"if={self.iso_path}", f"of={usb_drive}", "bs=4M", "--progress"]
                    
                    try:
                        process = subprocess.Popen(
                            cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            universal_newlines=True
                        )
                        
                        for line in process.stdout:
                            self._log(line.strip())
                            # Try to extract progress information
                            if "%" in line:
                                try:
                                    percent = int(line.split("%")[0].strip())
                                    self.progress_var.set(percent)
                                except:
                                    pass
                        
                        process.wait()
                        
                        if process.returncode == 0:
                            self._log("ISO successfully written to USB drive")
                            self.status_var.set("USB write completed")
                            self.progress_var.set(100)
                            self._on_write_complete(True)
                            return
                        else:
                            self._log(f"dd failed with code {process.returncode}, trying alternative method")
                    except Exception as e:
                        self._log(f"Error using dd: {e}, trying alternative method")
                
                                # If dd failed or isn't available, use diskpart and manual file copy
                self._log("Using diskpart and manual file copy method")
                
                # Create diskpart script
                script_path = os.path.join(os.environ['TEMP'], 'diskpart_script.txt')
                with open(script_path, 'w') as f:
                    f.write(f"select disk {self.selected_drive}\n")
                    f.write("clean\n")
                    f.write("create partition primary\n")
                    f.write("select partition 1\n")
                    f.write("active\n")
                    f.write("format fs=fat32 quick\n")
                    f.write("assign\n")
                    f.write("list volume\n")  # I added this to see all volumes
                    f.write("exit\n")
                
                self._log("Running diskpart to prepare USB drive")
                
                # Run diskpart script
                diskpart_process = subprocess.Popen(
                    ["diskpart", "/s", script_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )
                
                diskpart_output = ""
                for line in diskpart_process.stdout:
                    self._log(line.strip())
                    diskpart_output += line
                
                diskpart_process.wait()
                
                if diskpart_process.returncode != 0:
                    self._log(f"diskpart failed with code {diskpart_process.returncode}")
                    self.status_var.set("USB preparation failed")
                    self._on_write_complete(False)
                    return
                
                # Try to find the drive letter from diskpart output
                drive_letter = None
                
                # Look for the newly formatted drive in the diskpart output
                lines = diskpart_output.split('\n')
                for i, line in enumerate(lines):
                    if "successfully assigned the drive letter" in line.lower():
                        # Try to extract the drive letter from this message
                        parts = line.split()
                        for part in parts:
                            if len(part) == 2 and part[1] == ':':
                                drive_letter = part[0]
                                break
                
                # If couldn't find it in the success message, try another approach
                if not drive_letter:
                    # Try to get all USB drives and find one that wasn't there before
                    self._log("Trying to find USB drive letter using PowerShell")
                    ps_cmd = """
                    Get-Volume | Where-Object {$_.DriveType -eq 'Removable'} | ForEach-Object { $_.DriveLetter }
                    """
                    result = subprocess.run(
                        ["powershell", "-Command", ps_cmd],
                        capture_output=True, text=True
                    )
                    
                    possible_letters = result.stdout.strip().split('\n')
                    for letter in possible_letters:
                        if letter.strip():
                            drive_letter = letter.strip()
                            self._log(f"Found removable drive: {drive_letter}:")
                            break
                
                # If still don't have a drive letter, ask the user
                if not drive_letter:
                    self._log("Could not automatically determine drive letter")
                    
                    # Show a message box to ask for the drive letter
                    drive_letter_window = tk.Toplevel(self)
                    drive_letter_window.title("Drive Letter Required")
                    drive_letter_window.transient(self)
                    drive_letter_window.grab_set()
                    
                    tk.Label(
                        drive_letter_window, 
                        text="Could not automatically determine the USB drive letter.\n\n"
                             "Check Windows Explorer for the newly formatted USB drive letter.\n\n"
                             "Enter the drive letter (e.g., E):"
                    ).pack(pady=10, padx=10)
                    
                    letter_var = tk.StringVar()
                    entry = tk.Entry(drive_letter_window, textvariable=letter_var, width=5)
                    entry.pack(pady=5)
                    entry.focus_set()
                    
                    def on_ok():
                        nonlocal drive_letter
                        drive_letter = letter_var.get().strip().upper()
                        if drive_letter and len(drive_letter) == 1 and drive_letter.isalpha():
                            drive_letter_window.destroy()
                        else:
                            # The user is supposed to enter a single letter only 
                            messagebox.showerror("Invalid Input", "Please enter a single letter")
                    
                    tk.Button(drive_letter_window, text="OK", command=on_ok).pack(pady=10)
                    
                    # Center the dialog
                    drive_letter_window.update_idletasks()
                    width = drive_letter_window.winfo_width()
                    height = drive_letter_window.winfo_height()
                    x = (drive_letter_window.winfo_screenwidth() // 2) - (width // 2)
                    y = (drive_letter_window.winfo_screenheight() // 2) - (height // 2)
                    drive_letter_window.geometry(f"{width}x{height}+{x}+{y}")
                    
                    # Wait for the dialog to be closed
                    self.wait_window(drive_letter_window)
                
                if not drive_letter:
                    self._log("No drive letter provided")
                    self.status_var.set("USB write cancelled")
                    self._on_write_complete(False)
                    return
                
                # Ensure drive letter is properly formatted. We don't want to mess this up :)
                if not drive_letter.endswith(':'):
                    drive_letter = f"{drive_letter}:"
                
                self._log(f"Using drive letter: {drive_letter}")
                
                # Mount ISO and copy files
                self._log("Mounting ISO and copying files")
                # ps = powershell
                ps_cmd = f"""
                $iso = Mount-DiskImage -ImagePath '{self.iso_path}' -PassThru
                $isoDrive = ($iso | Get-Volume).DriveLetter
                Copy-Item -Path "$($isoDrive):\\*" -Destination "{drive_letter}\\" -Recurse -Force
                Dismount-DiskImage -ImagePath '{self.iso_path}'
                """
                
                self._log("Starting file copy - this may take several minutes")
                copy_process = subprocess.Popen(
                    ["powershell", "-Command", ps_cmd],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )
                
                # Set progress to indicate copying has started
                self.progress_var.set(10)
                
                for line in copy_process.stdout:
                    self._log(line.strip())
                    # Increment progress to show activity
                    current = self.progress_var.get()
                    if current < 90:  # Don't go above 90% until complete. Faking progress is bad lol.
                        self.progress_var.set(current + 1)
                
                copy_process.wait()
                
                if copy_process.returncode == 0:
                    self._log(f"ISO successfully written to USB drive {drive_letter}")
                    self.status_var.set("USB write completed")
                    self.progress_var.set(100)
                    self._on_write_complete(True)
                else:
                    self._log(f"Copy failed with code {copy_process.returncode}")
                    self.status_var.set("USB write failed")
                    self._on_write_complete(False)
                    
        
                    
        except Exception as e:
            self._log(f"Error writing ISO: {e}")
            self.after(0, lambda: self.status_var.set(f"Error: {str(e)[:50]}..."))
            self._on_write_complete(False)
            
    def _on_write_complete(self, success):
        """Called when the write process completes successfully."""
        # Yippee! We're almost done here.
        
        # Re-enable buttons
        self.after(0, lambda: self.download_btn.config(state=tk.NORMAL))
        self.after(0, lambda: self.write_btn.config(state=tk.NORMAL))
        self.after(0, lambda: self.close_btn.config(state=tk.NORMAL))
        
        # Ask about reboot if the writing was successful
        if success:
            if messagebox.askyesno("Reboot", "Do you want to reboot now to select USB boot device?"):
                try:
                    # Reboot into advanced startup options. The user can then select the USB device from there.
                    subprocess.run(["shutdown", "/r", "/o", "/f", "/t", "0"], check=True)
                except Exception as e:
                    self._log(f"Failed to reboot: {e}")


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()