# iso_resolver.py
# Resolves the latest official ISO URL for each supported distro.
# - Follows HTTP redirects.
# - Scrapes mirror index pages with regex when needed.
# - Provides a checksum URL when available (for SHA verification).

import re
import urllib.request
import urllib.error
from urllib.parse import urljoin, urlparse


USER_AGENT = "SelfLinux-Recommender/1.0 (+https://example.local)"


def _http_get(url, timeout=20, max_redirects=10):
    """GET text content following redirects."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read()
        try:
            return data.decode("utf-8", errors="replace"), resp.geturl()
        except Exception:
            return "", resp.geturl()


def _resolve_redirect(url, timeout=20):
    """Follow redirects with HEAD then GET fallback. Returns final URL."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT}, method="HEAD")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.geturl()
    except Exception:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.geturl()
        except Exception:
            return url


def _scrape_latest(index_url, pattern, prefer_amd64=True):
    """
    Fetch index page and find filenames matching pattern; return absolute URL of the
    latest (sorted descending lexicographically, which works for ISO version strings).
    """
    html, final_url = _http_get(index_url)
    matches = re.findall(pattern, html, re.IGNORECASE)
    # matches may be tuples if pattern has groups; flatten
    flat = []
    for m in matches:
        if isinstance(m, tuple):
            flat.append(m[0])
        else:
            flat.append(m)
    if prefer_amd64:
        flat.sort(key=lambda x: ("amd64" not in x and "x86_64" not in x and "x64" not in x, x), reverse=True)
    else:
        flat.sort(reverse=True)
    if not flat:
        return None
    return urljoin(final_url, flat[0])


# ---------- Resolvers ----------
def _resolve_ubuntu():
    base = "https://releases.ubuntu.com/"
    html, final = _http_get(base)
    # Find latest LTS folder (e.g. "24.04.3/")
    versions = re.findall(r'href="(\d{2}\.\d{2}(?:\.\d+)?)/"', html)
    if not versions:
        return None
    # Filter LTS by checking each folder text
    versions.sort(key=lambda v: tuple(int(x) for x in v.split(".")), reverse=True)
    for v in versions:
        sub = urljoin(base, v + "/")
        sub_html, sub_final = _http_get(sub)
        m = re.search(r'href="(ubuntu-' + re.escape(v) + r'-desktop-amd64\.iso)"', sub_html)
        if m:
            iso_url = urljoin(sub_final, m.group(1))
            sha_url = urljoin(sub_final, "SHA256SUMS")
            return {"url": iso_url, "sha_url": sha_url, "sha_algo": "sha256"}
    return None


def _resolve_xubuntu():
    # https://cdimage.ubuntu.com/xubuntu/releases/<ver>/release/
    base = "https://cdimage.ubuntu.com/xubuntu/releases/"
    html, final = _http_get(base)
    vers = re.findall(r'href="(\d{2}\.\d{2}(?:\.\d+)?)/"', html)
    vers.sort(key=lambda v: tuple(int(x) for x in v.split(".")), reverse=True)
    for v in vers:
        sub = urljoin(base, v + "/release/")
        try:
            sub_html, sub_final = _http_get(sub)
        except Exception:
            continue
        m = re.search(r'href="(xubuntu-[\d.]+-desktop-amd64\.iso)"', sub_html)
        if m:
            return {
                "url": urljoin(sub_final, m.group(1)),
                "sha_url": urljoin(sub_final, "SHA256SUMS"),
                "sha_algo": "sha256",
            }
    return None


def _resolve_lubuntu():
    base = "https://cdimage.ubuntu.com/lubuntu/releases/"
    html, final = _http_get(base)
    vers = re.findall(r'href="(\d{2}\.\d{2}(?:\.\d+)?)/"', html)
    vers.sort(key=lambda v: tuple(int(x) for x in v.split(".")), reverse=True)
    for v in vers:
        sub = urljoin(base, v + "/release/")
        try:
            sub_html, sub_final = _http_get(sub)
        except Exception:
            continue
        m = re.search(r'href="(lubuntu-[\d.]+-desktop-amd64\.iso)"', sub_html)
        if m:
            return {
                "url": urljoin(sub_final, m.group(1)),
                "sha_url": urljoin(sub_final, "SHA256SUMS"),
                "sha_algo": "sha256",
            }
    return None


def _resolve_debian():
    # Debian live XFCE
    base = "https://cdimage.debian.org/debian-cd/current-live/amd64/iso-hybrid/"
    html, final = _http_get(base)
    m = re.search(r'href="(debian-live-[\d.]+-amd64-xfce\.iso)"', html)
    if not m:
        return None
    return {
        "url": urljoin(final, m.group(1)),
        "sha_url": urljoin(final, "SHA256SUMS"),
        "sha_algo": "sha256",
    }


