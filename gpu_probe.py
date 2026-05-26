# Enhanced GPU probe - cross-platform (Windows / Linux / macOS), with VRAM and category scoring.

import platform
import subprocess
import re
import os


def _run(cmd, shell=False, timeout=10):
    try:
        out = subprocess.check_output(
            cmd, shell=shell, text=True, timeout=timeout,
            stderr=subprocess.DEVNULL
        )
        return out
    except Exception:
        return ""


def _detect_windows_gpu():
    out = ""
    # Try PowerShell first (more reliable on modern Windows)
    out = _run([
        "powershell", "-NoProfile", "-Command",
        "Get-CimInstance Win32_VideoController | "
        "Select-Object Name,AdapterRAM | "
        "ForEach-Object { \"$($_.Name)|$($_.AdapterRAM)\" }"
    ])
    if not out.strip():
        # Fallback to WMIC
        out = _run(["wmic", "path", "win32_VideoController", "get", "Name,AdapterRAM", "/format:csv"])

    gpus = []
    for line in out.splitlines():
        line = line.strip()
        if not line or "Name" in line and "AdapterRAM" in line:
            continue
        parts = line.split("|") if "|" in line else line.split(",")
        # Filter out empty parts
        parts = [p.strip() for p in parts if p.strip()]
        if not parts:
            continue
        name = parts[0]
        vram_bytes = 0
        for p in parts[1:]:
            if p.isdigit():
                vram_bytes = int(p)
                break
        if name and name.lower() not in ("name", "node"):
            gpus.append({"name": name, "vram_mb": vram_bytes // (1024 * 1024) if vram_bytes else 0})
    return gpus


def _detect_linux_gpu():
    gpus = []
    # Try lspci for VGA/3D controllers
    out = _run(["lspci", "-mm"])
    if not out:
        out = _run("lspci", shell=True)
    for line in out.splitlines():
        if re.search(r"VGA compatible controller|3D controller|Display controller", line, re.I):
            # Try to extract a clean name
            m = re.search(r'"([^"]+)"\s+"([^"]+)"', line)
            if m:
                name = f"{m.group(1)} {m.group(2)}"
            else:
                # Fallback parse
                parts = line.split(":")
                name = parts[-1].strip() if parts else line
            gpus.append({"name": name, "vram_mb": 0})

    # Try nvidia-smi for VRAM
    nv = _run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"])
    if nv:
        # Replace VRAM/name from nvidia-smi
        nvidia_gpus = []
        for line in nv.splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 2 and parts[1].isdigit():
                nvidia_gpus.append({"name": parts[0], "vram_mb": int(parts[1])})
        if nvidia_gpus:
            # Merge: prefer nvidia-smi entries
            merged = nvidia_gpus + [g for g in gpus if "nvidia" not in g["name"].lower()]
            return merged
    return gpus


def _detect_macos_gpu():
    out = _run(["system_profiler", "SPDisplaysDataType"])
    gpus = []
    current = None
    for line in out.splitlines():
        line_strip = line.strip()
        # Each GPU section starts with "Chipset Model:" or device name
        m = re.match(r"Chipset Model:\s*(.+)", line_strip)
        if m:
            if current:
                gpus.append(current)
            current = {"name": m.group(1).strip(), "vram_mb": 0}
            continue
        m = re.match(r"VRAM\s*\(.*?\):\s*([0-9.]+)\s*(MB|GB)", line_strip)
        if m and current:
            v = float(m.group(1))
            if m.group(2) == "GB":
                v *= 1024
            current["vram_mb"] = int(v)
    if current:
        gpus.append(current)
    return gpus


# ---------------- Categorization ----------------
WEAK_KEYWORDS = [
    # Intel integrated
    "intel hd", "intel uhd", "intel iris", "intel graphics", "intel gma",
    "intel arc a310", "intel arc a350m", "intel arc a370m",
    # AMD APUs / old
    "vega 3", "vega 5", "vega 6", "vega 7", "vega 8",
    "radeon r2", "radeon r3", "radeon r4", "radeon r5",
    "radeon hd 5", "radeon hd 6", "radeon hd 7000", "radeon hd 7400",
    "amd radeon graphics", "radeon (tm) graphics",
    # NVIDIA mobile / low-end
    "mx110", "mx130", "mx150", "mx230", "mx250", "mx330", "mx350", "mx450", "mx550",
    "geforce 210", "geforce 310", "geforce gt 6", "geforce gt 7", "geforce gt 8",
    "geforce gt 9", "geforce 9", "geforce 8",
    "geforce 920", "geforce 930", "geforce 940",
    # Generic
    "integrated", "onboard", "shared graphics", "softpipe", "llvmpipe", "swrast",
]

MID_KEYWORDS = [
    # Intel Arc (mid)
    "intel arc a380", "intel arc a550", "intel arc a730", "intel arc a770",
    # NVIDIA mid
    "gtx 750", "gtx 760", "gtx 770", "gtx 780",
    "gtx 950", "gtx 960", "gtx 970", "gtx 980",
    "gtx 1050", "gtx 1060", "gtx 1070",
    "gtx 1630", "gtx 1650", "gtx 1660",
    "rtx 2050", "rtx 2060", "rtx 3050", "rtx 4050",
    "rtx 3060",  # mid-high but reasonable
    # AMD mid
    "rx 460", "rx 470", "rx 480", "rx 550", "rx 560", "rx 570", "rx 580", "rx 590",
    "rx 5500", "rx 5600", "rx 6500", "rx 6600",
    "radeon r7", "radeon r9",
    # Apple M-series base
    "apple m1", "apple m2", "apple m3", "apple m4",
    # Workstation mid
    "quadro k", "quadro m", "quadro p", "quadro t",
]

STRONG_KEYWORDS = [
    # NVIDIA strong
    "gtx 1080",
    "rtx 2070", "rtx 2080",
    "rtx 3070", "rtx 3080", "rtx 3090",
    "rtx 4060 ti", "rtx 4070", "rtx 4080", "rtx 4090",
    "rtx 5070", "rtx 5080", "rtx 5090",
    "titan", "tesla", "a100", "h100", "h200", "l40", "rtx a", "rtx 6000",
    # AMD strong
    "rx 6700", "rx 6800", "rx 6900", "rx 6950",
    "rx 7700", "rx 7800", "rx 7900",
    "radeon vii", "instinct",
    # Apple high
    "m1 pro", "m1 max", "m1 ultra",
    "m2 pro", "m2 max", "m2 ultra",
    "m3 pro", "m3 max", "m3 ultra",
    "m4 pro", "m4 max",
]


def _categorize(name: str, vram_mb: int) -> str:
    if not name:
        return "nogpu"
    n = name.lower()

    # Software/virtual
    if any(k in n for k in ["llvmpipe", "softpipe", "swrast", "virtio", "vmware svga", "microsoft basic display"]):
        return "weak"

    # Strong first (most specific)
    if any(k in n for k in STRONG_KEYWORDS):
        return "strong"
    if any(k in n for k in MID_KEYWORDS):
        return "mid"
    if any(k in n for k in WEAK_KEYWORDS):
        return "weak"

    # Heuristics by VRAM
    if vram_mb >= 8000:
        return "strong"
    if vram_mb >= 4000:
        return "mid"
    if vram_mb >= 1500:
        return "weak"

    # Pattern fallbacks
    if re.search(r"rtx\s*[3-9]0\d{2}", n):
        return "strong"
    if re.search(r"rtx\s*\d{4}", n) or re.search(r"gtx\s*1[0-9]\d{2}", n):
        return "mid"
    if "intel" in n:
        return "weak"

    return "unknown"


def probe_gpu():
    """
    Cross-platform GPU probe.
    Returns: {ok, name, category, vram_mb, all_gpus, source, error}
    """
    sys = platform.system().lower()
    try:
        if sys == "windows":
            gpus = _detect_windows_gpu()
            source = "wmi"
        elif sys == "linux":
            gpus = _detect_linux_gpu()
            source = "lspci/nvidia-smi"
        elif sys == "darwin":
            gpus = _detect_macos_gpu()
            source = "system_profiler"
        else:
            gpus = []
            source = "unsupported"

        # Filter out empty entries
        gpus = [g for g in gpus if g.get("name")]

        if not gpus:
            return {
                "ok": True,
                "name": None,
                "category": "nogpu",
                "vram_mb": 0,
                "all_gpus": [],
                "source": source,
            }

        # Pick the "best" GPU - prefer discrete (non-Intel/iGPU) and largest VRAM
        def _gpu_priority(g):
            n = g["name"].lower()
            integrated = any(k in n for k in ["intel", "vega", "radeon graphics", "apple m"])
            return (0 if integrated else 1, g.get("vram_mb", 0))

        primary = max(gpus, key=_gpu_priority)
        category = _categorize(primary["name"], primary.get("vram_mb", 0))

        return {
            "ok": True,
            "name": primary["name"],
            "category": category,
            "vram_mb": primary.get("vram_mb", 0),
            "all_gpus": gpus,
            "source": source,
            "error": "",
        }
    except Exception as e:
        return {
            "ok": False,
            "name": None,
            "category": "nogpu",
            "vram_mb": 0,
            "all_gpus": [],
            "source": "error",
            "error": str(e),
        }


if __name__ == "__main__":
    import json
    print(json.dumps(probe_gpu(), indent=2))
