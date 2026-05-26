# recommender_engine.py
# Score-based recommendation engine that considers:
# - Hardware (CPU/GPU/RAM/storage scores + battery)
# - User preferences (usage, visual, experience, privacy, updates,
#   localization, theme, gaming demand, programming language family,
#   software freedom, stability vs cutting-edge, language)
#
# Returns a ranked list of distros with explanations. (which is more badass)

from typing import Any, Dict, List

# ---------- Distro feature matrix ----------
# Each distro has a feature vector of attributes.
# Scores from 0-10 unless noted.
DISTROS: Dict[str, Dict[str, Any]] = {
    "Ubuntu LTS": {
        "min_ram_gb": 2.0,
        "ideal_ram_gb": 4.0,
        "min_storage_gb": 25.0,
        "weight_low_hw": 4,
        "weight_mid_hw": 8,
        "weight_high_hw": 7,
        "beginner": 9,
        "stability": 9,
        "cutting_edge": 4,
        "office": 9,
        "development": 8,
        "gaming": 6,
        "creative": 7,
        "visual_polish": 7,
        "privacy": 5,
        "free_software_purity": 4,
        "lts": 10,
        "rolling": 0,
        "desktop": "GNOME",
        "package_mgr": "APT/Snap",
        "good_for_old_hw": False,
        "battery_friendly": 7,
        "summary": "Wide ecosystem with long-term support; safe default.",
    },
    "Linux Mint Cinnamon": {
        "min_ram_gb": 2.0,
        "ideal_ram_gb": 4.0,
        "min_storage_gb": 20.0,
        "weight_low_hw": 5,
        "weight_mid_hw": 9,
        "weight_high_hw": 7,
        "beginner": 10,
        "stability": 9,
        "cutting_edge": 3,
        "office": 9,
        "development": 7,
        "gaming": 6,
        "creative": 6,
        "visual_polish": 8,
        "privacy": 6,
        "free_software_purity": 5,
        "lts": 9,
        "rolling": 0,
        "desktop": "Cinnamon",
        "package_mgr": "APT/Flatpak",
        "good_for_old_hw": False,
        "battery_friendly": 7,
        "summary": "Newcomer-friendly, Windows-like, stable Ubuntu base.",
    },
    "Linux Mint XFCE": {
        "min_ram_gb": 1.0,
        "ideal_ram_gb": 2.0,
        "min_storage_gb": 15.0,
        "weight_low_hw": 9,
        "weight_mid_hw": 7,
        "weight_high_hw": 5,
        "beginner": 9,
        "stability": 9,
        "cutting_edge": 3,
        "office": 9,
        "development": 7,
        "gaming": 5,
        "creative": 5,
        "visual_polish": 6,
        "privacy": 6,
        "free_software_purity": 5,
        "lts": 9,
        "rolling": 0,
        "desktop": "XFCE",
        "package_mgr": "APT/Flatpak",
        "good_for_old_hw": True,
        "battery_friendly": 8,
        "summary": "Lightweight, balanced, perfect for older PCs.",
    },
    "Xubuntu": {
        "min_ram_gb": 1.0,
        "ideal_ram_gb": 2.0,
        "min_storage_gb": 15.0,
        "weight_low_hw": 9,
        "weight_mid_hw": 7,
        "weight_high_hw": 5,
        "beginner": 7,
        "stability": 8,
        "cutting_edge": 4,
        "office": 8,
        "development": 7,
        "gaming": 5,
        "creative": 5,
        "visual_polish": 5,
        "privacy": 5,
        "free_software_purity": 4,
        "lts": 9,
        "rolling": 0,
        "desktop": "XFCE",
        "package_mgr": "APT/Snap",
        "good_for_old_hw": True,
        "battery_friendly": 8,
        "summary": "Lightweight Ubuntu flavor with XFCE.",
    },
    "Lubuntu": {
        "min_ram_gb": 0.5,
        "ideal_ram_gb": 1.5,
        "min_storage_gb": 10.0,
        "weight_low_hw": 10,
        "weight_mid_hw": 6,
        "weight_high_hw": 3,
        "beginner": 7,
        "stability": 8,
        "cutting_edge": 4,
        "office": 7,
        "development": 5,
        "gaming": 3,
        "creative": 3,
        "visual_polish": 4,
        "privacy": 5,
        "free_software_purity": 4,
        "lts": 9,
        "rolling": 0,
        "desktop": "LXQt",
        "package_mgr": "APT",
        "good_for_old_hw": True,
        "battery_friendly": 9,
        "summary": "Very lightweight LXQt; runs on very old machines.",
    },
    "Debian XFCE": {
        "min_ram_gb": 1.0,
        "ideal_ram_gb": 2.0,
        "min_storage_gb": 15.0,
        "weight_low_hw": 9,
        "weight_mid_hw": 8,
        "weight_high_hw": 6,
        "beginner": 6,
        "stability": 10,
        "cutting_edge": 2,
        "office": 8,
        "development": 8,
        "gaming": 4,
        "creative": 4,
        "visual_polish": 5,
        "privacy": 7,
        "free_software_purity": 8,
        "lts": 10,
        "rolling": 0,
        "desktop": "XFCE",
        "package_mgr": "APT",
        "good_for_old_hw": True,
        "battery_friendly": 8,
        "summary": "Rock-solid, free-software-focused base.",
    },
    "Fedora Workstation": {
        "min_ram_gb": 4.0,
        "ideal_ram_gb": 8.0,
        "min_storage_gb": 20.0,
        "weight_low_hw": 2,
        "weight_mid_hw": 8,
        "weight_high_hw": 9,
        "beginner": 6,
        "stability": 7,
        "cutting_edge": 9,
        "office": 8,
        "development": 10,
        "gaming": 7,
        "creative": 8,
        "visual_polish": 8,
        "privacy": 7,
        "free_software_purity": 7,
        "lts": 4,
        "rolling": 5,
        "desktop": "GNOME",
        "package_mgr": "DNF/Flatpak",
        "good_for_old_hw": False,
        "battery_friendly": 6,
        "summary": "Modern toolchains; great for developers.",
    },
    "openSUSE Tumbleweed": {
        "min_ram_gb": 4.0,
        "ideal_ram_gb": 8.0,
        "min_storage_gb": 25.0,
        "weight_low_hw": 2,
        "weight_mid_hw": 7,
        "weight_high_hw": 9,
        "beginner": 5,
        "stability": 8,
        "cutting_edge": 10,
        "office": 8,
        "development": 9,
        "gaming": 7,
        "creative": 7,
        "visual_polish": 7,
        "privacy": 7,
        "free_software_purity": 6,
        "lts": 0,
        "rolling": 10,
        "desktop": "KDE/GNOME",
        "package_mgr": "Zypper",
        "good_for_old_hw": False,
        "battery_friendly": 6,
        "summary": "Rolling-release with strong QA (openQA + snapper).",
    },
    "KDE neon": {
        "min_ram_gb": 4.0,
        "ideal_ram_gb": 8.0,
        "min_storage_gb": 20.0,
        "weight_low_hw": 2,
        "weight_mid_hw": 7,
        "weight_high_hw": 9,
        "beginner": 6,
        "stability": 7,
        "cutting_edge": 8,
        "office": 8,
        "development": 8,
        "gaming": 7,
        "creative": 8,
        "visual_polish": 10,
        "privacy": 6,
        "free_software_purity": 5,
        "lts": 6,
        "rolling": 4,
        "desktop": "KDE Plasma",
        "package_mgr": "APT",
        "good_for_old_hw": False,
        "battery_friendly": 6,
        "summary": "Latest KDE Plasma on a stable Ubuntu base.",
    },
    "Pop!_OS": {
        "min_ram_gb": 4.0,
        "ideal_ram_gb": 8.0,
        "min_storage_gb": 20.0,
        "weight_low_hw": 3,
        "weight_mid_hw": 8,
        "weight_high_hw": 9,
        "beginner": 8,
        "stability": 8,
        "cutting_edge": 7,
        "office": 8,
        "development": 9,
        "gaming": 9,
        "creative": 8,
        "visual_polish": 8,
        "privacy": 6,
        "free_software_purity": 5,
        "lts": 8,
        "rolling": 0,
        "desktop": "COSMIC/GNOME",
        "package_mgr": "APT/Flatpak",
        "good_for_old_hw": False,
        "battery_friendly": 6,
        "summary": "NVIDIA support out of the box; great for dev/gaming.",
    },
    "Nobara": {
        "min_ram_gb": 4.0,
        "ideal_ram_gb": 8.0,
        "min_storage_gb": 30.0,
        "weight_low_hw": 1,
        "weight_mid_hw": 7,
        "weight_high_hw": 10,
        "beginner": 7,
        "stability": 7,
        "cutting_edge": 9,
        "office": 7,
        "development": 7,
        "gaming": 10,
        "creative": 9,
        "visual_polish": 8,
        "privacy": 5,
        "free_software_purity": 4,
        "lts": 0,
        "rolling": 6,
        "desktop": "KDE/GNOME",
        "package_mgr": "DNF/Flatpak",
        "good_for_old_hw": False,
        "battery_friendly": 5,
        "summary": "Fedora-based, gaming/creator focused.",
    },
    "elementary OS": {
        "min_ram_gb": 4.0,
        "ideal_ram_gb": 4.0,
        "min_storage_gb": 25.0,
        "weight_low_hw": 3,
        "weight_mid_hw": 8,
        "weight_high_hw": 7,
        "beginner": 9,
        "stability": 8,
        "cutting_edge": 5,
        "office": 8,
        "development": 7,
        "gaming": 4,
        "creative": 7,
        "visual_polish": 10,
        "privacy": 8,
        "free_software_purity": 6,
        "lts": 8,
        "rolling": 0,
        "desktop": "Pantheon",
        "package_mgr": "APT/Flatpak",
        "good_for_old_hw": False,
        "battery_friendly": 7,
        "summary": "Beautifully designed, focused desktop.",
    },
    "Zorin OS Core": {
        "min_ram_gb": 2.0,
        "ideal_ram_gb": 4.0,
        "min_storage_gb": 15.0,
        "weight_low_hw": 6,
        "weight_mid_hw": 9,
        "weight_high_hw": 6,
        "beginner": 10,
        "stability": 9,
        "cutting_edge": 4,
        "office": 9,
        "development": 7,
        "gaming": 6,
        "creative": 7,
        "visual_polish": 9,
        "privacy": 6,
        "free_software_purity": 4,
        "lts": 9,
        "rolling": 0,
        "desktop": "GNOME (custom)",
        "package_mgr": "APT/Flatpak",
        "good_for_old_hw": False,
        "battery_friendly": 7,
        "summary": "Polished UI, friendly for Windows switchers.",
    },
    "Linux Lite": {
        "min_ram_gb": 1.0,
        "ideal_ram_gb": 2.0,
        "min_storage_gb": 10.0,
        "weight_low_hw": 9,
        "weight_mid_hw": 5,
        "weight_high_hw": 3,
        "beginner": 9,
        "stability": 8,
        "cutting_edge": 3,
        "office": 8,
        "development": 5,
        "gaming": 4,
        "creative": 4,
        "visual_polish": 6,
        "privacy": 5,
        "free_software_purity": 4,
        "lts": 8,
        "rolling": 0,
        "desktop": "XFCE",
        "package_mgr": "APT",
        "good_for_old_hw": True,
        "battery_friendly": 8,
        "summary": "Beginner-friendly, XFCE-based, lightweight.",
    },
    "Peppermint": {
        "min_ram_gb": 1.0,
        "ideal_ram_gb": 2.0,
        "min_storage_gb": 10.0,
        "weight_low_hw": 9,
        "weight_mid_hw": 5,
        "weight_high_hw": 3,
        "beginner": 7,
        "stability": 8,
        "cutting_edge": 4,
        "office": 7,
        "development": 6,
        "gaming": 4,
        "creative": 4,
        "visual_polish": 6,
        "privacy": 6,
        "free_software_purity": 5,
        "lts": 7,
        "rolling": 0,
        "desktop": "XFCE",
        "package_mgr": "APT",
        "good_for_old_hw": True,
        "battery_friendly": 8,
        "summary": "Minimal Debian-based; fast & flexible.",
    },
    "Void (LXQt)": {
        "min_ram_gb": 1.0,
        "ideal_ram_gb": 2.0,
        "min_storage_gb": 10.0,
        "weight_low_hw": 8,
        "weight_mid_hw": 7,
        "weight_high_hw": 6,
        "beginner": 3,
        "stability": 8,
        "cutting_edge": 8,
        "office": 5,
        "development": 8,
        "gaming": 5,
        "creative": 4,
        "visual_polish": 5,
        "privacy": 8,
        "free_software_purity": 8,
        "lts": 0,
        "rolling": 9,
        "desktop": "LXQt",
        "package_mgr": "XBPS",
        "good_for_old_hw": True,
        "battery_friendly": 8,
        "summary": "Minimal rolling distro; for advanced users.",
    },
    "antiX": {
        "min_ram_gb": 0.25,
        "ideal_ram_gb": 1.0,
        "min_storage_gb": 5.0,
        "weight_low_hw": 10,
        "weight_mid_hw": 4,
        "weight_high_hw": 2,
        "beginner": 5,
        "stability": 8,
        "cutting_edge": 3,
        "office": 6,
        "development": 4,
        "gaming": 2,
        "creative": 2,
        "visual_polish": 3,
        "privacy": 7,
        "free_software_purity": 7,
        "lts": 8,
        "rolling": 0,
        "desktop": "IceWM/Fluxbox",
        "package_mgr": "APT",
        "good_for_old_hw": True,
        "battery_friendly": 9,
        "summary": "Ultra-light, runs on truly ancient hardware.",
    },
}


