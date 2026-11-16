"""Hazır hızlı komutlar: saat/tarih, hava durumu, müzik, ses seviyesi, zamanlayıcı, cihazlar.

Dış bağımlılıklar (saat, HTTP, kabuk komutu) parametreyle verilir; testlerde sahteleri kullanılır.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import subprocess
import threading
import time
import urllib.parse
import urllib.request
from typing import Callable

from tom.brain.persona import AYLAR, GUNLER
from tom.skills.base import Skill, SkillResult, rule
from tom.skills.text import parse_duration, sayi_yaz, sure_yaz


def _http_json(url: str, timeout: float = 4.0) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.load(r)


def _run(cmd: list[str], timeout: float = 3.0) -> str:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=True).stdout


# ----------------------------------------------------------------------------
class ClockSkill(Skill):
    name = "saat"
    description = "saati ve tarihi söylemek"
    rules = [
        rule(r"\bsaat\b.*\b(kaç|ne|nedir)\b|\bsaati söyle|\bsaat kaç\b", "time"),
        rule(r"\b(bugün|tarih\w*)\b.*\b(ne|nedir|kaç|ayın kaçı|günlerden)\b|\bayın kaçı\b|"
             r"\bgünlerden ne\b|\bhangi gün(deyiz)?\b|\bbugün ne günü\b", "date"),
    ]

    def __init__(self, now: Callable[[], dt.datetime] = dt.datetime.now):
        self.now = now

    def run(self, action, m, clause):
        n = self.now()
        if action == "time":
            if n.minute == 0:
                return SkillResult(f"Saat tam {sayi_yaz(n.hour)}.")
            return SkillResult(f"Saat {sayi_yaz(n.hour)}, {sayi_yaz(n.minute)}.")
        return SkillResult(f"Bugün {sayi_yaz(n.day)} {AYLAR[n.month - 1]}, {GUNLER[n.weekday()]}.")


# ----------------------------------------------------------------------------
WMO_TR = {
    0: "açık", 1: "çoğunlukla açık", 2: "parçalı bulutlu", 3: "kapalı", 45: "sisli", 48: "kırağılı sisli",
    51: "hafif çiseleyen", 53: "çiseleyen", 55: "yoğun çiseleyen", 56: "dondurucu çiseleyen",
    57: "dondurucu çiseleyen", 61: "hafif yağmurlu", 63: "yağmurlu", 65: "şiddetli yağmurlu",
    66: "dondurucu yağmurlu", 67: "dondurucu yağmurlu", 71: "hafif karlı", 73: "karlı",
    75: "yoğun karlı", 77: "kar taneli", 80: "hafif sağanak yağışlı", 81: "sağanak yağışlı",
    82: "şiddetli sağanak yağışlı", 85: "kar sağanaklı", 86: "yoğun kar sağanaklı",
    95: "gök gürültülü fırtınalı", 96: "dolu ve fırtınalı", 99: "dolu ve fırtınalı",
}


class WeatherSkill(Skill):
    """Open-Meteo (anahtarsız, ücretsiz). Konum yalnızca şehir adı olarak gönderilir."""

    name = "hava"
    description = "hava durumunu söylemek"
    rules = [
        rule(r"\bhava\b(?!\s*(?:yolu|yolları|alanı|limanı|kuvvet|yastığı|filtresi))"
             r"(?:\s+\w+){0,3}?\s*\b(durum\w*|nasıl|ne durumda|kaç derece|sıcak\w*|soğuk\w*|yağ\w*|"
             r"güzel mi|açık mı|bulutlu mu)", "weather"),
        rule(r"\b(yağmur|kar|sağanak)\w*\b.*\byağ\w*|\bkaç derece\b|\bşemsiye\b|\bmont\w* (al|giy)", "weather"),
    ]

    def __init__(self, city: str, http: Callable[[str], dict] = _http_json, ttl_s: float = 600):
        self.city = city
        self.http = http
        self.ttl_s = ttl_s
        self._geo: tuple[float, float, str] | None = None
        self._cache: tuple[float, dict] | None = None

    def _coords(self):
        if self._geo is None:
            q = urllib.parse.urlencode({"name": self.city, "count": 1, "language": "tr"})
            r = self.http(f"https://geocoding-api.open-meteo.com/v1/search?{q}").get("results") or []
            if not r:
                raise LookupError(self.city)
            self._geo = (r[0]["latitude"], r[0]["longitude"], r[0]["name"])
        return self._geo

    def _forecast(self) -> dict:
        if self._cache and time.monotonic() - self._cache[0] < self.ttl_s:
            return self._cache[1]
        lat, lon, _ = self._coords()
        q = urllib.parse.urlencode({
            "latitude": lat, "longitude": lon, "timezone": "auto", "forecast_days": 2,
            "current": "temperature_2m,weather_code",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code",
        })
        d = self.http(f"https://api.open-meteo.com/v1/forecast?{q}")
        self._cache = (time.monotonic(), d)
        return d

    def warm(self) -> None:
        """Açılışta arka planda çağrılır: ilk soruda konum arama + tahmin beklenmesin."""
        if self.city:
            try:
                self._forecast()
            except Exception:
                pass

    def run(self, action, m, clause):
        if not self.city:
            return SkillResult("Hangi şehrin havasına bakayım? Şehrini kişilik dosyasına yazarsan "
                               "bir daha sormam.", cacheable=True)
        d = self._forecast()
        name = self._coords()[2]
        day = 1 if re.search(r"\byarın\w*", clause) else 0
        daily = d["daily"]
        tmax = round(daily["temperature_2m_max"][day])
        tmin = round(daily["temperature_2m_min"][day])
        rain = daily["precipitation_probability_max"][day] or 0
        if day == 0:
            cur = d["current"]
            s = (f"{name} şu an {WMO_TR.get(cur['weather_code'], 'değişken')}, "
                 f"{sayi_yaz(round(cur['temperature_2m']))} derece. "
                 f"Bugün en yüksek {sayi_yaz(tmax)}, en düşük {sayi_yaz(tmin)} derece.")
        else:
            s = (f"Yarın {name} {WMO_TR.get(daily['weather_code'][1], 'değişken')}, "
                 f"en yüksek {sayi_yaz(tmax)}, en düşük {sayi_yaz(tmin)} derece.")
        if rain >= 50:
            s += f" Yağış ihtimali yüzde {sayi_yaz(rain)}, şemsiye almanı öneririm."
        elif rain >= 20:
            s += f" Yağış ihtimali yüzde {sayi_yaz(rain)}."
        return SkillResult(s)


# ----------------------------------------------------------------------------
MPRIS = "org.mpris.MediaPlayer2"


class MediaSkill(Skill):
    """Açık müzik/video çalarlar (Spotify, tarayıcı, VLC...) MPRIS/D-Bus üzerinden; ses pactl ile."""

    name = "medya"
    description = "müziği başlatmak, durdurmak, şarkı değiştirmek ve ses seviyesini ayarlamak"
    rules = [
        rule(r"\bses\w*\b.*\byüzde\s*(?P<pct>\d+)|\bses\w*\b.*\b(?P<pct2>\d+)\s*(yap|ayarla)", "vol_set"),
        rule(r"\bses\w*\b.*\b(aç|yükselt|artır|arttır|açar)\w*|\bdaha yüksek sesle\b", "vol_up"),
        rule(r"\bses\w*\b.*\b(kıs|azalt|düşür|alçalt)\w*|\bdaha (düşük|kısık) sesle\b", "vol_down"),
        rule(r"\b(sonraki|diğer|başka|sıradaki|yeni)\b.*\b(şarkı|parça|müzi)\w*|"
             r"\b(şarkı|parça|müzi)\w*\b.*\b(değiştir|geç|atla)\w*", "next"),
        rule(r"\b(önceki|bir önceki)\b.*\b(şarkı|parça|müzi)\w*", "previous"),
        rule(r"\b(müzi|şarkı|parça)\w*\b.*\b(durdur|kapat|dur|kes|sustur)\w*|\bsesi kapat\b", "pause"),
        rule(r"\b(müzi|şarkı|parça)\w*\b.*\b(çal|başlat|aç|devam)\w*|\b(müzi|şarkı)\w* (lazım|istiyorum)", "play"),
    ]

    def __init__(self, run: Callable[[list[str]], str] = _run):
        self.cmd = run

    # -- D-Bus --
    def _players(self) -> list[str]:
        out = self.cmd(["gdbus", "call", "--session", "--dest", "org.freedesktop.DBus",
                        "--object-path", "/org/freedesktop/DBus", "--method", "org.freedesktop.DBus.ListNames"])
        return re.findall(r"'(org\.mpris\.MediaPlayer2\.[^']+)'", out)

    def _status(self, p: str) -> str:
        try:
            out = self.cmd(["gdbus", "call", "--session", "--dest", p, "--object-path", "/org/mpris/MediaPlayer2",
                            "--method", "org.freedesktop.DBus.Properties.Get", f"{MPRIS}.Player", "PlaybackStatus"])
            m = re.search(r"'(Playing|Paused|Stopped)'", out)
            return m.group(1) if m else "?"
        except Exception:
            return "?"

    def _pick(self) -> str | None:
        ps = self._players()
        if not ps:
            return None
        st = {p: self._status(p) for p in ps}
        for want in ("Playing", "Paused"):
            for p in ps:
                if st[p] == want:
                    return p
        return ps[0]

    def _call(self, method: str) -> bool:
        p = self._pick()
        if not p:
            return False
        self.cmd(["gdbus", "call", "--session", "--dest", p, "--object-path", "/org/mpris/MediaPlayer2",
                  "--method", f"{MPRIS}.Player.{method}"])
        return True

    # -- ses --
    def _volume(self) -> int:
        out = self.cmd(["pactl", "get-sink-volume", "@DEFAULT_SINK@"])
        m = re.search(r"(\d+)%", out)
        return int(m.group(1)) if m else 0

    def _set_volume(self, pct: int) -> int:
        pct = max(0, min(150, pct))
        self.cmd(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{pct}%"])
        return pct

    def run(self, action, m, clause):
        if action in ("vol_up", "vol_down", "vol_set"):
            if action == "vol_set":
                pct = self._set_volume(int(m.group("pct") or m.group("pct2")))
            else:
                pct = self._set_volume(self._volume() + (10 if action == "vol_up" else -10))
            return SkillResult(f"Ses yüzde {sayi_yaz(pct)}.")
        method = {"play": "Play", "pause": "Pause", "next": "Next", "previous": "Previous"}[action]
        if not self._call(method):
            return SkillResult("Açık bir müzik çalar bulamadım.", cacheable=True)
        return SkillResult({"play": "Müzik başlıyor.", "pause": "Durdurdum.",
                            "next": "Sonraki şarkı.", "previous": "Önceki şarkı."}[action], cacheable=True)

    def fixed_phrases(self):
        return ["Müzik başlıyor.", "Durdurdum.", "Sonraki şarkı.", "Önceki şarkı.", "Açık bir müzik çalar bulamadım."]


# ----------------------------------------------------------------------------
class TimerSkill(Skill):
    name = "zamanlayıcı"
    description = "zamanlayıcı kurmak ve iptal etmek"
    rules = [
        rule(r"\b(zamanlayıcı|sayaç|alarm)\w*\b.*\b(iptal|kapat|sil|durdur)\w*", "cancel"),
        rule(r"\b(zamanlayıcı|sayaç|geri sayım)\w*|\b(saniye|dakika|saat)\w*\s+(sonra|içinde)\b.*\b(hatırlat|haber ver|söyle|uyar|uyandır)\w*|"
             r"\b(hatırlat|haber ver|uyar)\w*\b.*\b(saniye|dakika|saat)\w*\s+sonra\b", "set"),
    ]

    def __init__(self, announce: Callable[[str], None] = print,
                 timer_factory: Callable[[float, Callable], threading.Timer] = threading.Timer):
        self.announce = announce
        self.timer_factory = timer_factory
        self.timers: list[threading.Timer] = []

    def run(self, action, m, clause):
        if action == "cancel":
            n = sum(1 for t in self.timers if t.is_alive())
            for t in self.timers:
                t.cancel()
            self.timers.clear()
            return SkillResult("Zamanlayıcıyı iptal ettim." if n else "Kurulu zamanlayıcı yok.")
        secs = parse_duration(clause)
        if not secs:
            return SkillResult("Ne kadar süre için kurayım?", cacheable=True)
        note = ""
        nm = re.search(r"\b(?:sonra|içinde)\b\s+(.+?)\s+(?:diye\s+)?(?:hatırlat|haber ver|söyle|uyar)", clause)
        if nm:
            note = nm.group(1)
        msg = f"Zaman doldu. {note.capitalize()}." if note else "Zaman doldu!"
        t = self.timer_factory(secs, lambda: self.announce(msg))
        t.daemon = True
        t.start()
        self.timers.append(t)
        return SkillResult(f"Tamam, {sure_yaz(secs)} sonra haber vereceğim.")

    def fixed_phrases(self):
        return ["Ne kadar süre için kurayım?", "Zaman doldu!", "Kurulu zamanlayıcı yok.", "Zamanlayıcıyı iptal ettim."]


# ----------------------------------------------------------------------------
class DeviceBackend:
    """Ev cihazlarına bağlantı. Gerçek API (Home Assistant, kendi sunucun vb.) bunu uygular."""

    connected = False

    def set(self, device: str, state: str) -> None:
        raise NotImplementedError


DEVICE_NAMES = {"isik": "ışıklar", "klima": "klima", "tv": "televizyon", "kapi": "kapı", "perde": "perdeler"}


class DeviceSkill(Skill):
    name = "cihaz"
    description = "ışık, klima, televizyon, kapı ve perde komutlarını almak"
    rules = [
        rule(r"\b(ışı|lamba)\w*\b.*\b(aç|yak)\w*", "isik:on"),
        rule(r"\b(ışı|lamba)\w*\b.*\b(kapat|söndür)\w*", "isik:off"),
        rule(r"\bklima\w*\b.*\baç\w*", "klima:on"),
        rule(r"\bklima\w*\b.*\bkapat\w*", "klima:off"),
        rule(r"\b(televizyon|tv|tiviyi|teve)\w*\b.*\baç\w*", "tv:on"),
        rule(r"\b(televizyon|tv|tiviyi|teve)\w*\b.*\bkapat\w*", "tv:off"),
        rule(r"\bkapı\w*\b.*\b(aç)\w*", "kapi:on"),
        rule(r"\bkapı\w*\b.*\b(kapat|kilitle)\w*", "kapi:off"),
        rule(r"\bperde\w*\b.*\b(aç)\w*", "perde:on"),
        rule(r"\bperde\w*\b.*\b(kapat|çek)\w*", "perde:off"),
    ]

    def __init__(self, backend: DeviceBackend | None = None):
        self.backend = backend or DeviceBackend()

    def run(self, action, m, clause):
        dev, state = action.split(":")
        name = DEVICE_NAMES[dev]
        if not self.backend.connected:
            return SkillResult(f"{name.capitalize()} için henüz bir bağlantım yok.", cacheable=True)
        self.backend.set(dev, state)
        return SkillResult("Tamam.", cacheable=True)

    def fixed_phrases(self):
        return ["Tamam."] + [f"{n.capitalize()} için henüz bir bağlantım yok." for n in DEVICE_NAMES.values()]


def default_skills(city: str = "", announce: Callable[[str], None] = print,
                   devices: DeviceBackend | None = None) -> list[Skill]:
    # Sıra önemli: daha özel kurallar önce (ses seviyesi "aç" kelimesini cihazlardan önce alır)
    return [ClockSkill(), TimerSkill(announce), WeatherSkill(city), MediaSkill(), DeviceSkill(devices)]
