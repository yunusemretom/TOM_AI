"""Bilgisayar araçları: uygulama ve site açma, sistem durumu (Linux).

Güvenlik: kabuk komutu çalıştırılmaz. Uygulama yalnız kurulu .desktop kayıtlarından seçilir,
site yalnız http(s) adresi olarak varsayılan tarayıcıda açılır.
"""

from __future__ import annotations

import configparser
import glob
import os
import re
import shutil
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

DESKTOP_DIRS = ["/usr/share/applications", "/usr/local/share/applications", "~/.local/share/applications",
                "/var/lib/snapd/desktop/applications", "/var/lib/flatpak/exports/share/applications",
                "~/.local/share/flatpak/exports/share/applications"]


# Sık açılan siteler: "YouTube'u aç" uygulama değil site demek (yoksa .desktop anahtar kelimesinden
# ilgisiz bir uygulama açılabiliyor: Shotwell'in anahtar kelimelerinde "YouTube" var).
KNOWN_SITES = {
    "youtube": "https://www.youtube.com", "google": "https://www.google.com", "gmail": "https://mail.google.com",
    "google drive": "https://drive.google.com", "drive": "https://drive.google.com",
    "google takvim": "https://calendar.google.com", "takvim": "https://calendar.google.com",
    "haritalar": "https://maps.google.com", "google haritalar": "https://maps.google.com",
    "netflix": "https://www.netflix.com", "instagram": "https://www.instagram.com", "twitter": "https://x.com",
    "x": "https://x.com", "facebook": "https://www.facebook.com", "linkedin": "https://www.linkedin.com",
    "github": "https://github.com", "chatgpt": "https://chatgpt.com", "claude": "https://claude.ai",
    "whatsapp": "https://web.whatsapp.com", "whatsapp web": "https://web.whatsapp.com",
    "wikipedia": "https://tr.wikipedia.org", "vikipedi": "https://tr.wikipedia.org", "reddit": "https://www.reddit.com",
    "amazon": "https://www.amazon.com.tr", "trendyol": "https://www.trendyol.com", "hepsiburada": "https://www.hepsiburada.com",
    "spotify web": "https://open.spotify.com", "twitch": "https://www.twitch.tv", "e-devlet": "https://www.turkiye.gov.tr",
}
BROWSERS = {"chrome": ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"],
            "google chrome": ["google-chrome", "google-chrome-stable"], "chromium": ["chromium", "chromium-browser"],
            "firefox": ["firefox"], "brave": ["brave-browser", "brave"], "edge": ["microsoft-edge"]}


def _tr(s: str) -> str:
    return s.replace("I", "ı").replace("İ", "i").lower()


def installed_apps() -> list[tuple[str, str, str]]:
    """(görünen ad, .desktop yolu, aranacak metin) listesi."""
    out = []
    for d in DESKTOP_DIRS:
        for f in glob.glob(os.path.join(os.path.expanduser(d), "*.desktop")):
            cp = configparser.ConfigParser(interpolation=None, strict=False)
            try:
                cp.read(f, encoding="utf-8")
                e = cp["Desktop Entry"]
            except Exception:  # noqa: BLE001 — bozuk kayıtları atla
                continue
            if e.get("NoDisplay", "false").lower() == "true" or e.get("Type", "Application") != "Application":
                continue
            name = e.get("Name[tr]") or e.get("Name") or Path(f).stem
            hay = " ".join([name, e.get("Name", ""), e.get("GenericName[tr]", ""), e.get("GenericName", ""),
                            e.get("Keywords[tr]", ""), e.get("Keywords", ""), Path(f).stem])
            out.append((name, f, _tr(hay)))
    return out


def _clean_name(ad: str) -> str:
    """'YouTube'u' → 'youtube'; 'Chrome'dan' → 'chrome'."""
    k = _tr(ad).strip().strip("\"'")
    k = re.sub(r"['’](y?[ıiuü]|[yn]?[ae]|d[ae]n|t[ae]n|n[ıiuü]n)$", "", k)
    return k.strip()


def uygulama_ac(ad: str) -> str:
    key = _clean_name(ad)
    apps = installed_apps()
    exact = [a for a in apps if _tr(a[0]) == key]
    by_name = exact or [a for a in apps if key in _tr(a[0])]
    if not by_name and key in KNOWN_SITES:  # "YouTube'u aç": uygulama yoksa site
        return site_ac(KNOWN_SITES[key])
    cands = by_name or [a for a in apps if key in a[2].split()] or \
        [a for a in apps if all(w in a[2] for w in key.split())]
    if not cands:
        return f"'{ad}' adında kurulu bir uygulama bulamadım."
    name, path, _ = sorted(cands, key=lambda a: len(a[0]))[0]
    launcher = shutil.which("gio")
    cmd = [launcher, "launch", path] if launcher else ["gtk-launch", Path(path).stem]
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    return f"{name} açıldı."