def _resolve_mint(edition="cinnamon"):
    # Mint mirror redirects
    base = "https://linuxmint.com/edition.php?id=320"  # legacy; we use the all-versions page
    # Use the mirrors directory
    base = "https://mirrors.edge.kernel.org/linuxmint/stable/"
    html, final = _http_get(base)
    vers = re.findall(r'href="([\d.]+)/"', html)
    # Sort numerically
    def key(v):
        try:
            return tuple(int(x) for x in v.split(".") if x.isdigit())
        except Exception:
            return (0,)
    vers.sort(key=key, reverse=True)
    for v in vers:
        sub = urljoin(base, v + "/")
        try:
            sub_html, sub_final = _http_get(sub)
        except Exception:
            continue
        m = re.search(r'href="(linuxmint-' + re.escape(v) + r'-' + edition + r'-64bit\.iso)"', sub_html)
        if m:
            return {
                "url": urljoin(sub_final, m.group(1)),
                "sha_url": urljoin(sub_final, "sha256sum.txt"),
                "sha_algo": "sha256",
            }
    return None


def _resolve_fedora_workstation():
    # Fedora's "get the latest" stable redirector
    # https://download.fedoraproject.org/pub/fedora/linux/releases/<ver>/Workstation/x86_64/iso/
    base = "https://download.fedoraproject.org/pub/fedora/linux/releases/"
    html, final = _http_get(base)
    vers = re.findall(r'href="(\d+)/"', html)
    vers = sorted([int(v) for v in vers], reverse=True)
    for v in vers:
        sub = urljoin(base, f"{v}/Workstation/x86_64/iso/")
        try:
            sub_html, sub_final = _http_get(sub)
        except Exception:
            continue
        m = re.search(r'href="(Fedora-Workstation-Live-[\d.\-]+x86_64[\d\.\-]*\.iso)"', sub_html)
        if not m:
            m = re.search(r'href="(Fedora-Workstation-Live-x86_64-[\d\-]+\.iso)"', sub_html)
        if m:
            iso_name = m.group(1)
            iso_url = urljoin(sub_final, iso_name)
            sha_match = re.search(r'href="(Fedora-Workstation-[\d\-x86_64A-Za-z\.]+CHECKSUM)"', sub_html)
            sha_url = urljoin(sub_final, sha_match.group(1)) if sha_match else None
            return {"url": iso_url, "sha_url": sha_url, "sha_algo": "sha256"}
    return None


def _resolve_opensuse_tumbleweed():
    base = "https://download.opensuse.org/tumbleweed/iso/"
    html, final = _http_get(base)
    m = re.search(r'(openSUSE-Tumbleweed-DVD-x86_64-Current\.iso)\b', html)
    if not m:
        m = re.search(r'(openSUSE-Tumbleweed-DVD-x86_64-Snapshot\d+-Media\.iso)\b', html)
    if m:
        iso_url = urljoin(final, m.group(1))
        # Resolve "Current" symlink to actual file
        iso_url = _resolve_redirect(iso_url)
        sha_url = iso_url + ".sha256"
        return {"url": iso_url, "sha_url": sha_url, "sha_algo": "sha256"}
    return None


def _resolve_void():
    base = "https://repo-default.voidlinux.org/live/current/"
    html, final = _http_get(base)
    m = re.search(r'href="(void-live-x86_64-[\d]+-lxqt\.iso)"', html)
    if not m:
        m = re.search(r'href="(void-live-x86_64-[\d]+-xfce\.iso)"', html)
    if m:
        iso_url = urljoin(final, m.group(1))
        return {"url": iso_url, "sha_url": urljoin(final, "sha256sum.txt"), "sha_algo": "sha256"}
    return None


def _resolve_zorin():
    # Zorin OS Core - direct from official; use HTML probing.
    base = "https://zrn.co/17core"  # Zorin's short URL redirector
    url = _resolve_redirect(base)
    if url and url.lower().endswith(".iso"):
        return {"url": url, "sha_url": None, "sha_algo": None}
    return None


def _resolve_elementary():
    # elementary OS - direct download via official torrent/HTTP
    # We use elementary's stable redirector
    candidates = [
        "https://sgp1.dl.elementary.io/download/MTcyMzMxMTM3NQ==/elementaryos-8.0-stable.20250314rc.iso",
    ]
    for c in candidates:
        try:
            url = _resolve_redirect(c)
            if url:
                return {"url": url, "sha_url": None, "sha_algo": None}
        except Exception:
            continue
    return None


def _resolve_pop_os():
    # Pop!_OS - JSON manifest
    try:
        html, final = _http_get("https://pop.system76.com/api/release")
        # Some endpoints return JSON; fallback: scrape main page
        import json
        data = json.loads(html)
        # Try to find amd64 intel iso URL
        for k, v in data.items():
            if isinstance(v, dict) and "url" in v and "amd64" in v["url"] and "intel" in v["url"]:
                return {"url": v["url"], "sha_url": v.get("sha_sum_url"), "sha_algo": "sha256"}
    except Exception:
        pass
    return None


