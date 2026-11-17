"""Ses ayarları: config/ses.yaml (yoksa config/ses.example.yaml).

Değiştirip TOM'u yeniden başlatman yeterli. Denemek için: `python tools/ses_dene.py`.
Komut satırındaki --xtts / --ref bu dosyadakileri geçersiz kılar.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SETTINGS_FILE = ROOT / "config" / "ses.yaml"
EXAMPLE_FILE = ROOT / "config" / "ses.example.yaml"

# yaml anahtarı → XTTS üretim parametresi
_GEN = {"hiz": "speed", "sicaklik": "temperature", "top_p": "top_p", "top_k": "top_k",
        "tekrar_cezasi": "repetition_penalty", "uzunluk_cezasi": "length_penalty"}


@dataclass
class VoiceSettings:
    model: str | None = None                      # XTTS klasörü (model.pth, config.json, vocab.json)
    referans: list[str] = field(default_factory=list)  # klonlanacak ses klipleri (wav)
    hiz: float | None = None                      # 1.0 normal; 0.9 daha yavaş, 1.15 daha hızlı
    sicaklik: float | None = None                 # 0.3 tekdüze/kararlı … 0.9 canlı/değişken
    top_p: float | None = None
    top_k: int | None = None
    tekrar_cezasi: float | None = None
    uzunluk_cezasi: float | None = None

    @classmethod
    def load(cls, path: Path | None = None) -> "VoiceSettings":
        p = path or (SETTINGS_FILE if SETTINGS_FILE.exists() else EXAMPLE_FILE)
        if not Path(p).exists():
            return cls()
        d = yaml.safe_load(Path(p).read_text(encoding="utf-8")) or {}
        ref = d.get("referans") or []
        return cls(model=_abs(d.get("model")), referans=[_abs(r) for r in ([ref] if isinstance(ref, str) else ref)],
                   **{k: d.get(k) for k in _GEN})

    def overrides(self) -> dict:
        """XTTS'e gidecek üretim parametreleri (yalnız dosyada verilenler; gerisi modelin config.json'ı)."""
        return {_GEN[k]: getattr(self, k) for k in _GEN if getattr(self, k) is not None}

    def style_key(self) -> str:
        """Üretim ayarları değişince hazır cümle sesleri yeniden üretilsin diye kısa özet."""
        o = self.overrides()
        return hashlib.sha1(json.dumps(o, sort_keys=True).encode()).hexdigest()[:8] if o else ""


def _abs(p: str | None) -> str | None:
    if not p:
        return None
    q = Path(p).expanduser()
    return str(q if q.is_absolute() else ROOT / q)
