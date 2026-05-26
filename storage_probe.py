# Enhanced storage probe - cross-platform with NVMe/SSD/HDD detection and free space.

import subprocess
import os
import re
import platform
import shutil


def _run(cmd, shell=False, timeout=10):
    try:
        return subprocess.check_output(
            cmd, shell=shell, text=True, timeout=timeout, stderr=subprocess.DEVNULL
        )
    except Exception:
        return ""


def _categorize(media_type: str, model: str) -> str:
    s = (media_type + " " + model).lower()
    if "nvme" in s:
        return "high"
    if "ssd" in s or "solid state" in s:
        return "fast"
    if "hdd" in s or "hard disk" in s or "rotational" in s or "5400" in s or "7200" in s:
        return "low"
    if "emmc" in s or "sd card" in s:
        return "low"
    return "mid"


def _probe_windows():
    system_drive = os.environ.get("SystemDrive", "C:")[0]
    ps = f"""
    $disk = Get-PhysicalDisk | Where-Object {{
        $_.DeviceId -eq (Get-Partition -DriveLetter '{system_drive}' | Get-Disk).Number
    }} | Select-Object -First 1
    if ($disk) {{
        $size = [math]::Round($disk.Size / 1GB, 2)
        "$($disk.MediaType)|$($disk.BusType)|$($disk.FriendlyName)|$size"
    }}
    """
    out = _run(["powershell", "-NoProfile", "-Command", ps]).strip()
    if out:
        parts = out.split("|")
        if len(parts) >= 4:
            media_type = parts[0].strip() or "Unknown"
            bus = parts[1].strip()
            model = parts[2].strip()
            try:
                size_gb = float(parts[3].strip())
            except Exception:
                size_gb = 0.0

            # Free space on system drive
            try:
                total, used, free = shutil.disk_usage(f"{system_drive}:\\")
                free_gb = round(free / (1024 ** 3), 2)
            except Exception:
                free_gb = 0.0

            type_str = f"{model} ({media_type}/{bus})"
            category = _categorize(f"{media_type} {bus}", model)
            return {
                "ok": True,
                "type": type_str,
                "model": model,
                "media_type": media_type,
                "bus": bus,
                "size_gb": size_gb,
                "free_gb": free_gb,
                "category": category,
                "source": "powershell",
            }
    return None


def _probe_linux():
    # Find root device
    root_dev = ""
    out = _run(["findmnt", "-n", "-o", "SOURCE", "/"])
    root_dev = out.strip()
    # Strip partition number (e.g. /dev/nvme0n1p2 -> /dev/nvme0n1, /dev/sda1 -> /dev/sda)
    base_dev = root_dev
    if base_dev.startswith("/dev/"):
        m = re.match(r"(/dev/(nvme\d+n\d+|mmcblk\d+|sd[a-z]+|vd[a-z]+|hd[a-z]+))", base_dev)
        if m:
            base_dev = m.group(1)

    model = "Unknown"
    rotational = None
    size_gb = 0.0
    media_type = "Unknown"

    dev_basename = base_dev.replace("/dev/", "")
    sysfs = f"/sys/block/{dev_basename}"
    try:
        if os.path.exists(f"{sysfs}/device/model"):
            with open(f"{sysfs}/device/model") as f:
                model = f.read().strip()
        if os.path.exists(f"{sysfs}/queue/rotational"):
            with open(f"{sysfs}/queue/rotational") as f:
                rotational = f.read().strip() == "1"
        if os.path.exists(f"{sysfs}/size"):
            with open(f"{sysfs}/size") as f:
                sectors = int(f.read().strip())
                size_gb = round(sectors * 512 / (1024 ** 3), 2)
    except Exception:
        pass

    if "nvme" in dev_basename:
        media_type = "NVMe"
    elif rotational is False:
        media_type = "SSD"
    elif rotational is True:
        media_type = "HDD"
    elif "mmcblk" in dev_basename:
        media_type = "eMMC"

    try:
        total, used, free = shutil.disk_usage("/")
        free_gb = round(free / (1024 ** 3), 2)
    except Exception:
        free_gb = 0.0

    type_str = f"{model} ({media_type})"
    category = _categorize(media_type, model)

    return {
        "ok": True,
        "type": type_str,
        "model": model,
        "media_type": media_type,
        "bus": media_type,
        "size_gb": size_gb,
        "free_gb": free_gb,
        "category": category,
        "source": "sysfs",
    }


def _probe_macos():
    out = _run(["diskutil", "info", "/"])
    model = "Unknown"
    media_type = "Unknown"
    size_gb = 0.0

    for line in out.splitlines():
        if "Device / Media Name" in line or "Media Name" in line:
            model = line.split(":", 1)[-1].strip()
        elif "Solid State" in line and "Yes" in line:
            media_type = "SSD"
        elif "Protocol" in line:
            proto = line.split(":", 1)[-1].strip()
            if "PCI" in proto or "NVMe" in proto:
                media_type = "NVMe"
            elif "SATA" in proto and media_type == "Unknown":
                media_type = "SSD"
        elif "Disk Size" in line:
            m = re.search(r"\(([\d\.]+)\s*GB\)", line) or re.search(r"([\d\.]+)\s*GB", line)
            if m:
                try:
                    size_gb = float(m.group(1))
                except Exception:
                    pass
    try:
        total, used, free = shutil.disk_usage("/")
        free_gb = round(free / (1024 ** 3), 2)
    except Exception:
        free_gb = 0.0

    type_str = f"{model} ({media_type})"
    category = _categorize(media_type, model)
    return {
        "ok": True,
        "type": type_str,
        "model": model,
        "media_type": media_type,
        "bus": media_type,
        "size_gb": size_gb,
        "free_gb": free_gb,
        "category": category,
        "source": "diskutil",
    }


def probe_storage_type():
    """
    Probe primary storage. Returns:
        ok, type, model, media_type, bus, size_gb, free_gb, category, source
    Category: 'high' (NVMe), 'fast' (SSD), 'mid' (unknown), 'low' (HDD/eMMC)
    """
    try:
        sys = platform.system().lower()
        if sys == "windows":
            res = _probe_windows()
            if res:
                return res
        elif sys == "linux":
            return _probe_linux()
        elif sys == "darwin":
            return _probe_macos()
        return {"ok": False, "type": None, "category": "unknown", "error": "unsupported os"}
    except Exception as e:
        return {"ok": False, "type": None, "category": "unknown", "error": str(e)}


if __name__ == "__main__":
    import json
    print(json.dumps(probe_storage_type(), indent=2))
