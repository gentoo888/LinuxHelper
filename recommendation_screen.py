# recommendation_screen.py
import tkinter as tk
import os
from PIL import Image, ImageTk

# --------- HW tier: comprehensive hardware categorization ----------
def _cpu_strong(cpu_cat: str | None) -> bool:
    return (cpu_cat or "") in ("Mid-range", "High-end", "Extreme")

def _gpu_strong(gpu_cat: str | None) -> bool:
    return (gpu_cat or "") == "strong"

def _ram_sufficient(ram_cat: str | None) -> bool:
    return (ram_cat or "") in ("good", "high")

def _storage_fast(storage_cat: str | None) -> bool:
    return (storage_cat or "") in ("high", "fast")

def _hardware_tier(cpu_cat: str | None, gpu_cat: str | None, ram_cat: str | None, storage_cat: str | None) -> str:
    """
    Enhanced hardware tier logic that considers CPU, GPU, RAM, and storage:
    
    Tiers:
    - "low": Low-end hardware (weak CPU, weak GPU, limited RAM, slow storage)
    - "mid": Mid-range hardware (mix of components, some strong, some weak)
    - "high": High-end hardware (strong CPU, strong GPU, ample RAM, fast storage)
    
    The tier is determined by the overall balance of components.
    """
    # Count how many components are strong/sufficient
    strong_components = 0
    
    if _cpu_strong(cpu_cat):
        strong_components += 1
    
    if _gpu_strong(gpu_cat):
        strong_components += 1
    
    if _ram_sufficient(ram_cat):
        strong_components += 1
    
    if _storage_fast(storage_cat):
        strong_components += 1
    
    # Determine tier based on number of strong components
    if strong_components <= 1:
        return "low"
    elif strong_components == 2:
        return "mid-low"
    elif strong_components == 3:
        return "mid-high"
    else:  # All 4 components are strong
        return "high"


