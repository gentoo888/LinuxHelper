# Enhanced RAM probe with extra optional info (speed, slots) where possible.

from typing import TypedDict, Optional
import math
import re
import os
import platform
import subprocess
from pathlib import Path


class RamInfo(TypedDict, total=False):
    ok: bool
    total_gb: float
    available_gb: float
    used_percent: float
    speed_mhz: int
    type: str          # DDR3 / DDR4 / DDR5 / Unknown
    slots_used: int
    source: str


def _bytes_to_gb(b: int) -> float:
    return round(b / (1024 ** 3), 2)


def _run(cmd, timeout=10):
    try:
        return subprocess.check_output(cmd, text=True, timeout=timeout, stderr=subprocess.DEVNULL)
    except Exception:
        return ""


def _probe_extra_windows():
    out = _run([
        "powershell", "-NoProfile", "-Command",
        "Get-CimInstance Win32_PhysicalMemory | "
        "ForEach-Object { \"$($_.Speed)|$($_.SMBIOSMemoryType)\" }"
    ])
    speed = 0
    type_str = "Unknown"
    slots = 0
    type_map = {"20": "DDR", "21": "DDR2", "24": "DDR3", "26": "DDR4", "34": "DDR5"}
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        slots += 1
        parts = line.split("|")
        try:
            sp = int(parts[0]) if parts[0].isdigit() else 0
            if sp > speed:
                speed = sp
        except Exception:
            pass
        if len(parts) > 1 and parts[1] in type_map:
            type_str = type_map[parts[1]]
    return speed, type_str, slots


def _probe_extra_linux():
    speed = 0
    type_str = "Unknown"
    slots = 0
    out = _run(["dmidecode", "--type", "memory"])
    if out:
        for block in out.split("\n\n"):
            if "Memory Device" in block and "Size:" in block:
                # Skip empty slots
                if re.search(r"Size:\s*No Module Installed", block):
                    continue
                slots += 1
                m = re.search(r"Speed:\s*(\d+)\s*MT/s", block) or re.search(r"Speed:\s*(\d+)", block)
                if m:
                    sp = int(m.group(1))
                    if sp > speed:
                        speed = sp
                m = re.search(r"Type:\s*(DDR\d?)", block)
                if m:
                    type_str = m.group(1)
    return speed, type_str, slots


def _probe_with_procfs() -> RamInfo:
    p = Path("/proc/meminfo")
    if not p.exists():
        return {"ok": False, "total_gb": 0.0, "available_gb": 0.0, "used_percent": 0.0, "source": "procfs"}

    text = p.read_text()

    def get_kb(key: str):
        m = re.search(rf"^{key}:\s+(\d+)\s+kB", text, re.MULTILINE)
        return int(m.group(1)) if m else None

    mt = get_kb("MemTotal")
    ma = get_kb("MemAvailable")
    if not mt or not ma or ma > mt:
        return {"ok": False, "total_gb": 0.0, "available_gb": 0.0, "used_percent": 0.0, "source": "procfs"}

    total_b = mt * 1024
    avail_b = ma * 1024
    used_percent = round(100.0 * (1.0 - (avail_b / total_b)), 1)

    return {
        "ok": True,
        "total_gb": _bytes_to_gb(total_b),
        "available_gb": _bytes_to_gb(avail_b),
        "used_percent": float(used_percent),
        "speed_mhz": 0,
        "type": "Unknown",
        "slots_used": 0,
        "source": "procfs",
    }


def probe_ram() -> RamInfo:
    out: RamInfo = {"ok": False, "total_gb": 0.0, "available_gb": 0.0, "used_percent": 0.0,
                    "speed_mhz": 0, "type": "Unknown", "slots_used": 0, "source": ""}
    try:
        import psutil  # type: ignore
        vm = psutil.virtual_memory()
        out = {
            "ok": True,
            "total_gb": _bytes_to_gb(vm.total),
            "available_gb": _bytes_to_gb(vm.available),
            "used_percent": float(vm.percent),
            "speed_mhz": 0,
            "type": "Unknown",
            "slots_used": 0,
            "source": "psutil",
        }
    except Exception:
        out = _probe_with_procfs()

    if not out.get("ok"):
        return out

    # Try to enrich with type/speed
    try:
        sysname = platform.system().lower()
        if sysname == "windows":
            sp, t, sl = _probe_extra_windows()
        elif sysname == "linux":
            sp, t, sl = _probe_extra_linux()
        else:
            sp, t, sl = 0, "Unknown", 0
        out["speed_mhz"] = sp
        out["type"] = t
        out["slots_used"] = sl
    except Exception:
        pass

    if not (0 <= out["available_gb"] <= out["total_gb"] and 0 <= out["used_percent"] <= 100 and
            all(map(math.isfinite, (out["total_gb"], out["available_gb"], out["used_percent"])))):
        return {"ok": False, "total_gb": 0.0, "available_gb": 0.0, "used_percent": 0.0, "source": "invalid"}
    return out


if __name__ == "__main__":
    import json
    print(json.dumps(probe_ram(), indent=2))
