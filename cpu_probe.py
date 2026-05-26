# Enhanced CPU probing with benchmark scoring and cross-platform support.

from typing import TypedDict, Optional
import platform
import re
import os
import subprocess

try:
    import psutil  # type: ignore
except Exception:
    psutil = None


class CpuInfo(TypedDict, total=False):
    ok: bool
    category: str
    model: str
    arch: str
    max_ghz: float
    base_ghz: float
    current_ghz: float
    cores: int
    threads: int
    score: int           # 0-100 normalized score
    generation: str      # rough age/generation hint
    vendor: str          # Intel / AMD / Apple / ARM / Unknown
    source: str
    error: str


# ---------------- Helpers ----------------
def _mhz_to_ghz(mhz: Optional[float]) -> float:
    if mhz is None:
        return 0.0
    try:
        return round(float(mhz) / 1000.0, 2)
    except Exception:
        return 0.0


def _get_model_name() -> str:
    # Linux
    try:
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if "model name" in line:
                    return line.split(":", 1)[1].strip()
    except Exception:
        pass

    # macOS
    if platform.system() == "Darwin":
        try:
            out = subprocess.check_output(
                ["sysctl", "-n", "machdep.cpu.brand_string"], text=True
            ).strip()
            if out:
                return out
        except Exception:
            pass

    # Windows registry / WMIC
    if os.name == "nt":
        try:
            out = subprocess.check_output(
                ["wmic", "cpu", "get", "Name"], text=True
            ).splitlines()
            for line in out:
                line = line.strip()
                if line and line.lower() != "name":
                    return line
        except Exception:
            pass

    return platform.processor() or platform.uname().processor or "Unknown CPU"


def _detect_vendor(model: str) -> str:
    m = model.lower()
    if "intel" in m:
        return "Intel"
    if "amd" in m or "ryzen" in m or "epyc" in m or "threadripper" in m:
        return "AMD"
    if "apple" in m or "m1" in m or "m2" in m or "m3" in m or "m4" in m:
        return "Apple"
    if "arm" in m or "cortex" in m or "snapdragon" in m:
        return "ARM"
    return "Unknown"


def _detect_generation(model: str) -> str:
    """Rough generation hint - useful for tier guessing."""
    m = model.lower()
    # Intel core ix-NNNN family: 1st digit usually maps to generation (>=10 multi-digit)
    intel_match = re.search(r"i[3579]-(\d{4,5})", m)
    if intel_match:
        digits = intel_match.group(1)
        gen = digits[0] if len(digits) == 4 else digits[:2]
        return f"Intel Core {gen}th gen"
    # Ryzen 5 5600X -> 5000 series
    ryzen_match = re.search(r"ryzen\s*[3579]\s*(\d)\d{3}", m)
    if ryzen_match:
        return f"Ryzen {ryzen_match.group(1)}000 series"
    # Apple M1/M2/M3/M4
    apple_match = re.search(r"apple\s*m(\d)", m)
    if apple_match:
        return f"Apple M{apple_match.group(1)}"
    return ""


def _score_cpu(model: str, max_ghz: float, cores: int, threads: int) -> int:
    """
    Compute a 0-100 score combining clock, cores, threads, and known model heuristics.
    """
    # Base score: clock + parallelism
    clock_score = min(40, max_ghz * 10)          # 4.0 GHz -> 40
    core_score = min(30, cores * 3)              # 10 cores -> 30
    thread_score = min(15, max(0, (threads - cores)) * 2 + min(15, threads))
    thread_score = min(15, thread_score)

    base = clock_score + core_score + thread_score  # max 85

    # Model bonus
    m = model.lower()
    bonus = 0
    if any(k in m for k in ["i9", "ryzen 9", "threadripper", "epyc", "xeon w", "m3 max", "m2 ultra", "m3 ultra", "m4 max"]):
        bonus = 15
    elif any(k in m for k in ["i7", "ryzen 7", "m1 pro", "m2 pro", "m3 pro", "m4 pro"]):
        bonus = 10
    elif any(k in m for k in ["i5", "ryzen 5", "m1", "m2", "m3", "m4"]):
        bonus = 6
    elif any(k in m for k in ["i3", "ryzen 3"]):
        bonus = 3
    elif any(k in m for k in ["pentium", "celeron", "atom"]):
        bonus = -10
    elif "n100" in m or "n200" in m or "n95" in m or "n97" in m:
        bonus = -5  # low-power Intel Alder Lake-N

    score = max(0, min(100, int(base + bonus)))
    return score


def _category_from_score(score: int) -> str:
    if score >= 85:
        return "Extreme"
    if score >= 70:
        return "High-end"
    if score >= 50:
        return "Mid-range"
    if score >= 30:
        return "Low-end"
    return "Very-low"


# ---------------- Public API ----------------
def probe_cpu() -> CpuInfo:
    try:
        if psutil is not None:
            freq = psutil.cpu_freq()
            current_ghz = _mhz_to_ghz(freq.current if freq else None)
            base_ghz = _mhz_to_ghz(freq.min if freq else None)
            max_ghz = _mhz_to_ghz(freq.max if freq else None)
            cores = psutil.cpu_count(logical=False) or 1
            threads = psutil.cpu_count(logical=True) or cores
        else:
            current_ghz = base_ghz = max_ghz = 0.0
            cores = os.cpu_count() or 1
            threads = cores

        # Some VMs/containers report max_ghz=0 - fallback to current
        if not max_ghz and current_ghz:
            max_ghz = current_ghz

        model = _get_model_name()
        arch = platform.machine()
        vendor = _detect_vendor(model)
        generation = _detect_generation(model)
        score = _score_cpu(model, max_ghz, cores, threads)
        category = _category_from_score(score)

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
            "score": score,
            "generation": generation,
            "vendor": vendor,
            "source": "psutil+platform" if psutil else "platform",
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
            "score": 0,
            "generation": "",
            "vendor": "Unknown",
            "source": "error",
            "error": str(e),
        }


if __name__ == "__main__":
    import json
    print(json.dumps(probe_cpu(), indent=2))
