"""Düşün → konuş akışı: LLM metni cümle cümle TTS'e, TTS sesi parça parça çalara.

İki iş parçacığı çalışır:
  LLM iş parçacığı: token'ları okur, cümle bölücüden geçirir, cümle kuyruğuna koyar.
  TTS (çağıran) iş parçacığı: kuyruktan cümleyi alır, ses parçalarını `on_audio`'ya verir.
Böylece kullanıcı ilk cümleyi duyarken LLM sonraki cümleleri yazmaya devam eder.
"""

from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Iterable, Iterator

import numpy as np

from tom.brain.sentence_splitter import SentenceSplitter

_END = object()


@dataclass
class ResponseTimings:
    """Tüm süreler `respond()` çağrısından (kullanıcı sustu) itibaren saniye."""

    llm_first_token: float | None = None
    first_sentence: float | None = None
    first_audio: float | None = None
    llm_done: float | None = None
    done: float | None = None
    audio_seconds: float = 0.0
    stall_seconds: float = 0.0  # çalma sırasında sesin yetişmediği toplam süre
    sentences: list[str] = field(default_factory=list)
    text: str = ""


class _Synth:
    """Testlerde sahte motor verilebilsin diye XttsEngine'den beklenen arayüz."""

    sample_rate: int

    def stream(self, text: str) -> Iterator[np.ndarray]: ...


def respond(
    llm_pieces: Iterable[str],
    tts: _Synth,
    on_audio: Callable[[np.ndarray], None] = lambda a: None,
    splitter: SentenceSplitter | None = None,
) -> ResponseTimings:
    t0 = time.perf_counter()
    now = lambda: time.perf_counter() - t0
    tm = ResponseTimings()
    splitter = splitter or SentenceSplitter()
    sentences: queue.Queue = queue.Queue()
    err: list[BaseException] = []
    text_parts: list[str] = []

    def llm_worker():
        try:
            for piece in llm_pieces:
                if tm.llm_first_token is None:
                    tm.llm_first_token = now()
                text_parts.append(piece)
                for s in splitter.feed(piece):
                    sentences.put(s)
            for s in splitter.flush():
                sentences.put(s)
        except BaseException as e:  # hatayı ana iş parçacığına taşı
            err.append(e)
        finally:
            tm.llm_done = now()
            sentences.put(_END)

    th = threading.Thread(target=llm_worker, daemon=True)
    th.start()

    play_clock = None  # sesin çalınması bittiği an (gerçek zamanlı çalma benzetimi)
    sr = tts.sample_rate
    while True:
        s = sentences.get()
        if s is _END:
            break
        if tm.first_sentence is None:
            tm.first_sentence = now()
        tm.sentences.append(s)
        for chunk in tts.stream(s):
            t = now()
            if tm.first_audio is None:
                tm.first_audio = t
                play_clock = t
            elif t > play_clock:
                tm.stall_seconds += t - play_clock
                play_clock = t
            dur = len(chunk) / sr
            play_clock += dur
            tm.audio_seconds += dur
            on_audio(chunk)

    th.join()
    if err:
        raise err[0]
    tm.done = now()
    tm.text = "".join(text_parts)
    return tm
