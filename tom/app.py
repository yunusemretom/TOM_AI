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
from tom.brain.agent import AgentTurn
from tom.brain.sentence_splitter import SentenceSplitter
from tom.pipeline.respond import ResponseTimings, respond


@dataclass
class TurnLog:
    user: str
    stt_s: float
    timings: ResponseTimings | None
    skills: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)  # LLM'in çağırdığı araçlar
    ignored: str = ""  # uyandırma kelimesi gerektiği için yok sayıldıysa nedeni
    fast_first_audio_s: float | None = None  # komut cevabının ilk sesi (STT sonrasından)

    def line(self) -> str:
        parts = [f"STT {self.stt_s*1000:.0f} ms"]
        if self.ignored:
            return parts[0] + f" · 💤 yok sayıldı ({self.ignored})"
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
        if self.tools:
            parts.append("araç: " + ", ".join(self.tools))
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
    agent: object | None = None   # tom.brain.agent.Agent: araçlı cevap (yoksa düz sohbet)
    memory: object | None = None  # tom.tools.memory.Memory: kalıcı bilgiler sistem istemine girer
    # torch'un önbelleğinde tuttuğu boş GPU belleğini bırakır (torch.cuda.empty_cache). XTTS'in ayırdığı ama
    # kullanmadığı bellek Whisper'a (CTranslate2, ayrı ayırıcı) geçsin; yoksa bir süre sonra Whisper OOM verir.
    free_gpu: Callable[[], None] = lambda: None
    # Uyandırma kelimesi ve uyku (tom.wake.WakeGate); None ise her cümle dinlenir
    wake: object | None = None
    media_playing: Callable[[], bool] = lambda: False  # video/müzik çalıyorsa her cümlede "Hey TOM" istenir
    on_sleep: Callable[[], None] = lambda: None        # uyurken: LLM'i bellekten çıkar
    on_wake: Callable[[], None] = lambda: None         # uyanınca: LLM'i arkada yeniden yükle

    def __post_init__(self):
        self.inbox: queue.Queue[str] = queue.Queue()  # zamanlayıcı gibi kendiliğinden söylenecekler

    def notify(self, text: str) -> None:
        self.inbox.put(text)

    def system_prompt(self) -> str:
        caps = self.router.capabilities() if self.router else None
        facts = self.memory.facts if self.memory else None
        return self.persona.system_prompt(capabilities=caps, tools=self.agent is not None, facts=facts)

    speaking_text: str = ""  # şu an söylenen metin (konuşurken susturmada kendi sesini ayırmak için)

    def speak(self, text: str, play: Callable[[np.ndarray], None]) -> None:
        self.speaking_text = text
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
            recent = self.history[-self.max_history:]
            while recent and (recent[0].get("role") != "user"):  # kesim araç mesajının ortasına düşmesin
                recent = recent[1:]
            msgs = [{"role": "system", "content": self.system_prompt()}] + recent
            if said:  # LLM, komutların zaten yapıldığını bilsin
                msgs[-1] = {"role": "user", "content": f"{rest}\n(Not: şu komutlar zaten yapıldı ve "
                            f"söylendi, tekrar etme: {' '.join(said)})"}
            if self.agent is not None:
                from tom.brain.agent import tool_hint

                hint = tool_hint(rest)
                if hint:
                    msgs[-1] = {"role": "user", "content": msgs[-1]["content"] + "\n" + hint}
            else:
                hint = None
            turn = AgentTurn()
            from tom.brain.agent import hinted_tools

            expected = hinted_tools(rest) if hint else []
            pieces = (self.agent.stream(msgs, turn, expect_tool=expected or bool(hint)) if self.agent is not None
                      else stream_chat(msgs, self.llm_model, options=self.llm_options))
            tm = respond(pieces, self.tts, play, SentenceSplitter())
            # Geçmişe söylenen cümleler girer (elenen kalıp kapanışlar girmez, model onları görüp tekrarlamasın)
            reply = " ".join(tm.sentences)
            self.speaking_text = " ".join(said + [reply])
            if turn.tools_used:
                print(f"🔧 araç: {', '.join(turn.tools_used)} ({turn.tool_seconds:.1f} s)"
                      + (" · ilk deneme aracı atladı, kurtarıldı" if turn.retried else ""), flush=True)
                log.tools += turn.tools_used
            print(f"🤖 TOM: {reply}", flush=True)
            said.append(reply)
            log.timings = tm
            self._remember_trace(turn.trace)
        self.history.append({"role": "assistant", "content": " ".join(said)})
        self.free_gpu()
        return log

    def _remember_trace(self, trace: list[dict], keep_chars: int = 1200) -> None:
        """Yalnız son turun araç mesajları geçmişte kalır (devam soruları için); eskileri atılır, bağlam şişmesin."""
        self.history = [m for m in self.history if m.get("role") != "tool" and not m.get("tool_calls")]
        for m in trace:
            m = dict(m)
            if m.get("role") == "tool" and len(m.get("content", "")) > keep_chars:
                m["content"] = m["content"][:keep_chars] + " …"
            self.history.append(m)

    def answer(self, audio: np.ndarray, play: Callable[[np.ndarray], None]) -> TurnLog:
        t = time.perf_counter()
        self.free_gpu()
        try:
            text = self.stt.transcribe(audio)
        except RuntimeError as e:
            if "out of memory" not in str(e).lower():
                raise
            print("⚠️  GPU belleği yetmedi, boşaltıp yeniden deniyorum…", flush=True)
            self.free_gpu()
            time.sleep(0.5)
            text = self.stt.transcribe(audio)  # yine olmazsa üst katman yeniden başlatır
        stt_s = time.perf_counter() - t
        if not text:
            return TurnLog("", stt_s, None)
        if self.wake is not None:
            from tom.wake import PHRASE_HERE, PHRASE_HUH, is_sleep_command

            d = self.wake.check(text, media_playing=self._media_playing())
            if not d.listen:
                return TurnLog(text, stt_s, None, ignored=f"{d.reason}: {text[:50]}")
            if d.woke:
                print("☀️  Uyandım.", flush=True)
                self.on_wake()
            text = d.text
            if not text:  # yalnız "Hey TOM"
                print(f"\n🗣  Sen: (Hey TOM)\n🤖 TOM: {PHRASE_HERE if d.woke else PHRASE_HUH}", flush=True)
                self.speak(PHRASE_HERE if d.woke else PHRASE_HUH, play)
                self.wake.touch()
                return TurnLog("(Hey TOM)", stt_s, None)
            if is_sleep_command(text):
                self.go_to_sleep(play)
                return TurnLog(text, stt_s, None, skills=["uyku"], fast_first_audio_s=0.0)
        log = self.respond_text(text, play, stt_s)
        if self.wake is not None:
            self.wake.touch()  # pencere cevap bittikten sonra başlar
        return log

    def _check_stop(self, audio: np.ndarray, interrupt: Callable[[], None]) -> bool:
        from tom.wake import stop_command

        try:
            heard = self.stt.transcribe(audio)
        except RuntimeError:
            return False
        kind = stop_command(heard, self.speaking_text) if heard else None
        if kind is None:
            return False
        interrupt()
        print(f"\n✋ Sen: {heard} → susturuldu", flush=True)
        if kind == "sleep" and self.wake is not None:
            self.go_to_sleep()
        elif self.wake is not None:
            self.wake.touch()
        return True

    def _media_playing(self) -> bool:
        try:
            return bool(self.media_playing())
        except Exception:  # noqa: BLE001 — D-Bus sorunu dinlemeyi engellemesin
            return False

    def go_to_sleep(self, play: Callable[[np.ndarray], None] | None = None) -> None:
        """Uyku modu: yalnız "Hey TOM" dinlenir, LLM bellekten çıkarılır (Whisper ve ses açık kalır)."""
        from tom.wake import PHRASE_SLEEP

        if self.wake is None or self.wake.asleep:
            return
        self.wake.sleep()
        print(f"\n😴 TOM: {PHRASE_SLEEP}" if play else "\n😴 Uzun süre konuşulmadı, uyku moduna geçtim.", flush=True)
        if play is not None:
            self.speak(PHRASE_SLEEP, play)
        self.on_sleep()

    def run(
        self,
        frames: Iterable[np.ndarray],
        play: Callable[[np.ndarray], None],
        *,
        is_speaking: Callable[[], bool] = lambda: False,
        on_resume: Callable[[], None] = lambda: None,
        barge_in: Callable[[], None] | None = None,
        interrupt: Callable[[], None] | None = None,
        max_turns: int | None = None,
    ) -> list[TurnLog]:
        """interrupt: TOM konuşurken "sus / sessiz ol / uyu" duyulursa çağrılır (çalmayı keser). Konuşurken
        mikrofon kısa parçalarla dinlenir; yalnız durdurma komutları aranır (kendi sesi metinle ayıklanır)."""
        ep = Endpointer(self.vad, self.vad_cfg)
        stop_ep = Endpointer(self.vad, EndpointConfig(min_silence_ms=250, max_utterance_s=2.5, min_speech_ms=120))
        logs: list[TurnLog] = []
        was_speaking = False
        for fr in frames:
            if self.wake is not None and self.wake.should_auto_sleep():
                self.go_to_sleep()
            speaking = is_speaking()
            if speaking and barge_in is None:
                was_speaking = True
                if interrupt is not None:
                    for ev in stop_ep.feed(fr):
                        if ev.kind == "end" and self._check_stop(ev.audio, interrupt):
                            stop_ep.reset()
                            break
                continue  # yarı çift yönlü: cevap için kendi sesini dinleme
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
