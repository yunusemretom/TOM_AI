"""faster-whisper ile Türkçe konuşma tanıma.

work_8'den farkları: ses diske yazılmaz, VAD'ın kestiği tek ifade bir kez çözülür
(biriken sesi tekrar tekrar çözmek yok), sıcaklık geri düşüşü kapalı (hız), bilinen
Whisper halüsinasyonları ("Altyazı M.K." vb.) ve sessizlik çıktıları elenir.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import numpy as np

# Whisper'ın sessizlikte/gürültüde uydurduğu, altyazı verisinden kalma kalıplar
HALLUCINATIONS = (
    "altyazı m.k",
    "altyazı",
    "abone olmayı unutmayın",
    "izlediğiniz için teşekkür",
    "videoyu beğenmeyi",
    "bir sonraki videoda görüşmek",
    "teşekkürler.",
)


@dataclass
class Transcript:
    text: str
    no_speech_prob: float
    avg_logprob: float
    language_prob: float


def tr_lower(s: str) -> str:
    return s.replace("I", "ı").replace("İ", "i").lower()


def is_repetitive(text: str, max_ratio: float = 2.4) -> bool:
    """Whisper'ın döngüye girip aynı öbeği tekrar etmesi ("bir günlük bir günlük ...").

    Tekrarlı metin çok iyi sıkışır; Whisper'ın kendi geri düşüş ölçütü de aynı orandır.
    """
    import zlib

    b = text.strip().encode("utf-8")
    if len(b) < 60:
        return False
    return len(b) / len(zlib.compress(b)) > max_ratio


def is_hallucination(text: str) -> bool:
    t = tr_lower(text).strip(" .!?…")
    if not t:
        return True
    return any(t == h.strip(" .") or (len(t) < 40 and h in t) for h in HALLUCINATIONS)


class WhisperSTT:
    def __init__(
        self,
        model: str = "large-v3-turbo",
        *,
        device: str = "cuda",
        compute_type: str | None = None,
        language: str = "tr",
        beam_size: int = 1,
        cpu_threads: int = 8,
    ):
        import torch  # noqa: F401  (CUDA/cuDNN kitaplıklarını ctranslate2'den önce yükler)
        from faster_whisper import WhisperModel

        if compute_type is None:
            compute_type = "int8_float16" if device == "cuda" else "int8"
        self.model = WhisperModel(model, device=device, compute_type=compute_type, cpu_threads=cpu_threads)
        self.language = language
        self.beam_size = beam_size

    def transcribe_full(self, audio: np.ndarray) -> Transcript:
        seconds = len(audio) / 16000
        segments, info = self.model.transcribe(
            audio.astype(np.float32),
            language=self.language,
            # Konuşma ~4 token/s; döngüye girerse 448 token boyunca saçmalamasın (gecikme de büyür)
            max_new_tokens=min(440, int(12 * seconds) + 24),
            beam_size=self.beam_size,
            temperature=0.0,
            condition_on_previous_text=False,
            without_timestamps=True,
            vad_filter=False,
        )
        segs = list(segments)
        text = " ".join(s.text.strip() for s in segs).strip()
        nsp = max((s.no_speech_prob for s in segs), default=1.0)
        alp = min((s.avg_logprob for s in segs), default=-10.0)
        return Transcript(re.sub(r"\s+", " ", text), nsp, alp, info.language_probability)

    def transcribe(self, audio: np.ndarray) -> str:
        """Boş string: konuşma yok / halüsinasyon."""
        t = self.transcribe_full(audio)
        if (is_hallucination(t.text) or is_repetitive(t.text)
                or (t.no_speech_prob > 0.6 and t.avg_logprob < -1.0)):
            return ""
        return t.text
