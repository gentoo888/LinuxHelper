import platform
import subprocess
import re

def probe_gpu():
    """
    GPU probing. If Windows, tries WMIC, falls back to PowerShell.
    If Linux/Mac, tries GPUtil; if not available, falls back to lspci.
    Categorizes GPU into 'nogpu', 'weak', 'mid', 'strong', or 'unknown'.
    """
    system = platform.system().lower()

    try:
        if system == "windows":
            # --- Windows: WMIC -> PowerShell fallback ---
            try:
                out = subprocess.check_output(
                    ["wmic", "path", "win32_VideoController", "get", "name"],
                    text=True
                )
            except FileNotFoundError:
                # If WMIC not available, use PowerShell
                out = subprocess.check_output(
                    [
                        "powershell",
                        "-NoProfile",
                        "-Command",
                        "Get-WmiObject Win32_VideoController | Select-Object -ExpandProperty Name"
                    ],
                    text=True
                )

            gpus = [line.strip() for line in out.splitlines() if line.strip() and "Name" not in line]
            gpu_name = ", ".join(gpus) if gpus else None


    except Exception as e:
        return {"ok": False, "name": None, "category": "nogpu", "error": str(e)}

    # If no GPU found
    if not gpu_name:
        return {"ok": True, "name": None, "category": "nogpu"}

    # Convert to lowercase for case-insensitive matching
    name_lower = gpu_name.lower()

    # WEAK GPUs (integrated, old, or entry-level)
    weak_keywords = [
        # This part surely can be improved over time by adding more models. If you are a developer and know more models, please contribute!

        # Intel Integrated
        "intel hd", "intel uhd", "intel iris", "intel graphics", "intel gma", 
        "intel x3100", "intel x4500", "intel 3000", "intel 4000", "intel 5000", 
        "intel 5100", "intel 5200", "intel 5300", "intel 5400", "intel 5500", 
        "intel 5600", "intel 5700", "intel 5800", "intel 6000", "intel 6100", 
        "intel 6200", "intel 6300", "intel 6400", "intel 6500", "intel 6600", 
        "intel 6700", "intel 6800", "intel 6900",
        
        # Intel Arc (entry-level)
        "intel arc a310", "intel arc a380", "intel arc a350m", "intel arc a370m",
        
        # AMD/ATI Integrated and Low-End
        "amd radeon graphics", "radeon (tm) graphics", "amd radeon (tm) graphics",
        "vega 3", "vega 5", "vega 6", "vega 7", "vega 8", "vega 9", "vega 11",
        "radeon r2", "radeon r3", "radeon r4", "radeon r5", "radeon r6", "radeon r7", "radeon r8",
        "radeon hd 5450", "radeon hd 6450", "radeon hd 7470", "radeon hd 8490", "radeon hd 8570",
        "radeon hd 2400", "radeon hd 2600", "radeon hd 3450", "radeon hd 3470", "radeon hd 3650",
        "radeon hd 3670", "radeon hd 3850", "radeon hd 3870", "radeon hd 4350", "radeon hd 4550",
        "radeon hd 4650", "radeon hd 4670", "radeon hd 4730", "radeon hd 4750", "radeon hd 4770",
        "radeon hd 4830", "radeon hd 4850", "radeon hd 4870", "radeon hd 4890", "radeon hd 5550",
        "radeon hd 5570", "radeon hd 5670", "radeon hd 5750", "radeon hd 5770", "radeon hd 5830",
        "radeon hd 5850", "radeon hd 5870", "radeon hd 5970",
        
        # AMD Ryzen APUs (sorry amd fanboys, but these are weak for gaming lol)
        "ryzen 2 graphics", "ryzen 3 graphics", "ryzen 5 graphics", "ryzen 7 graphics",
        "radeon graphics", "amd renoir", 
        
        # NVIDIA Low-End and Mobile
        "mx110", "mx130", "mx150", "mx230", "mx250", "mx330", "mx350", "mx450", "mx550", "mx570",
        "geforce 210", "geforce 310", "geforce 405", "geforce 410m", "geforce 510",
        "geforce gt 610", "geforce gt 620", "geforce gt 630", "geforce gt 640", "geforce gt 650m",
        "geforce gt 710", "geforce gt 720", "geforce gt 730", "geforce gt 740", "geforce gt 740m",
        "geforce 610m", "geforce 615", "geforce 620m", "geforce 705m", "geforce 710m", "geforce 720m",
        "geforce 730m", "geforce 735m", "geforce 740m", "geforce 745m", "geforce 820m", "geforce 825m", 
        "geforce 830m", "geforce 840m", "geforce 920m", "geforce 930m", "geforce 930mx", "geforce 940m", 
        "geforce 940mx", "geforce 945m", "geforce 950m", "geforce 9600m", "geforce 9650m", "geforce 9700m", 
        "geforce 9800m",
        
        # Apple Integrated
        "apple m1", "apple m2", "apple m3", "apple a12z", "apple a14", "apple a15", "apple a16", "apple a17", "apple a18",
        
        # Generic terms
        "integrated", "onboard", "shared graphics", "igp"
    ]

    # MID-RANGE GPUs
    mid_keywords = [
        # Intel Arc (mid-range)
        "intel arc a550m", "intel arc a730m", "intel arc a770m",
        
        # NVIDIA GTX Mid-Range
        "gtx 750", "gtx 760", "gtx 770", "gtx 780", "gtx 950", "gtx 960", "gtx 970", "gtx 980",
        "gtx 1050", "gtx 1050 ti", "gtx 1060", "gtx 1070", "gtx 1080",
        "gtx 1650", "gtx 1660", "gtx 1630", "gtx 1660 super", "gtx 1660 ti",
        "gtx 860m", "gtx 870m", "gtx 880m", "gtx 965m", "gtx 970m", "gtx 980m", 
        "gtx 1050m", "gtx 1060m", "gtx 1070m", "gtx 1080m",
        
        # RTX 20/30 Series (Lower End)
        "rtx 2050", "rtx 2060", "rtx 3050", "rtx 3050 ti", "rtx 3060",
        
        # AMD RX 400/500/5000/6000 (Mid-Range)
        "rx 460", "rx 470", "rx 480", "rx 550", "rx 560", "rx 570", "rx 580", "rx 590",
        "rx 5500", "rx 5600", "rx 6500", "rx 6600",
        "radeon hd 7850", "radeon hd 7870", "radeon hd 7950", "radeon hd 7970",
        "radeon r7 240", "radeon r7 250", "radeon r7 260", "radeon r7 260x", "radeon r7 265", 
        "radeon r7 360", "radeon r7 370", "radeon r9 270", "radeon r9 280", "radeon r9 285", 
        "radeon r9 380", "radeon r9 380x", "radeon r9 390", "radeon r9 390x", "radeon r9 290", 
        "radeon r9 290x", "radeon r9 295x2",
        
        # Apple Pro/Max
        "apple m1 pro", "apple m1 max", "apple m2 pro", "apple m2 max", "apple m3 pro", "apple m3 max",
        
        # Workstation (Mid-Range)
        "quadro k", "quadro m", "quadro p", "quadro t", "firepro", "radeon pro", "radeon pro wx"
    ]

    # HIGH-END GPUs
    strong_keywords = [
        # NVIDIA RTX (High-End)
        "rtx 2070", "rtx 2080", "rtx 2080 ti", "rtx 3070", "rtx 3080", "rtx 3090",
        "rtx 4060", "rtx 4070", "rtx 4080", "rtx 4090", "rtx 5000", "rtx 6000", "rtx 8000",
        
        # NVIDIA Data Center/Professional
        "titan", "tesla", "a100", "a30", "a40", "a6000", "h100", "h200", "l40", "l40s", "l4", "l20", "l2",
        
        # AMD High-End
        "rx 6700", "rx 6750", "rx 6800", "rx 6850", "rx 6900", "rx 6950",
        "rx 7600", "rx 7700", "rx 7800", "rx 7900", "rx 7900 xt", "rx 7900 xtx",
        "radeon vii", "radeon pro duo", "instinct", "radeon instinct", "radeon pro vii",
        
        # Apple Ultra
        "apple m1 ultra", "apple m2 ultra", "apple m3 ultra"
    ]

    # Add uppercase variants. We do this to avoid case sensitivity issues.
    weak_keywords = weak_keywords + [k.upper() for k in weak_keywords]
    mid_keywords = mid_keywords + [k.upper() for k in mid_keywords]
    strong_keywords = strong_keywords + [k.upper() for k in strong_keywords]

    # Name variants to check against
    name_variants = [gpu_name, name_lower]

    # Categorization logic
    if any(any(k in n for k in strong_keywords) for n in name_variants):
        cat = "strong"
    elif any(any(k in n for k in mid_keywords) for n in name_variants):
        cat = "mid"
    elif any(any(k in n for k in weak_keywords) for n in name_variants):
        cat = "weak"
    else:
        # Additional heuristics for unknown GPUs
        if any(re.search(r'rtx\s*[3-9]\d{3}', n) for n in name_variants):  # RTX 3000+ series pattern
            cat = "strong"
        elif any(re.search(r'gtx\s*\d{4}', n) for n in name_variants):  # GTX 1000+ series pattern
            cat = "mid"
        elif any(re.search(r'radeon\s*rx\s*\d{4}', n) for n in name_variants):  # RX series pattern
            cat = "mid"
        elif any('intel' in n and ('graphics' in n or 'gpu' in n) for n in name_variants):  # Intel integrated
            cat = "weak"
        else:
            cat = "unknown"

    return {"ok": True, "name": gpu_name, "category": cat}

if __name__ == "__main__":
    result = probe_gpu()
    print(f"GPU: {result['name']}")
    print(f"Category: {result['category']}")