# --------- Recommendation matrix based on hardware tier and preferences ----------
# value: (warnings[list[str]], recs[list[(name, desc)]])
MATRIX: dict[tuple[str, str, str], tuple[list[str], list[tuple[str, str]]]] = {
    # LOW TIER - development
    ("low", "development", "no"): (["Your hardware is limited. These lightweight distributions will work best."], [
        ("Debian XFCE", "Stable and lightweight; good for dev on low-end systems."),
        ("Xubuntu", "XFCE-based, lightweight; wide package ecosystem."),
        ("Void (LXQt)", "Minimal/rolling; light desktop footprint.")
    ]),
    ("low", "development", "yes"): (["Your hardware is limited. These distributions balance visuals and performance."], [
        ("Zorin OS Core", "Sleek but light; friendly for newcomers."),
        ("Linux Lite", "Lightweight and beginner-friendly."),
        ("Peppermint", "Minimal base for fast workflows.")
    ]),

    # LOW TIER - office
    ("low", "office", "no"): (["Your hardware is limited. These lightweight distributions will work best."], [
        ("Linux Mint XFCE", "Balanced and fast; ideal for office tasks."),
        ("Lubuntu", "Very light LXQt; runs smoothly on old hardware."),
        ("antiX", "Ultra-light; very quick boot.")
    ]),
    ("low", "office", "yes"): (["Your hardware is limited. These distributions balance visuals and performance."], [
        ("Zorin OS Core", "Visually pleasant yet light."),
        ("Xubuntu", "Lightweight with a modern look possible."),
        ("elementary OS", "Polished visuals; may feel heavy on very weak machines.")
    ]),

    # LOW TIER - gaming
    ("low", "gaming", "no"): (["Your hardware is very limited for gaming. Expect to run only older or lightweight games."], [
        ("Linux Mint XFCE", "Light desktop → leave resources for games."),
        ("Lubuntu", "Extra light; suitable for retro/indie titles.")
    ]),
    ("low", "gaming", "yes"): (["Your hardware is very limited for gaming. Expect to run only older or lightweight games."], [
        ("Zorin OS Core", "Clean look; keep expectations modest."),
        ("Peppermint", "Minimalist; leaves more resources for gaming."),
        ("Xubuntu", "Lightweight; good for older/indie games.")
    ]),

    # MID-LOW TIER - development
    ("mid-low", "development", "no"): ([], [
        ("Debian XFCE", "Stable and efficient; good for development."),
        ("Xubuntu", "Lightweight Ubuntu variant with good dev tools."),
        ("Fedora Workstation", "Up-to-date toolchains; good for development.")
    ]),
    ("mid-low", "development", "yes"): ([], [
        ("Zorin OS Core", "Polished UI with practical defaults."),
        ("Linux Mint Cinnamon", "User-friendly and stable."),
        ("elementary OS", "Clean design; good for focused work.")
    ]),

    # MID-LOW TIER - office
    ("mid-low", "office", "no"): ([], [
        ("Linux Mint XFCE", "Balanced for daily/office work."),
        ("Ubuntu LTS", "Simple, predictable, and long support."),
        ("Xubuntu", "Lightweight with good office application support.")
    ]),
    ("mid-low", "office", "yes"): ([], [
        ("Zorin OS Core", "Great for Windows switchers."),
        ("elementary OS", "Design-consistent, elegant UI."),
        ("Linux Mint Cinnamon", "User-friendly with Windows-like interface.")
    ]),

    # MID-LOW TIER - gaming
    ("mid-low", "gaming", "no"): (["Your hardware may struggle with newer games. Consider lighter titles."], [
        ("Pop!_OS", "Drivers/Steam made easy; target low/medium settings."),
        ("Linux Mint XFCE", "Light desktop; best when GPU is the limit."),
        ("Xubuntu", "Lightweight; good for older games.")
    ]),
    ("mid-low", "gaming", "yes"): (["Your hardware may struggle with newer games. Consider lighter titles."], [
        ("Zorin OS Core", "Stylish; keep graphics settings low/medium."),
        ("Pop!_OS", "Good driver support with a clean interface."),
        ("Linux Mint Cinnamon", "Balanced performance and visuals.")
    ]),

    # MID-HIGH TIER - development
    ("mid-high", "development", "no"): ([], [
        ("Fedora Workstation", "Up-to-date toolchains; strong container/Wayland support."),
        ("Ubuntu LTS", "Long-term support; high package availability."),
        ("Debian XFCE", "Rock-solid base; great for servers/CI.")
    ]),
    ("mid-high", "development", "yes"): ([], [
        ("KDE neon", "Latest Plasma; modern dev workstation."),
        ("Pop!_OS", "Dev-friendly; NVIDIA made easy; optional tiling."),
        ("Linux Mint Cinnamon", "User-friendly and stable.")
    ]),

    # MID-HIGH TIER - office
    ("mid-high", "office", "no"): ([], [
        ("Ubuntu LTS", "Wide ecosystem with long support."),
        ("Linux Mint Cinnamon", "Stable and practical."),
        ("Fedora Workstation", "Modern and stable; good for productivity.")
    ]),
    ("mid-high", "office", "yes"): ([], [
        ("KDE neon", "Modern and smooth desktop experience."),
        ("elementary OS", "Design-consistent, elegant UI."),
        ("Zorin OS Core", "Polished and smooth desktop.")
    ]),

    # MID-HIGH TIER - gaming
    ("mid-high", "gaming", "no"): ([], [
        ("Pop!_OS", "Steam/Proton easy; solid driver management."),
        ("Nobara", "Gaming-focused tweaks out of the box."),
        ("Ubuntu LTS", "Good compatibility with most games.")
    ]),
    ("mid-high", "gaming", "yes"): ([], [
        ("Nobara", "OBS/Proton GE/codec patches ready."),
        ("Pop!_OS", "Clean interface with good driver support."),
        ("KDE neon", "Modern Plasma with a polished look.")
    ]),

    # HIGH TIER - development
    ("high", "development", "no"): ([], [
        ("Fedora Workstation", "Cutting-edge dev experience."),
        ("Arch Linux", "AUR + minimal → full control."),
        ("openSUSE Tumbleweed", "Rolling with strong QA; zypper/YaST tooling.")
    ]),
    ("high", "development", "yes"): ([], [
        ("KDE neon", "Latest KDE; modern developer desk."),
        ("Pop!_OS", "Dev-friendly; NVIDIA made easy; optional tiling."),
        ("Fedora Workstation", "Polished GNOME experience; latest tools.")
    ]),

    # HIGH TIER - office
    ("high", "office", "no"): ([], [
        ("Ubuntu LTS", "Wide ecosystem with long support."),
        ("Linux Mint Cinnamon", "Stable and practical."),
        ("Fedora Workstation", "Modern and stable; good for productivity.")
    ]),
    ("high", "office", "yes"): ([], [
        ("KDE neon", "Visual quality + productivity."),
        ("Zorin OS Core", "Polished and smooth desktop."),
        ("elementary OS", "Design-consistent, elegant UI.")
    ]),

    # HIGH TIER - gaming
    ("high", "gaming", "no"): ([], [
        ("Pop!_OS", "Steam/Proton easy; solid driver management."),
        ("Nobara", "Gaming-focused tweaks out of the box."),
        ("Arch Linux", "Bleeding-edge; Proton-GE easy to install.(And if you wanna say 'I use arch btw') ;-)")
    ]),
    ("high", "gaming", "yes"): ([], [
        ("Nobara", "OBS/Proton GE/codec patches ready."),
        ("KDE neon", "Modern Plasma with a polished look.")
    ]),
}


