"""Sabit cevapların ("Müzik başlıyor.", "Durdurdum." ...) önceden üretilmiş sesleri.

Açılışta bir kez üretilip `models/voices/<ses>-phrases.npz` dosyasına yazılır; sonraki
açılışlarda diskten okunur. Komut cevabı sıfır gecikmeyle çalınır.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np


class PhraseCache:
    def __init__(self, tts, cache_dir: Path | str = "models/voices"):
        self.tts = tts
        self.path = Path(cache_dir) / f"{tts.voice_key}-phrases.npz"
        self.audio: dict[str, np.ndarray] = {}

    def warm(self, phrases: list[str]) -> int:
        """Eksik cümleleri üretir; kaç tane yeni üretildiğini döner."""
        if self.path.exists():
            with np.load(self.path, allow_pickle=False) as z:
                texts = [str(t) for t in z["texts"]]
                self.audio = {t: z[f"a{i}"] for i, t in enumerate(texts)}
        missing = [p for p in phrases if p not in self.audio]
        for p in missing:
            # Düşük sıcaklık: sabit cümle her seferinde aynı, düzgün çıksın
            self.audio[p] = self.tts.synthesize(p, temperature=0.3)
        if missing:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            texts = list(self.audio)
            np.savez(self.path, texts=np.array(texts), **{f"a{i}": self.audio[t] for i, t in enumerate(texts)})
        return len(missing)

    def get(self, text: str) -> np.ndarray | None:
        return self.audio.get(text)
