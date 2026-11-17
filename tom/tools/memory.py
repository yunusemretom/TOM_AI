"""Kalıcı hafıza: kullanıcı hakkında bilgiler, notlar ve saatli hatırlatıcılar (data/hafiza.json, git dışı).

Hatırlatıcılar ayrı bir thread'de izlenir; zamanı gelince `notify` ile asistana verilir, o da
boşta olduğu ilk anda sesli söyler. Uygulama kapalıyken kaçan hatırlatıcı açılışta söylenir.
"""

from __future__ import annotations

import contextlib
import datetime as dt
import fcntl
import json
import threading
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FILE = ROOT / "data" / "hafiza.json"


class Memory:
    def __init__(self, path: Path = DEFAULT_FILE, now: Callable[[], dt.datetime] = dt.datetime.now):
        self.path = Path(path)
        self.now = now
        self.lock = threading.Lock()
        self.data = {"bilgiler": [], "notlar": [], "hatirlaticilar": []}
        self._mtime = None
        self._refresh()

    def _refresh(self) -> None:
        """Dosya başka süreçte (sesli TOM / API) değiştiyse yeniden oku: biri ötekinin yazdığını ezmesin."""
        try:
            m = self.path.stat().st_mtime_ns
        except FileNotFoundError:
            return
        if m == self._mtime:
            return
        try:
            d = json.loads(self.path.read_text(encoding="utf-8"))
        except ValueError:
            return
        self.data = {"bilgiler": [], "notlar": [], "hatirlaticilar": []}
        self.data.update(d)
        self._mtime = m

    @contextlib.contextmanager
    def _locked(self):
        """Süreç içi + süreçler arası kilit; içeride veri diskteki en son hâlidir."""
        with self.lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path.with_suffix(".lock"), "w") as lf:
                fcntl.flock(lf, fcntl.LOCK_EX)
                try:
                    self._refresh()
                    yield
                finally:
                    fcntl.flock(lf, fcntl.LOCK_UN)

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(self.path)
        self._mtime = self.path.stat().st_mtime_ns

    # ---- bilgiler (sistem istemine girer) ----
    @property
    def facts(self) -> list[str]:
        self._refresh()
        return list(self.data["bilgiler"])

    def hatirla(self, bilgi: str) -> str:
        bilgi = bilgi.strip()
        with self._locked():
            if bilgi and bilgi not in self.data["bilgiler"]:
                self.data["bilgiler"].append(bilgi)
                self._save()
        return f"Hafızaya eklendi: {bilgi}"

    def unut(self, ifade: str) -> str:
        key = ifade.lower().strip()
        with self._locked():
            gone = [b for b in self.data["bilgiler"] if key in b.lower()]
            self.data["bilgiler"] = [b for b in self.data["bilgiler"] if b not in gone]
            self._save()
        return f"Silindi: {'; '.join(gone)}" if gone else "Böyle bir bilgi hafızada yok."

    # ---- notlar ----
    def not_al(self, metin: str) -> str:
        with self._locked():
            self.data["notlar"].append({"zaman": self.now().strftime("%Y-%m-%d %H:%M"), "metin": metin.strip()})
            self._save()
        return f"Not alındı ({len(self.data['notlar'])}. not)."

    def notlari_oku(self, son: int = 5) -> str:
        self._refresh()
        n = self.data["notlar"][-max(1, int(son)):]
        return "\n".join(f"- {x['zaman']}: {x['metin']}" for x in n) if n else "Hiç not yok."

    # ---- hatırlatıcılar ----
    def hatirlatici_kur(self, zaman: str, mesaj: str) -> str:
        """zaman: 'YYYY-MM-DD HH:MM' (yerel saat)."""
        when = dt.datetime.strptime(zaman.strip().replace("T", " ")[:16], "%Y-%m-%d %H:%M")
        if when <= self.now():
            return f"Hata: {zaman} geçmişte kalıyor; şu an {self.now():%Y-%m-%d %H:%M}."
        with self._locked():
            self.data["hatirlaticilar"].append({"zaman": when.strftime("%Y-%m-%d %H:%M"), "mesaj": mesaj.strip()})
            self.data["hatirlaticilar"].sort(key=lambda x: x["zaman"])
            self._save()
        return f"Hatırlatıcı kuruldu: {when:%d.%m.%Y %H:%M} — {mesaj}"

    def hatirlaticilar(self) -> str:
        self._refresh()
        h = self.data["hatirlaticilar"]
        return "\n".join(f"- {x['zaman']}: {x['mesaj']}" for x in h) if h else "Kurulu hatırlatıcı yok."

    def hatirlatici_sil(self, ifade: str) -> str:
        key = ifade.lower().strip()
        with self._locked():
            gone = [x for x in self.data["hatirlaticilar"] if key in x["mesaj"].lower() or key in x["zaman"]]
            self.data["hatirlaticilar"] = [x for x in self.data["hatirlaticilar"] if x not in gone]
            self._save()
        return f"Silindi: {len(gone)} hatırlatıcı." if gone else "Eşleşen hatırlatıcı yok."

    def due(self) -> list[dict]:
        """Zamanı gelenleri listeden çıkarıp döner."""
        now = self.now().strftime("%Y-%m-%d %H:%M")
        with self._locked():
            due = [x for x in self.data["hatirlaticilar"] if x["zaman"] <= now]
            if due:
                self.data["hatirlaticilar"] = [x for x in self.data["hatirlaticilar"] if x not in due]
                self._save()
        return due

    def watch(self, notify: Callable[[str], None], every_s: float = 5.0) -> threading.Thread:
        def loop():
            ev = threading.Event()
            while not ev.wait(every_s):
                for x in self.due():
                    notify(f"Hatırlatma: {x['mesaj']}")
        t = threading.Thread(target=loop, daemon=True, name="tom-hatirlatici")
        t.start()
        return t
