import hashlib
import os
import re
import threading
import tkinter as tk
import urllib.request
from tkinter import ttk

USER_AGENT = "SelfLinux-Recommender/1.0"


def compute_hash(file_path, algo="sha256", progress_cb=None, chunk_size=1024 * 1024):
    """
    Compute a hash of a file. progress_cb(processed_bytes, total_bytes) for UI.
    Returns hex digest (lowercase) or raises.
    """
    algo = algo.lower()
    if algo not in ("md5", "sha1", "sha256", "sha512"):
        raise ValueError(f"Unsupported algorithm: {algo}")
    h = hashlib.new(algo)
    total = os.path.getsize(file_path)
    processed = 0
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
            processed += len(chunk)
            if progress_cb:
                try:
                    progress_cb(processed, total)
                except Exception:
                    pass
    return h.hexdigest().lower()


def fetch_expected_hash(sha_url, filename, algo="sha256", timeout=20):
    """
    Download a checksums file (e.g. SHA256SUMS) and find the line for `filename`.
    Returns the expected hex digest (lowercase) or None.
    """
    if not sha_url:
        return None
    try:
        req = urllib.request.Request(sha_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read().decode("utf-8", errors="replace")
    except Exception:
        return None

    base = os.path.basename(filename).lower()
    # Lines look like: "<hex>  filename" or "<hex> *filename" or just "<hex>"
    for line in data.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^([0-9a-fA-F]{32,128})\s+\*?(\S+)\s*$", line)
        if m:
            digest, fname = m.group(1).lower(), m.group(2).lower()
            if os.path.basename(fname) == base or fname.endswith(base):
                return digest
        # Some files have only hash content (single line .sha256)
        m2 = re.match(r"^([0-9a-fA-F]{32,128})$", line)
        if m2 and len(data.splitlines()) <= 3:
            return m2.group(1).lower()
    return None


# ui
class ShaVerifyDialog(tk.Toplevel):
    """
    Modal dialog that computes a file's hash and compares against expected.
    If expected is None, only displays the computed hash to user.
    """

    def __init__(self, parent, file_path, algo="sha256", expected=None, distro_name=""):
        super().__init__(parent)
        self.title("ISO Integrity Verification")
        self.geometry("640x420")
        self.minsize(620, 400)
        self.configure(bg="#f5f6fa")

        self.file_path = file_path
        self.algo = algo
        self.expected = (expected or "").lower().strip() or None
        self.distro_name = distro_name
        self.result = None  # True/False/None

        self._build_ui()
        self.after(200, self._start)

    def _build_ui(self):
        pad = {"padx": 18, "pady": 6}

        title = tk.Label(
            self,
            text="🔒  ISO Integrity Check",
            font=("Segoe UI", 16, "bold"),
            bg="#f5f6fa",
            fg="#1f2d3d",
        )
        title.pack(anchor="w", padx=18, pady=(16, 0))

        sub = tk.Label(
            self,
            text=f"Verifying {self.distro_name or os.path.basename(self.file_path)}",
            font=("Segoe UI", 10),
            bg="#f5f6fa",
            fg="#5a6477",
        )
        sub.pack(anchor="w", **pad)

        info_frame = tk.Frame(
            self, bg="white", bd=0, highlightthickness=1, highlightbackground="#dde2eb"
        )
        info_frame.pack(fill="x", **pad)

        tk.Label(
            info_frame, text="File:", bg="white", font=("Segoe UI", 9, "bold")
        ).grid(row=0, column=0, sticky="w", padx=10, pady=(8, 2))
        tk.Label(
            info_frame,
            text=self.file_path,
            bg="white",
            font=("Segoe UI", 9),
            anchor="w",
            wraplength=560,
            justify="left",
        ).grid(row=0, column=1, sticky="w", padx=4, pady=(8, 2))
        tk.Label(
            info_frame, text="Algorithm:", bg="white", font=("Segoe UI", 9, "bold")
        ).grid(row=1, column=0, sticky="w", padx=10, pady=(2, 8))
        tk.Label(
            info_frame, text=self.algo.upper(), bg="white", font=("Segoe UI", 9)
        ).grid(row=1, column=1, sticky="w", padx=4, pady=(2, 8))

        self.status_var = tk.StringVar(value="Preparing…")
        tk.Label(
            self,
            textvariable=self.status_var,
            font=("Segoe UI", 10),
            bg="#f5f6fa",
            fg="#1f2d3d",
        ).pack(anchor="w", **pad)

        self.progress = ttk.Progressbar(
            self, orient="horizontal", mode="determinate", length=560
        )
        self.progress.pack(fill="x", **pad)

        self.result_frame = tk.Frame(self, bg="#f5f6fa")
        self.result_frame.pack(fill="both", expand=True, padx=18, pady=8)

        self.result_lbl = tk.Label(
            self.result_frame, text="", bg="#f5f6fa", font=("Segoe UI", 11, "bold")
        )
        self.result_lbl.pack(anchor="w")

        self.computed_lbl = tk.Label(
            self.result_frame,
            text="",
            bg="#f5f6fa",
            font=("Consolas", 9),
            wraplength=580,
            justify="left",
            fg="#1f2d3d",
        )
        self.computed_lbl.pack(anchor="w", pady=(8, 2))

        self.expected_lbl = tk.Label(
            self.result_frame,
            text="",
            bg="#f5f6fa",
            font=("Consolas", 9),
            wraplength=580,
            justify="left",
            fg="#5a6477",
        )
        self.expected_lbl.pack(anchor="w")

        btn_frame = tk.Frame(self, bg="#f5f6fa")
        btn_frame.pack(fill="x", padx=18, pady=(4, 14))
        self.close_btn = ttk.Button(btn_frame, text="Close", command=self.destroy)
        self.close_btn.pack(side="right")

    def _start(self):
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        try:
            self._set_status("Computing hash…")
            total = os.path.getsize(self.file_path)
            self.after(0, lambda: self.progress.configure(maximum=max(1, total)))

            def on_progress(processed, total_):
                pct = (processed / total_) * 100 if total_ else 0
                self.after(0, lambda: self._update_progress(processed, pct))

            digest = compute_hash(self.file_path, self.algo, progress_cb=on_progress)
            self.after(0, lambda: self._show_result(digest))
        except Exception as e:
            self.after(0, lambda: self._show_error(str(e)))

    def _update_progress(self, value, pct):
        self.progress["value"] = value
        self.status_var.set(f"Hashing… {pct:.1f}%")

    def _show_result(self, computed):
        self.progress["value"] = self.progress["maximum"]
        self.computed_lbl.config(text=f"Computed {self.algo.upper()}:\n{computed}")
        if self.expected:
            self.expected_lbl.config(text=f"Expected:\n{self.expected}")
            if computed == self.expected:
                self.result = True
                self.status_var.set("Verification successful")
                self.result_lbl.config(
                    text="✓  Hashes match — the ISO is authentic.", fg="#1b6e2c"
                )
            else:
                self.result = False
                self.status_var.set("Verification FAILED")
                self.result_lbl.config(
                    text="✗  Hashes DO NOT match — do not use this ISO!", fg="#b00020"
                )
        else:
            self.result = None
            self.status_var.set("Hash computed (no reference available)")
            self.result_lbl.config(
                text="ℹ  No official checksum available — compare manually.",
                fg="#7a5b00",
            )
            self.expected_lbl.config(
                text="Reference: not provided. Verify against the distribution's website."
            )

    def _show_error(self, msg):
        self.status_var.set("Error")
        self.result_lbl.config(text=f"✗  Could not compute hash: {msg}", fg="#b00020")

    def _set_status(self, txt):
        self.after(0, lambda: self.status_var.set(txt))


if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 2:
        print(compute_hash(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "sha256"))
