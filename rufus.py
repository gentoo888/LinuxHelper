import os
import subprocess
import webbrowser
from pathlib import Path
from tkinter import messagebox


def get_rufus_path():
    downloads_path = Path.home() / "Downloads"
    matches = sorted(downloads_path.glob("rufus*.exe"), reverse=True)
    if matches:
        return matches[0]  # Return the most recent one
    return None

def write_iso_to_usb(iso_path, usb_drive):
    
    rufus_path = get_rufus_path()
    cmd = [
        str(rufus_path),
        '--quiet',
        '--device', usb_drive,
        '--iso', str(iso_path),
        '--noninteractive'
    ]
    subprocess.run(cmd, check=True)

def ensure_rufus():
    
    rufus_path = get_rufus_path()
    if not rufus_path or not os.path.exists(rufus_path):
        if messagebox.askyesno(
            "Rufus Not Found",
            "Rufus is required to write the ISO to USB.\nDo you want to download Rufus now?"
        ):
            messagebox.showinfo(
                "Download Rufus",
                "Rufus's official website will now open in your default web browser.\n"
                "Please download and install Rufus, then restart SelfLinux."
            )
            webbrowser.open("https://rufus.ie/")
        return False
    return True
