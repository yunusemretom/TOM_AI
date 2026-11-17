"""Uyandırma kelimesi ("Hey TOM"), sohbet penceresi ve uyku modu.

Ayrı bir uyandırma modeli yok: her konuşma parçası zaten Whisper'dan geçiyor (~0,3 sn), metnin başında
"Hey TOM" aranır. Kurallar:
- Uykudayken ya da sohbet penceresi kapalıyken yalnız "Hey TOM" ile başlayan cümleler dinlenir.
- TOM cevap verdikten sonra `window_s` boyunca uyandırma kelimesi gerekmez (doğal sohbet).
- Bilgisayarda video/müzik çalarken pencere yok sayılır: videodaki konuşmalar TOM'u tetiklemesin.
- `idle_sleep_s` boyunca kimse konuşmazsa uyku moduna geçilir (LLM bellekten çıkarılır).
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Callable

# Whisper "Hey TOM"u farklı yazabiliyor: Hey Tom, Hey Tam, Hei Tom, Tom, ...
_WAKE = re.compile(
    r"^\s*(?:(?:hey|hay|hei|hi|ey|heey|hey hey)[\s,.!]*)?(?:tom|tam|tum|thom|ton|tomm|tomb|tım|tomcuğum)\b[\s,.!?:;]*",
    re.I)
_HEY_ONLY = re.compile(r"^\s*(?:hey|hay|hei)\s+t\w{0,3}\b[\s,.!?:;]*", re.I)  # "Hey Thomas" gibi kaymalar

SLEEP = re.compile(r"\b(uyu|uyuyabilirsin|uyku moduna (geç|gir)\w*|uykuya (geç|dal)\w*|dinlenmeye geç\w*|"
                   r"beni dinleme\w*|bekleme moduna geç\w*)\b")

# TOM konuşurken söylenebilecek durdurma komutları
_STOP = re.compile(r"\b(sus|susar mısın|sussana|sessiz ol|sesini kes|kes sesini|yeter|tamam tamam|dur|durur musun|"
                   r"bekle|kes|stop)\b")
_STOP_SLEEP = re.compile(r"\b(uyu|uyku moduna|uykuya geç|beni dinleme)\w*")


def stop_command(heard: str, speaking_text: str = "") -> str | None:
    """TOM konuşurken duyulan parçada durdurma komutu var mı? "sleep" | "stop" | None.

    Mikrofon TOM'un kendi sesini de duyar: kelime TOM'un o an söylediği metinde de geçiyorsa yok sayılır
    (TOM kendi cümlesindeki "dur" ile kendini susturmasın)."""
    h, mine = _tr(heard), _tr(speaking_text)
    for rx, kind in ((_STOP_SLEEP, "sleep"), (_STOP, "stop")):
        for m in rx.finditer(h):
            if m.group(0) not in mine:
                return kind
    return None


PHRASE_HUH = "Efendim?"
PHRASE_HERE = "Buradayım."
PHRASE_SLEEP = "Tamam, uyuyorum. Uyandırmak için Hey TOM de."
PHRASES = [PHRASE_HUH, PHRASE_HERE, PHRASE_SLEEP]


def _tr(s: str) -> str:
    return s.replace("I", "ı").replace("İ", "i").lower()


def strip_wake(text: str) -> tuple[bool, str]:
    """("Hey Tom, saat kaç?") → (True, "saat kaç?"); uyandırma kelimesi yoksa (False, metin)."""
    m = _WAKE.match(_tr(text)) or _HEY_ONLY.match(_tr(text))
    if not m:
        return False, text
    rest = text[m.end():].strip()
    return True, (rest[0].upper() + rest[1:]) if rest else ""


def is_sleep_command(text: str) -> bool:
    return bool(SLEEP.search(_tr(text)))


@dataclass
class Decision:
    listen: bool          # bu cümleye cevap verilecek mi
    text: str             # uyandırma kelimesi atılmış metin
    woke: bool = False    # uykudan uyandı (LLM yeniden yüklenmeli)
    reason: str = ""


@dataclass
class WakeGate:
    window_s: float = 40.0
    idle_sleep_s: float = 600.0
    clock: Callable[[], float] = time.monotonic
    asleep: bool = False
    awake_until: float = 0.0
    last_activity: float = field(default=0.0)

    def __post_init__(self):
        self.last_activity = self.clock()

    def check(self, text: str, media_playing: bool = False) -> Decision:
        woke_word, rest = strip_wake(text)
        now = self.clock()
        if woke_word:
            woke = self.asleep
            self.asleep = False
            self.touch()
            return Decision(True, rest, woke=woke)
        if self.asleep:
            return Decision(False, text, reason="uykuda")
        if media_playing:
            return Decision(False, text, reason="video/müzik çalıyor")
        if now >= self.awake_until:
            return Decision(False, text, reason="Hey TOM denmedi")
        self.touch()
        return Decision(True, text)

    def touch(self) -> None:
        """Sohbet sürüyor: pencereyi şimdiden itibaren yeniden aç."""
        now = self.clock()
        self.awake_until = now + self.window_s
        self.last_activity = now

    def sleep(self) -> None:
        self.asleep = True
        self.awake_until = 0.0

    def should_auto_sleep(self) -> bool:
        return not self.asleep and self.clock() - self.last_activity > self.idle_sleep_s