# Hardware score (not being generous lol)
def compute_hardware_score(state) -> int:
    """
    Combine cpu/gpu/ram/storage into 0-100.
    """
    cpu_score = state.get("cpu_score") or 0  # already 0-100
    gpu_cat = (state.get("gpu_cat") or "").lower()
    gpu_score = {"strong": 90, "mid": 60, "weak": 30, "nogpu": 10, "unknown": 35}.get(
        gpu_cat, 35
    )
    ram_total = float(state.get("ram_total_gb") or 0)
    if ram_total >= 32:
        ram_score = 100
    elif ram_total >= 16:
        ram_score = 85
    elif ram_total >= 8:
        ram_score = 65
    elif ram_total >= 4:
        ram_score = 45
    elif ram_total >= 2:
        ram_score = 25
    else:
        ram_score = 10
    st_cat = (state.get("storage_cat") or "").lower()
    storage_score = {"high": 90, "fast": 75, "mid": 50, "low": 25, "unknown": 50}.get(
        st_cat, 50
    )

    # Weighted average
    total = int(
        round(
            cpu_score * 0.30
            + gpu_score * 0.20
            + ram_score * 0.30
            + storage_score * 0.20
        )
    )
    return max(0, min(100, total))


def hardware_tier(score: int) -> str:
    if score >= 85:
        return "ultra"
    if score >= 70:
        return "high"
    if score >= 55:
        return "mid_high"
    if score >= 40:
        return "mid"
    if score >= 25:
        return "mid_low"
    if score >= 12:
        return "low"
    return "very_low"


