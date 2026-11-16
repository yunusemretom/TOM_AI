"""TOM sesli asistan döngüsü: mikrofon → VAD → STT → (hızlı komut | LLM) → TTS → hoparlör.

Şimdilik yarı çift yönlü (half-duplex): asistan konuşurken mikrofon dinlenmez, çünkü
hoparlörden çıkan ses mikrofona geri girer (yankı iptali yok). Kulaklıkla
`barge_in` verilirse kullanıcı konuşmaya başlayınca asistan susar.
"""

from __future__ import annotations

import queue
import time
from dataclasses import dataclass, field
from typing import Callable, Iterable

import numpy as np

from tom.audio.vad import EndpointConfig, Endpointer
from tom.brain.ollama_client import stream_chat
from tom.brain.persona import Persona
from tom.brain.sentence_splitter import SentenceSplitter
from tom.pipeline.respond import ResponseTimings, respond


@dataclass
class TurnLog:
    user: str
    stt_s: float
    timings: ResponseTimings | None
    skills: list[str] = field(default_factory=list)
    fast_first_audio_s: float | None = None  # komut cevabının ilk sesi (STT sonrasından)

    def line(self) -> str:
        parts = [f"STT {self.stt_s*1000:.0f} ms"]
        if not self.user:
            return parts[0] + " (boş/halüsinasyon, yanıt yok)"
        if self.skills:
            parts.append(f"komut: {', '.join(self.skills)} → ilk ses "
                         f"{self.stt_s + self.fast_first_audio_s:.2f} s")
        t = self.timings
        if t is not None:
            first = t.first_audio if t.first_audio is not None else float("nan")
            parts.append(f"LLM ilk token {t.llm_first_token or 0:.2f} s | LLM ilk ses "
                         f"{self.stt_s + (self.fast_first_audio_s or 0) + first:.2f} s")
            parts.append(f"ses {t.audio_seconds:.1f} s, takılma {t.stall_seconds:.2f} s")
        return " | ".join(parts) + " (VAD sonundan)"


@dataclass
class Assistant:
    stt: object  # WhisperSTT
    vad: Callable[[np.ndarray], float]
    tts: object  # XttsEngine
    llm_model: str
    persona: Persona = field(default_factory=Persona)
    router: object | None = None  # tom.skills.router.Router
    phrases: object | None = None  # tom.voice.phrase_cache.PhraseCache
    vad_cfg: EndpointConfig = field(default_factory=EndpointConfig)
    max_history: int = 8  # son N mesaj (kullanıcı+asistan)
    llm_options: dict = field(default_factory=lambda: {"num_ctx": 2048, "temperature": 0.7})
    history: list[dict] = field(default_factory=list)

    def __post_init__(self):
        self.inbox: queue.Queue[str] = queue.Queue()  # zamanlayıcı gibi kendiliğinden söylenecekler

    def notify(self, text: str) -> None:
        self.inbox.put(text)

    def system_prompt(self) -> str:
        caps = self.router.capabilities() if self.router else None
        return self.persona.system_prompt(capabilities=caps)

    def speak(self, text: str, play: Callable[[np.ndarray], None]) -> None:
        audio = self.phrases.get(text) if self.phrases else None
        if audio is not None:
            play(audio)
            return
        for chunk in self.tts.stream(text):
            play(chunk)

    def respond_text(self, text: str, play: Callable[[np.ndarray], None], stt_s: float = 0.0) -> TurnLog:
        print(f"\n🗣  Sen: {text}", flush=True)
        log = TurnLog(text, stt_s, None)
        rest, said = text, []
        t0 = time.perf_counter()
        if self.router:
            routed = self.router.route(text)
            rest = routed.rest
            for name, res in routed.results:
                log.skills.append(name)
                print(f"⚡ TOM ({name}): {res.say}", flush=True)
                first = [True]

                def play_first(a, first=first):
                    if first[0] and log.fast_first_audio_s is None:
                        log.fast_first_audio_s = time.perf_counter() - t0
                    first[0] = False
                    play(a)

                self.speak(res.say, play_first)
                said.append(res.say)
        self.history.append({"role": "user", "content": text})
        if rest:
            msgs = [{"role": "system", "content": self.system_prompt()}] + self.history[-self.max_history:]
            if said:  # LLM, komutların zaten yapıldığını bilsin
                msgs[-1] = {"role": "user", "content": f"{rest}\n(Not: şu komutlar zaten yapıldı ve "
                            f"söylendi, tekrar etme: {' '.join(said)})"}
            tm = respond(stream_chat(msgs, self.llm_model, options=self.llm_options),
                         self.tts, play, SentenceSplitter())
            reply = " ".join(tm.text.split())
            print(f"🤖 TOM: {reply}", flush=True)
            said.append(reply)
            log.timings = tm
        self.history.append({"role": "assistant", "content": " ".join(said)})
        return log

    def answer(self, audio: np.ndarray, play: Callable[[np.ndarray], None]) -> TurnLog:
        t = time.perf_counter()
        text = self.stt.transcribe(audio)
        stt_s = time.perf_counter() - t
        if not text:
            return TurnLog("", stt_s, None)
        return self.respond_text(text, play, stt_s)

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
            if not speaking and not ep.speaking and not self.inbox.empty():
                msg = self.inbox.get_nowait()
                print(f"\n⏰ TOM: {msg}", flush=True)
                self.speak(msg, play)
                was_speaking = True
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