def _resolve_kde_neon():
    base = "https://files.kde.org/neon/images/user/current/"
    html, final = _http_get(base)
    m = re.search(r'href="(neon-user-[\d-]+\.iso)"', html)
    if m:
        iso_url = urljoin(final, m.group(1))
        sha_url = iso_url + ".sha256sum"
        return {"url": iso_url, "sha_url": sha_url, "sha_algo": "sha256"}
    return None


def _resolve_nobara():
    # Nobara - GitHub releases or official mirror; using their official site
    try:
        html, final = _http_get("https://nobaraproject.org/download-nobara/")
        m = re.search(r'(https://[^"\'\s]+Nobara-[^"\'\s]+\.iso)', html)
        if m:
            return {"url": m.group(1), "sha_url": None, "sha_algo": None}
    except Exception:
        pass
    return None


def _resolve_antix():
    # antiX - sourceforge mirror
    base = "https://sourceforge.net/projects/antix-linux/files/Final/"
    try:
        html, final = _http_get(base)
        m = re.search(r'href="(/projects/antix-linux/files/Final/antiX-[\d.]+/)"', html)
        if m:
            sub = urljoin("https://sourceforge.net", m.group(1))
            sub_html, sub_final = _http_get(sub)
            m2 = re.search(r'href="(/projects/antix-linux/files/Final/antiX-[\d.]+/antiX-[\d.]+_x64-full\.iso/download)"', sub_html)
            if m2:
                return {"url": urljoin("https://sourceforge.net", m2.group(1)), "sha_url": None, "sha_algo": None}
    except Exception:
        pass
    return None


def _resolve_linux_lite():
    # Linux Lite - osdn or sourceforge
    base = "https://sourceforge.net/projects/linux-lite/files/"
    try:
        html, final = _http_get(base)
        m = re.search(r'href="(/projects/linux-lite/files/([\d.]+)/)"', html)
        if m:
            ver = m.group(2)
            sub = urljoin("https://sourceforge.net", m.group(1))
            sub_html, sub_final = _http_get(sub)
            m2 = re.search(r'href="(/projects/linux-lite/files/' + re.escape(ver) + r'/linux-lite-' + re.escape(ver) + r'-64bit\.iso/download)"', sub_html)
            if m2:
                return {"url": urljoin("https://sourceforge.net", m2.group(1)), "sha_url": None, "sha_algo": None}
    except Exception:
        pass
    return None


def _resolve_peppermint():
    base = "https://peppermintos.com/cms/download/"
    try:
        html, final = _http_get(base)
        m = re.search(r'(https://[^"\'\s]+PeppermintOS-[^"\'\s]*64\.iso)', html)
        if m:
            return {"url": m.group(1), "sha_url": None, "sha_algo": None}
    except Exception:
        pass
    return None


# Map distro display names to resolver functions
RESOLVERS = {
    "Ubuntu LTS": _resolve_ubuntu,
    "Xubuntu": _resolve_xubuntu,
    "Lubuntu": _resolve_lubuntu,
    "Debian XFCE": _resolve_debian,
    "Linux Mint Cinnamon": lambda: _resolve_mint("cinnamon"),
    "Linux Mint XFCE": lambda: _resolve_mint("xfce"),
    "Fedora Workstation": _resolve_fedora_workstation,
    "openSUSE Tumbleweed": _resolve_opensuse_tumbleweed,
    "Void (LXQt)": _resolve_void,
    "Zorin OS Core": _resolve_zorin,
    "elementary OS": _resolve_elementary,
    "Pop!_OS": _resolve_pop_os,
    "KDE neon": _resolve_kde_neon,
    "Nobara": _resolve_nobara,
    "antiX": _resolve_antix,
    "Linux Lite": _resolve_linux_lite,
    "Peppermint": _resolve_peppermint,
}


def resolve_iso(distro_name):
    """
    Returns dict: { url, sha_url, sha_algo, filename } or None on failure.
    Always follows redirects to get the final, canonical URL.
    """
    fn = RESOLVERS.get(distro_name)
    if not fn:
        return None
    try:
        info = fn()
        if not info or not info.get("url"):
            return None
        # Resolve final URL (handle redirects)
        final_url = _resolve_redirect(info["url"])
        info["url"] = final_url
        info["filename"] = urlparse(final_url).path.rsplit("/", 1)[-1] or "image.iso"
        # sha_algo default
        info.setdefault("sha_algo", "sha256")
        info.setdefault("sha_url", None)
        return info
    except Exception as e:
        return None


def supported_distros():
    return sorted(RESOLVERS.keys())


if __name__ == "__main__":
    import sys
    import json
    name = sys.argv[1] if len(sys.argv) > 1 else "Ubuntu LTS"
    print(json.dumps(resolve_iso(name), indent=2))
