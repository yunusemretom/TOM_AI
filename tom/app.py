"""TOM sesli asistan döngüsü: mikrofon → VAD → STT → LLM → TTS → hoparlör.

Şimdilik yarı çift yönlü (half-duplex): asistan konuşurken mikrofon dinlenmez, çünkü
hoparlörden çıkan ses mikrofona geri girer (yankı iptali yok). Kulaklıkla
`barge_in=True` verilirse kullanıcı konuşmaya başlayınca asistan susar.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Iterable

import numpy as np

from tom.audio.vad import EndpointConfig, Endpointer
from tom.brain.ollama_client import stream_chat
from tom.brain.sentence_splitter import SentenceSplitter
from tom.pipeline.respond import ResponseTimings, respond

SYSTEM_PROMPT = (
    "Sen TOM adında, Türkçe konuşan kişisel bir sesli asistansın. Cevapların sesli okunacak: "
    "kısa ve doğal konuş, en fazla 2-3 cümle. Markdown, liste, emoji ve kısaltma kullanma; "
    "sayıları yazıyla yaz."
)


@dataclass
class TurnLog:
    user: str
    stt_s: float
    timings: ResponseTimings | None

    def line(self) -> str:
        t = self.timings
        if t is None:
            return f"STT {self.stt_s*1000:.0f} ms (boş/halüsinasyon, yanıt yok)"
        return (f"STT {self.stt_s*1000:.0f} ms | LLM ilk token {t.llm_first_token:.2f} s | "
                f"ilk ses {self.stt_s + t.first_audio:.2f} s (VAD sonundan) | "
                f"ses {t.audio_seconds:.1f} s, takılma {t.stall_seconds:.2f} s")


@dataclass
class Assistant:
    stt: object  # WhisperSTT
    vad: Callable[[np.ndarray], float]
    tts: object  # XttsEngine
    llm_model: str
    system_prompt: str = SYSTEM_PROMPT
    vad_cfg: EndpointConfig = field(default_factory=EndpointConfig)
    max_history: int = 6  # son N mesaj (kullanıcı+asistan)
    llm_options: dict = field(default_factory=lambda: {"num_ctx": 2048, "temperature": 0.7})
    history: list[dict] = field(default_factory=list)

    def answer(self, audio: np.ndarray, play: Callable[[np.ndarray], None]) -> TurnLog:
        t = time.perf_counter()
        text = self.stt.transcribe(audio)
        stt_s = time.perf_counter() - t
        if not text:
            return TurnLog("", stt_s, None)
        print(f"\n🗣  Sen: {text}", flush=True)
        self.history.append({"role": "user", "content": text})
        msgs = [{"role": "system", "content": self.system_prompt}] + self.history[-self.max_history:]
        tm = respond(stream_chat(msgs, self.llm_model, options=self.llm_options),
                     self.tts, play, SentenceSplitter())
        reply = " ".join(tm.text.split())
        print(f"🤖 TOM: {reply}", flush=True)
        self.history.append({"role": "assistant", "content": reply})
        return TurnLog(text, stt_s, tm)

    def run(
        self,
        frames: Iterable[np.ndarray],
        play: Callable[[np.ndarray], None],
        *,
        is_speaking: Callable[[], bool] = lambda: False,
        on_resume: Callable[[], None] = lambda: None,
        barge_in: Callable[[], None] | None = None,
        max_turns: int | None = None,
    ) -> list[TurnLog]:
        ep = Endpointer(self.vad, self.vad_cfg)
        logs: list[TurnLog] = []
        was_speaking = False
        for fr in frames:
            speaking = is_speaking()
            if speaking and barge_in is None:
                was_speaking = True
                continue  # yarı çift yönlü: kendi sesini dinleme
            if was_speaking and not speaking:
                was_speaking = False
                ep.reset()
                on_resume()
                continue
            for ev in ep.feed(fr):
                if ev.kind == "start":
                    if speaking and barge_in:
                        barge_in()
                    print("🎙  …", end="", flush=True)
                elif ev.kind == "end":
                    log = self.answer(ev.audio, play)
                    print(f"   ⏱  {log.line()}", flush=True)
                    logs.append(log)
                    was_speaking = True  # yanıt çalarken gelen kareleri at
                    if max_turns and len(logs) >= max_turns:
                        return logs
        return logs
