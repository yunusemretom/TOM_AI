"""Konuşma algılama (VAD) ve konuşma sonu tespiti.

Silero VAD her 32 ms'lik kare (16 kHz'de 512 örnek) için "bu konuşma mı?" olasılığı verir.
`Endpointer` bu olasılıklardan cümle sınırlarını çıkarır:
- Olasılık `threshold` üstünde `min_speech_ms` boyunca kalırsa konuşma başlar
  (kısa tıkırtı/öksürük elenir). Başlangıçtan önceki `pre_roll_ms` ses de eklenir,
  yoksa ilk hece kesilir.
- Olasılık `neg_threshold` altında `min_silence_ms` boyunca kalırsa konuşma biter ve
  tüm ifade tek parça olarak verilir. İki eşik (histerezis) sınırda titremeyi önler.
- `max_utterance_s` aşılırsa zorla bitirilir.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Callable

import numpy as np


@dataclass
class EndpointConfig:
    sample_rate: int = 16000
    frame: int = 512
    threshold: float = 0.5
    neg_threshold: float = 0.35
    min_speech_ms: int = 160
    min_silence_ms: int = 600
    pre_roll_ms: int = 300
    tail_ms: int = 128  # bitişte bırakılan sessizlik (son hece kesilmesin)
    max_utterance_s: float = 20.0

    def frames(self, ms: float) -> int:
        return max(1, round(ms * self.sample_rate / 1000 / self.frame))


@dataclass
class VadEvent:
    kind: str  # "start" | "end"
    audio: np.ndarray | None = None


class Endpointer:
    def __init__(self, prob_fn: Callable[[np.ndarray], float], cfg: EndpointConfig | None = None):
        self.prob_fn = prob_fn
        self.cfg = cfg or EndpointConfig()
        c = self.cfg
        self._n_speech = c.frames(c.min_speech_ms)
        self._n_silence = c.frames(c.min_silence_ms)
        self._n_tail = c.frames(c.tail_ms)
        self._n_max = int(c.max_utterance_s * c.sample_rate / c.frame)
        self._pre = deque(maxlen=c.frames(c.pre_roll_ms) + self._n_speech)
        self.reset()

    def reset(self) -> None:
        self.speaking = False
        self._pre.clear()
        self._utt: list[np.ndarray] = []
        self._run = 0  # başlangıç için art arda konuşma karesi
        self._silence = 0
        self.last_prob = 0.0

    def feed(self, frame: np.ndarray) -> list[VadEvent]:
        p = self.prob_fn(frame)
        self.last_prob = p
        c = self.cfg
        if not self.speaking:
            self._pre.append(frame)
            self._run = self._run + 1 if p >= c.threshold else 0
            if self._run >= self._n_speech:
                self.speaking = True
                self._utt = list(self._pre)
                self._pre.clear()
                self._silence = 0
                return [VadEvent("start")]
            return []

        self._utt.append(frame)
        self._silence = self._silence + 1 if p < c.neg_threshold else 0
        if self._silence >= self._n_silence or len(self._utt) >= self._n_max:
            drop = max(0, self._silence - self._n_tail)
            frames = self._utt[: len(self._utt) - drop] if drop else self._utt
            audio = np.concatenate(frames)
            self.reset()
            return [VadEvent("end", audio)]
        return []


class SileroVad:
    """Silero VAD (pip `silero-vad`, model pakete gömülü; internet gerekmez). CPU'da ~0,1 ms/kare."""

    def __init__(self, sample_rate: int = 16000):
        import torch
        from silero_vad import load_silero_vad

        torch.set_num_threads(1)
        self._torch = torch
        self.model = load_silero_vad()
        self.sample_rate = sample_rate

    def __call__(self, frame: np.ndarray) -> float:
        with self._torch.inference_mode():
            return float(self.model(self._torch.from_numpy(frame), self.sample_rate).item())

    def reset(self) -> None:
        self.model.reset_states()
