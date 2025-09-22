from typing import TypedDict, Optional
import math
import platform
import psutil

class CpuInfo(TypedDict):
    ok: bool
    category: str
    model: str
    arch: str
    max_ghz: float
    base_ghz: float
    current_ghz: float
    cores: int
    threads: int
    source: str
    error: str

def _mhz_to_ghz(mhz: Optional[float]) -> float:
    if mhz is None:
        return 0.0
    return round(float(mhz) / 1000.0, 2)

def _categorize(max_ghz: float, cores: int, threads: int) -> str:
    if max_ghz >= 4.0 or cores >= 16:
        return "Extreme"
    elif max_ghz >= 3.0 and cores >= 8:
        return "High-end"
    elif max_ghz >= 2.0 and cores >= 4:
        return "Mid-range"
    else:
        return "Low-end"

def _get_model_name() -> str:
    try:
        # Linux
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if "model name" in line:
                    return line.split(":", 1)[1].strip()
    except FileNotFoundError:
        pass
    return platform.processor() or platform.uname().processor or "Unknown CPU"

def probe_cpu() -> CpuInfo:
    try:
        freq = psutil.cpu_freq()
        current_ghz = _mhz_to_ghz(freq.current if freq else None)
        base_ghz = _mhz_to_ghz(freq.min if freq else None)
        max_ghz = _mhz_to_ghz(freq.max if freq else None)
        cores = psutil.cpu_count(logical=False) or 1
        threads = psutil.cpu_count(logical=True) or cores
        model = _get_model_name()
        arch = platform.machine()
        category = _categorize(max_ghz, cores, threads)

        return {
            "ok": True,
            "category": category,
            "model": model,
            "arch": arch,
            "max_ghz": max_ghz,
            "base_ghz": base_ghz,
            "current_ghz": current_ghz,
            "cores": cores,
            "threads": threads,
            "source": "psutil+platform",
            "error": "",
        }
    except Exception as e:
        return {
            "ok": False,
            "category": "Unknown",
            "model": "",
            "arch": "",
            "max_ghz": 0.0,
            "base_ghz": 0.0,
            "current_ghz": 0.0,
            "cores": 0,
            "threads": 0,
            "source": "error",
            "error": str(e),
        }

if __name__ == "__main__":
    print(probe_cpu())