def _hw_weight_for(distro, score: int) -> int:
    if score >= 70:
        return distro["weight_high_hw"]
    if score >= 40:
        return distro["weight_mid_hw"]
    return distro["weight_low_hw"]


# Recommendation
def recommend(state, prefs, top_n=5):
    hw_score = compute_hardware_score(state)
    ram_gb = float(state.get("ram_total_gb") or 0)
    storage_free = float(state.get("storage_free_gb") or 0)

    results = []
    for name, d in DISTROS.items():
        score = 0.0
        reasons = []

        # Hardware match (weighted)
        hw_w = _hw_weight_for(d, hw_score)
        score += hw_w * 6.0
        if hw_w >= 8:
            reasons.append("Excellent fit for your hardware")
        elif hw_w >= 5:
            reasons.append("Good fit for your hardware")
        else:
            reasons.append(
                "May feel sluggish on this hardware" if hw_score < 40 else ""
            )

        # RAM check (penalty if below minimum)
        if ram_gb and ram_gb < d["min_ram_gb"]:
            score -= 30
            reasons.append(f"Below minimum RAM ({d['min_ram_gb']} GB)")
        elif ram_gb and ram_gb >= d["ideal_ram_gb"]:
            score += 8

        # Storage minimum
        if storage_free and storage_free < d["min_storage_gb"]:
            score -= 10

        # Usage
        usage = prefs.get("usage", "office").lower()
        usage_key = {
            "gaming": "gaming",
            "office": "office",
            "development": "development",
            "creative": "creative",
        }.get(usage, "office")
        score += d.get(usage_key, 0) * 3
        if d.get(usage_key, 0) >= 8:
            reasons.append(f"Strong for {usage_key}")

        # Gaming intensity
        gi = prefs.get("gaming_intensity", "none").lower()
        if gi == "serious":
            score += d["gaming"] * 2

        # Visual polish
        if prefs.get("visual") == "yes":
            score += d["visual_polish"] * 2
            if d["visual_polish"] >= 9:
                reasons.append("Polished, modern UI")

        # Experience
        exp = prefs.get("experience", "beginner").lower()
        if exp == "beginner":
            score += d["beginner"] * 2.5
            if d["beginner"] >= 9:
                reasons.append("Beginner-friendly")
        elif exp == "advanced":
            # Reward cutting-edge & free software for advanced users
            score += d["cutting_edge"] * 1.5

        # Update preference
        upd = prefs.get("update_pref", "balanced").lower()
        if upd == "stable":
            score += d["stability"] * 2 + d["lts"] * 1.5
        elif upd == "cutting_edge":
            score += d["cutting_edge"] * 2 + d["rolling"] * 1.5
            if d["rolling"] >= 8:
                reasons.append("Rolling release with latest software")
        else:
            score += d["stability"] * 1.0 + d["cutting_edge"] * 1.0

        # Privacy
        if prefs.get("privacy") == "yes":
            score += d["privacy"] * 2

        # Free software only
        if prefs.get("free_software_only") == "yes":
            score += d["free_software_purity"] * 3
            if d["free_software_purity"] < 5:
                score -= 15

        # Battery
        if prefs.get("battery_priority") == "yes":
            score += d["battery_friendly"] * 2
            if d["battery_friendly"] >= 8:
                reasons.append("Good battery efficiency")

        # Windows-like
        if prefs.get("windows_like") == "yes":
            if d["desktop"].lower().startswith(("cinnamon", "kde", "gnome (custom)")):
                score += 12
                reasons.append("Windows-like interface")
            elif d["desktop"].lower().startswith(("xfce",)):
                score += 6

        # Desktop preference
        dp = prefs.get("desktop_pref", "any").lower()
        if dp != "any":
            if dp in d["desktop"].lower():
                score += 15
                reasons.append(f"Uses preferred {dp.upper()} desktop")

        # Older hardware bonus
        if hw_score < 30 and d["good_for_old_hw"]:
            score += 12

        results.append(
            {
                "name": name,
                "score": round(score, 1),
                "summary": d["summary"],
                "desktop": d["desktop"],
                "package_mgr": d["package_mgr"],
                "reasons": [r for r in reasons if r],
                "min_ram_gb": d["min_ram_gb"],
                "ideal_ram_gb": d["ideal_ram_gb"],
            }
        )

    results.sort(key=lambda r: r["score"], reverse=True)
    return {
        "hardware_score": hw_score,
        "tier": hardware_tier(hw_score),
        "recommendations": results[:top_n],
    }


if __name__ == "__main__":
    import json

    state = {
        "cpu_score": 65,
        "gpu_cat": "mid",
        "ram_total_gb": 8,
        "storage_cat": "fast",
        "storage_free_gb": 100,
    }
    prefs = {
        "usage": "development",
        "visual": "yes",
        "experience": "intermediate",
        "update_pref": "balanced",
        "privacy": "no",
        "free_software_only": "no",
        "battery_priority": "no",
        "windows_like": "no",
        "gaming_intensity": "casual",
        "desktop_pref": "any",
    }
    print(json.dumps(recommend(state, prefs), indent=2))
