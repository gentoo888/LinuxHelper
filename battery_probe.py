# Battery probe - detects laptop/desktop and battery health

import platform
import os

try:
    import psutil  # type: ignore
except Exception:
    psutil = None


def probe_battery():
    """
    Returns: { ok, has_battery, percent, plugged, is_laptop, source, error }
    is_laptop heuristic: battery present == laptop.
    """
    try:
        if psutil is not None and hasattr(psutil, "sensors_battery"):
            b = psutil.sensors_battery()
            if b is not None:
                return {
                    "ok": True,
                    "has_battery": True,
                    "percent": round(float(b.percent), 1),
                    "plugged": bool(b.power_plugged),
                    "is_laptop": True,
                    "source": "psutil",
                    "error": "",
                }
        # Linux sysfs fallback
        if platform.system().lower() == "linux":
            for name in os.listdir("/sys/class/power_supply") if os.path.isdir("/sys/class/power_supply") else []:
                if name.lower().startswith("bat"):
                    base = f"/sys/class/power_supply/{name}"
                    try:
                        with open(f"{base}/capacity") as f:
                            pct = float(f.read().strip())
                    except Exception:
                        pct = 0.0
                    plugged = False
                    try:
                        with open(f"{base}/status") as f:
                            plugged = "Charging" in f.read() or "Full" in f.read()
                    except Exception:
                        pass
                    return {
                        "ok": True,
                        "has_battery": True,
                        "percent": pct,
                        "plugged": plugged,
                        "is_laptop": True,
                        "source": "sysfs",
                        "error": "",
                    }
        return {
            "ok": True,
            "has_battery": False,
            "percent": 0.0,
            "plugged": True,
            "is_laptop": False,
            "source": "none",
            "error": "",
        }
    except Exception as e:
        return {
            "ok": False,
            "has_battery": False,
            "percent": 0.0,
            "plugged": True,
            "is_laptop": False,
            "source": "error",
            "error": str(e),
        }


if __name__ == "__main__":
    import json
    print(json.dumps(probe_battery(), indent=2))