class RecommendationScreen(tk.Frame):
    """
    Dynamic distro recommendation screen with comprehensive hardware assessment:
    - Hardware tier based on CPU, GPU, RAM, and storage
    - Usage: development / office / gaming
    - Visual preference: yes / no
    - Shows warnings if hardware limitations exist
    - Card: Name + Logo + description + Install button
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Store image references to prevent garbage collection
        self.images = {}
        
        # Create the UI elements
        self._create_ui()
        
    def _create_ui(self):
        """Create the user interface elements."""
        # Header section
        header_frame = tk.Frame(self, pady=10)
        header_frame.pack(fill="x")
        
        tk.Label(
            header_frame, 
            text="Recommended Distros", 
            font=("Arial", 24, "bold")
        ).pack()
        
        tk.Label(
            header_frame,
            text="SelfLinux recommends these distributions based on your hardware and preferences.\nTo install one, click the 'Install' button in its box.",
            font=("Arial", 12),
            justify="center",
            wraplength=760
        ).pack(pady=(5, 0))
        
        # Hardware assessment section
        hw_frame = tk.LabelFrame(self, text="Hardware Assessment", font=("Arial", 12, "bold"), padx=15, pady=10)
        hw_frame.pack(fill="x", padx=20, pady=10)
        
        self.hw_summary = tk.Label(
            hw_frame, 
            text="", 
            font=("Arial", 11),
            justify="left"
        )
        self.hw_summary.pack(anchor="w")
        
        # Preference summary
        pref_frame = tk.Frame(self, bg="#e3f2fd", padx=15, pady=10)  # Light blue background
        pref_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        self.pref_summary = tk.Label(
            pref_frame, 
            text="", 
            font=("Arial", 11),
            bg="#e3f2fd",
            justify="left"
        )
        self.pref_summary.pack(anchor="w")
        
        # Warning banner (initially hidden)
        self.warn_frame = tk.Frame(self, bg="#ffebee", padx=15, pady=10)  # Light red background
        
        self.warn = tk.Label(
            self.warn_frame, 
            text="", 
            fg="#b00020",  # Dark red text
            font=("Arial", 11, "bold"),
            bg="#ffebee",
            justify="left", 
            wraplength=760
        )
        self.warn.pack(anchor="w")
        
        # Card container
        self.cards_container = tk.Frame(self)
        self.cards_container.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Navigation buttons
        nav_frame = tk.Frame(self)
        nav_frame.pack(fill="x", padx=20, pady=(0, 15))
        
    
    def _mk_card(self, parent, name: str, desc: str, col: int):
        """Create a card for a distribution recommendation."""
        # Card frame with shadow effect (looks cool right?)
        outer_frame = tk.Frame(parent, bd=0, highlightthickness=1, highlightbackground="#ddd")
        outer_frame.grid(row=0, column=col, padx=10, sticky="n")
        
        # Inner card with padding
        card = tk.Frame(outer_frame, bd=0, padx=15, pady=15, bg="white")
        card.pack(fill="both", expand=True)
        
        # Logo
        logo_path = self._get_logo_path(name)
        if logo_path:
            logo_img = self._load_image(logo_path, (96, 96))
            if logo_img:
                logo_label = tk.Label(card, image=logo_img, bg="white")
                logo_label.pack(pady=(0, 10))
        
        # Distribution name
        name_label = tk.Label(
            card, 
            text=name, 
            font=("Arial", 14, "bold"),
            bg="white"
        )
        name_label.pack()
        
        #  Desc = Description 
        desc_label = tk.Label(
            card, 
            text=desc, 
            font=("Arial", 11),
            wraplength=200, 
            justify="center",
            bg="white"
        )
        desc_label.pack(pady=(5, 15), fill="x")
        
        # Install button
        install_btn = tk.Button(
            card,
            text="Install",
            font=("Arial", 12, "bold"),
            bg="#FFD700",  # Golden yellow (because tux's beak is yellow XD)
            fg="white",
            padx=15,
            pady=5,
            command=lambda n=name: self._on_install(n)
        )
        install_btn.pack()
    
    def _get_logo_path(self, distro_name: str) -> str:
        """Get the path to the logo for a given distro."""
        # Map distro names to logo filenames
        logo_map = {
            "Debian XFCE": "debian.png",
            "Xubuntu": "xubuntu.png",
            "Void (LXQt)": "void.png",
            "Zorin OS Core": "zorin.png",
            "Linux Lite": "linux_lite.png",
            "Peppermint": "peppermint.png",
            "Linux Mint XFCE": "mint.png",
            "Linux Mint Cinnamon": "mint.png",
            "Lubuntu": "lubuntu.png",
            "antiX": "antix.png",
            "elementary OS": "elementary.png",
            "Fedora Workstation": "fedora.png",
            "Ubuntu LTS": "ubuntu.png",
            "KDE neon": "neon.png",
            "Pop!_OS": "pop_os.png",
            "Nobara": "nobara.png",
            "openSUSE Tumbleweed": "opensuse.png",
            "Arch Linux": "arch.png",
            "Garuda KDE": "garuda.png",
        }
        
        # Get the logo filename for this distro
        logo_file = logo_map.get(distro_name)
        if not logo_file:
            return None
        
        # Construct the full path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(script_dir, "assets", "logos", logo_file)
        
        # Check if file exists
        if os.path.exists(logo_path):
            return logo_path
        return None
    
    def _load_image(self, path, size=None):
        """Load an image and optionally resize it."""
        try:
            img = Image.open(path)
            
            # Resize if size is specified
            if size:
                img = img.resize(size, Image.LANCZOS)
                
            photo = ImageTk.PhotoImage(img)
            
            # Store reference to prevent garbage collection
            self.images[path] = photo
            return photo
        except Exception as e:
            print(f"Error loading image {path}: {e}")
            return None
    
    def _on_install(self, name: str):
        """Handle the Install button click."""
        self.controller.write_distro_to_usb(name)
    
    def _get_hardware_description(self, tier: str) -> str:
        """Get a description of the hardware tier."""
        descriptions = {
            "low": "Your hardware is limited. Lightweight distributions will work best.",
            "mid-low": "Your hardware is adequate for most tasks, but may struggle with demanding applications.",
            "mid-high": "Your hardware is good for most uses including moderate gaming and development.",
            "high": "Your hardware is excellent and can handle any Linux distribution with ease."
        }
        return descriptions.get(tier, "Hardware assessment unavailable.")
    
    def _render(self):
        """Render the recommendations based on hardware and preferences."""
        s = self.controller.state
        
        # Get hardware information
        cpu_cat = s.get("cpu_cat") or "unknown"
        gpu_cat = s.get("gpu_cat") or "unknown"
        ram_cat = s.get("ram_cat") or "unknown"
        storage_cat = s.get("storage_cat") or "unknown"
        
        # Get detailed hardware info for display
        ram_total = s.get("ram_total_gb")
        ram_avail = s.get("ram_avail_gb")
        ram_used = s.get("ram_used_percent")
        gpu_name = s.get("gpu_name") or "Unknown"
        
        # Format RAM information
        if None not in (ram_total, ram_avail, ram_used):
            ram_info = f"{ram_cat} ({ram_avail} GB free / {ram_total} GB total, {ram_used}% used)"
        else:
            ram_info = ram_cat
        
        # Get user preferences 
        visual = (s.get("visual") or "no")  # 'yes' / 'no'
        usage = (s.get("usage") or "office")  # 'gaming' / 'office' / 'development'
        
        # Determine hardware tier based on all components
        hw_tier = _hardware_tier(cpu_cat, gpu_cat, ram_cat, storage_cat)
        
        # Update hardware summary
        self.hw_summary.config(
            text=(f"CPU: {cpu_cat} | GPU: {gpu_cat} ({gpu_name})\n"
                  f"RAM: {ram_info} | Storage: {storage_cat}\n"
                  f"Overall Hardware Assessment: {hw_tier.upper()}")
        )
        
        # Update preference summary
        usage_display = {
            "gaming": "Gaming", 
            "office": "Office & Productivity", 
            "development": "Software Development"
        }.get(usage, usage)
        
        visual_display = "Yes - Visual design is important" if visual == "yes" else "No - Performance over appearance"
        
        self.pref_summary.config(
            text=f"Usage Preference: {usage_display} | Visual Preference: {visual_display}"
        )
        
        # Get recommendations based on hardware tier and preferences
        key = (hw_tier, usage, visual)
        warnings, recs = MATRIX.get(key, ([], [
            ("Ubuntu LTS", "Safe default: broad support and ecosystem."),
            ("Linux Mint XFCE", "Light and balanced; fits most scenarios."),
            ("Xubuntu", "Light XFCE; good performance on low-end.")
        ]))
        
        # Show or hide warning banner
        if warnings:
            self.warn.config(text="⚠️ " + " ".join(warnings))
            self.warn_frame.pack(fill="x", padx=20, pady=(0, 10))
        else:
            self.warn_frame.pack_forget()
        
        # Clear existing cards
        for widget in self.cards_container.winfo_children():
            widget.destroy()
        
        # Create card row
        row = tk.Frame(self.cards_container)
        row.pack(fill="x", expand=True)
        
        # Create cards for recommendations (up to 5. More can be added if needed but we don't want to overwhelm the user XD)
        for i, (name, desc) in enumerate(recs[:5]):
            self._mk_card(row, name, desc, i)
    
    def tkraise(self):
        """Called when this screen is shown."""
        super().tkraise()
        self._render()