def site_ac(adres: str, tarayici: str = "") -> str:
    a = adres.strip()
    known = KNOWN_SITES.get(_clean_name(a))
    if known:
        url = known
    elif re.match(r"^https?://", a):
        url = a
    elif re.match(r"^[\w.-]+\.[a-z]{2,}(/\S*)?$", a, re.I):
        url = "https://" + a
    else:  # adres değil: arama sayfası
        url = "https://duckduckgo.com/?q=" + urllib.parse.quote(a)
    exe = None
    if tarayici:
        for cand in BROWSERS.get(_clean_name(tarayici), [_clean_name(tarayici)]):
            exe = shutil.which(cand)
            if exe:
                break
        if not exe:
            return f"'{tarayici}' tarayıcısı bulunamadı."
    cmd = [exe, url] if exe else ["xdg-open", url]
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    return f"{'Tarayıcıda' if not exe else Path(exe).name + ' ile'} açıldı: {url}"


def youtube_ara(sorgu: str, oynat: bool = False, tarayici: str = "") -> str:
    """YouTube'da arar. oynat=True: ilk videoyu doğrudan açar (sayfadan videoId okunur, API anahtarı gerekmez)."""
    q = urllib.parse.quote_plus(sorgu.strip())
    results = f"https://www.youtube.com/results?search_query={q}"
    if not oynat:
        site_ac(results, tarayici)
        return f"YouTube'da arama açıldı: {sorgu}"
    try:
        req = urllib.request.Request(results, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)",
                                                       "Accept-Language": "tr,en;q=0.8"})
        html = urllib.request.urlopen(req, timeout=6).read(3_000_000).decode("utf-8", "replace")
        m = re.search(r'"videoRenderer":\{"videoId":"([\w-]{11})".*?"title":\{"runs":\[\{"text":"(.*?)"\}', html)
        if not m:
            raise ValueError("video bulunamadı")
        title = m.group(2).encode().decode("unicode_escape", "ignore") if "\\u" in m.group(2) else m.group(2)
        site_ac(f"https://www.youtube.com/watch?v={m.group(1)}", tarayici)
        return f"YouTube'da ilk video açıldı: {title}"
    except Exception:  # noqa: BLE001 — oynatılamazsa sonuç sayfası yeter
        site_ac(results, tarayici)
        return f"İlk videoyu bulamadım, YouTube'da arama sonuçlarını açtım: {sorgu}"


def ses_ayarla(yuzde: int) -> str:
    from tom.skills.builtin import MediaSkill

    m = MediaSkill()
    m._mute(False)
    return f"Ses yüzde {m._set_volume(min(int(yuzde), 150))} yapıldı."


def parlaklik_ayarla(yuzde: int) -> str:
    from tom.skills.builtin import BrightnessSkill

    return f"Parlaklık yüzde {BrightnessSkill()._set(int(yuzde))} yapıldı."


def bildir(baslik: str, metin: str = "") -> None:
    """Masaüstü bildirimi (notify-send varsa); yoksa sessizce geçer."""
    if shutil.which("notify-send"):
        subprocess.Popen(["notify-send", "-a", "TOM", "-i", "audio-input-microphone", "-t", "4000", baslik, metin],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def sistem_durumu() -> str:
    import psutil

    vm = psutil.virtual_memory()
    du = psutil.disk_usage(str(Path.home()))
    parts = [f"İşlemci %{psutil.cpu_percent(interval=0.3):.0f}",
             f"RAM {vm.used / 1e9:.1f}/{vm.total / 1e9:.1f} GB (%{vm.percent:.0f})",
             f"Ev diski boş {du.free / 1e9:.0f} GB"]
    b = psutil.sensors_battery()
    if b:
        parts.append(f"Pil %{b.percent:.0f}" + (" (şarjda)" if b.power_plugged else ""))
    try:
        temps = psutil.sensors_temperatures()
        cpu = temps.get("coretemp") or temps.get("k10temp")
        if cpu:
            parts.append(f"İşlemci sıcaklığı {max(t.current for t in cpu):.0f}°C")
    except Exception:  # noqa: BLE001
        pass
    if shutil.which("nvidia-smi"):
        try:
            g = subprocess.run(["nvidia-smi", "--query-gpu=temperature.gpu,memory.used,memory.total,utilization.gpu",
                                "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=3).stdout
            t, mu, mt, u = [x.strip() for x in g.split(",")]
            parts.append(f"GPU %{u}, {t}°C, bellek {mu}/{mt} MB")
        except Exception:  # noqa: BLE001
            pass
    return ", ".join(parts) + "."
