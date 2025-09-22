from typing import TypedDict
import math
import re
from pathlib import Path

class RamInfo(TypedDict):
    ok: bool
    total_gb: float
    available_gb: float
    used_percent: float
    source: str   # "psutil" | "procfs"

def _bytes_to_gb(b: int) -> float:
    return round(b / (1024**3), 2)

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

    out: RamInfo = {
        "ok": True,
        "total_gb": _bytes_to_gb(total_b),
        "available_gb": _bytes_to_gb(avail_b),
        "used_percent": float(used_percent),
        "source": "procfs",
    }
    if not (0 <= out["available_gb"] <= out["total_gb"] <= 100*1024 and 0 <= out["used_percent"] <= 100 and
            all(map(math.isfinite, (out["total_gb"], out["available_gb"], out["used_percent"])))):
        return {"ok": False, "total_gb": 0.0, "available_gb": 0.0, "used_percent": 0.0, "source": "procfs"}
    return out

def probe_ram() -> RamInfo:
    try:
        import psutil  # type: ignore
        vm = psutil.virtual_memory()
        out: RamInfo = {
            "ok": True,
            "total_gb": _bytes_to_gb(vm.total),
            "available_gb": _bytes_to_gb(vm.available),
            "used_percent": float(vm.percent),
            "source": "psutil",
        }
        if not (0 <= out["available_gb"] <= out["total_gb"] and 0 <= out["used_percent"] <= 100 and
                all(map(math.isfinite, (out["total_gb"], out["available_gb"], out["used_percent"])))):
            return {"ok": False, "total_gb": 0.0, "available_gb": 0.0, "used_percent": 0.0, "source": "psutil"}
        return out
    except Exception:
        return _probe_with_procfs()

if __name__ == "__main__":
    d = probe_ram()
    assert d["ok"], "RAM probe failed"
    assert 0 <= d["available_gb"] <= d["total_gb"]
    assert 0 <= d["used_percent"] <= 100
    print(d)

