"""TOM'u başlat:  PYTHONPATH=. .venv/bin/python -m tom [--deepspeed] [--llm gemma4:e4b]

Deneme modları (mikrofon/hoparlör yerine):
    python -m tom --input-wav soru.wav --output-wav cevap.wav
    python -m tom --text "Saat kaç?" "Bana bir fıkra anlat" --output-wav cevap.wav
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import time
from pathlib import Path

import numpy as np

BASE_XTTS = "~/.local/share/tts/tts_models--multilingual--multi-dataset--xtts_v2"
BASE_REF = ["~/Downloads/optimized_model/reference.wav"]
# Fine-tune edilmiş model ve klon sesi (git dışı, models/ altında); yoksa temel XTTS'e dönülür
_ROOT = Path(__file__).resolve().parent.parent
TUNED_XTTS = str(_ROOT / "models/xtts_ince_test1")
TUNED_REF = [str(_ROOT / f"models/voices/ugur/ref_{i}.wav") for i in (1, 2, 3)]
DEFAULT_XTTS = TUNED_XTTS if Path(TUNED_XTTS, "model.pth").exists() else BASE_XTTS
DEFAULT_REF = TUNED_REF if all(Path(p).exists() for p in TUNED_REF) else BASE_REF


def file_frames(path: str, frame: int = 512):
    import soundfile as sf
    import torch
    import torchaudio.functional as AF

    wav, sr = sf.read(path, dtype="float32")
    if wav.ndim > 1:
        wav = wav.mean(1)
    if sr != 16000:
        wav = AF.resample(torch.from_numpy(wav), sr, 16000).numpy()
    pad = np.zeros(16000, dtype=np.float32)
    x = np.concatenate([pad, wav, pad, pad])
    for k in range(0, len(x) - frame + 1, frame):
        yield x[k : k + frame]


def free_gpu_from_ollama() -> None:
    """Önceki oturumdan Ollama'da yüklü kalan modelleri boşaltır.

    Ollama modelleri keep_alive süresince (30 dk) GPU'da kalır. TTS ve STT sabit yer ister,
    LLM ise kalan yere sığdığı kadarını GPU'ya alır; bu yüzden LLM en son yüklenmeli.
    """
    from tom.brain.ollama_client import unload_all

    names = unload_all()
    for n in names:
        print(f"Ollama'da yüklü kalan {n} boşaltıldı (GPU'da yer açmak için).", flush=True)
    if names:
        time.sleep(1.0)


def gpu_free_mib() -> int | None:
    try:
        import torch

        free, _ = torch.cuda.mem_get_info()
        return free // 2**20
    except Exception:
        return None


def make_parser(prog: str = "tom") -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog=prog)
    ap.add_argument("--llm", default="gemma4:e4b")
    ap.add_argument("--llm-gpu-layers", type=int, default=None,
                    help="LLM'in GPU'ya konan katman sayısı. XTTS+Whisper ~3,2 GB tuttuğu için e4b tamamen sığmaz; "
                         "verilmezse e4b'de 26 (6 GB kartta Whisper'a ~0,8 GB pay; 28'de uzun oturumda OOM oldu), "
                         "diğerlerinde Ollama karar verir")
    ap.add_argument("--xtts", default=None, help="XTTS model klasörü (verilmezse config/ses.yaml, o da yoksa "
                    "fine-tune edilmiş model)")
    ap.add_argument("--ref", default=None, nargs="+", help="Klon ses referansı (verilmezse config/ses.yaml)")
    ap.add_argument("--persona", default=None, help="Kişilik dosyası (varsayılan config/kisilik.yaml)")
    ap.add_argument("--stt-model", default="large-v3-turbo")
    ap.add_argument("--deepspeed", action="store_true")
    ap.add_argument("--silence-ms", type=int, default=600, help="Konuşma bitti saymak için sessizlik")
    ap.add_argument("--barge-in", action="store_true", help="Konuşurken araya girilebilsin (kulaklıkla)")
    ap.add_argument("--no-skills", action="store_true", help="Hızlı komutları kapat (her şey LLM'e)")
    ap.add_argument("--no-tools", action="store_true", help="LLM araçlarını kapat (web, hatırlatıcı, hafıza…)")
    ap.add_argument("--no-wake", action="store_true", help="'Hey TOM' uyandırma kelimesi olmadan her cümleyi dinle")
    ap.add_argument("--wake-window", type=float, default=40, help="Cevaptan sonra 'Hey TOM' gerekmeyen süre (s)")
    ap.add_argument("--idle-sleep", type=float, default=600, help="Bu kadar sessizlikten sonra uyu, LLM'i boşalt (s)")
    ap.add_argument("--input-wav", help="Mikrofon yerine bu dosyayı dinle (deneme)")
    ap.add_argument("--text", nargs="+", help="Mikrofon yerine bu cümleleri sırayla sor (deneme)")
    ap.add_argument("--output-wav", help="Hoparlör yerine bu dosyaya yaz (deneme)")
    return ap


def build(args, need_stt: bool = True):
    """Modelleri yükler (XTTS → Whisper → LLM sırası VRAM için önemli); (asistan, tts, kişilik) döner."""

    if args.deepspeed:
        os.environ.setdefault("CUDA_HOME", "/usr/local/cuda-12.4")
        os.environ["PATH"] = os.environ["CUDA_HOME"] + "/bin:" + os.environ["PATH"]

    from tom.app import Assistant
    from tom.audio.vad import EndpointConfig, SileroVad
    from tom.brain.ollama_client import stream_chat
    from tom.brain.persona import Persona
    from tom.skills.builtin import default_skills
    from tom.skills.router import Router
    from tom.voice.phrase_cache import PhraseCache
    from tom.voice.xtts_engine import XttsEngine

    t = time.perf_counter()
    persona = Persona.load(Path(args.persona) if args.persona else None)
    free_gpu_from_ollama()
    print("XTTS yükleniyor…", flush=True)
    from tom.voice.settings import VoiceSettings

    voice = VoiceSettings.load()
    args.xtts = args.xtts or voice.model or DEFAULT_XTTS
    args.ref = args.ref or voice.referans or DEFAULT_REF
    tts = XttsEngine(Path(args.xtts).expanduser(), use_deepspeed=args.deepspeed,
                     gen_overrides=voice.overrides(), style_key=voice.style_key())
    print(f"Ses: {Path(args.xtts).name} · {len(args.ref)} referans klip · {voice.overrides() or 'model ayarları'}",
          flush=True)
    tts.load()
    tts.set_voice([Path(r).expanduser() for r in args.ref])
    tts.warmup()

    stt = None
    if need_stt:
        from tom.listener.whisper_stt import WhisperSTT

        free = gpu_free_mib()
        if free is not None and free < 1100:
            import subprocess

            apps = subprocess.run(["nvidia-smi", "--query-compute-apps=pid,process_name,used_memory",
                                   "--format=csv,noheader"], capture_output=True, text=True).stdout.strip()
            raise SystemExit(
                f"GPU'da Whisper için yer yok ({free} MiB boş, ~1100 gerekli). GPU'yu kullanan süreçler:\n"
                f"{apps or '(listelenemedi)'}\nBunları kapatıp yeniden dene.")
        print("Whisper yükleniyor…", flush=True)
        stt = WhisperSTT(args.stt_model)
        stt.transcribe(np.zeros(16000, dtype=np.float32))

    bot = Assistant(stt=stt, vad=SileroVad(), tts=tts, llm_model=args.llm, persona=persona,
                    vad_cfg=EndpointConfig(min_silence_ms=args.silence_ms))
    import torch

    bot.free_gpu = torch.cuda.empty_cache  # her turdan sonra: XTTS'in tuttuğu boş bellek Whisper'a kalsın
    if not args.no_tools:
        from tom.brain.agent import Agent
        from tom.brain.ollama_client import stream_chat_events
        from tom.tools.memory import Memory
        from tom.tools.registry import default_toolbox

        bot.memory = Memory()
        for x in bot.memory.due():  # uygulama kapalıyken kaçan hatırlatıcılar
            bot.notify(f"Kaçırdığın hatırlatma ({x['zaman']}): {x['mesaj']}")
        bot.memory.watch(bot.notify)
        bot.llm_options["num_ctx"] = 4096  # araç sonuçları (web sayfaları) bağlama sığsın
        bot.llm_options["temperature"] = 0.4  # araç kararlarında tutarlılık
        from tom.tools.pc import bildir

        def tool_started(name, a):
            if name in ("web_ara", "web_oku", "haberler"):
                bildir("TOM araştırıyor 🔎", str(a.get("sorgu") or a.get("adres") or a.get("konu") or "gündem"))

        bot.agent = Agent(stream_chat_events, args.llm, default_toolbox(bot.memory), options=bot.llm_options,
                          on_tool_start=tool_started,
                          on_tool=lambda name, a, r: print(f"   🔧 {name}({', '.join(f'{k}={v!r}' for k, v in a.items())})"
                                                           f" → {r[:90]!r}", flush=True))
    layers = args.llm_gpu_layers if args.llm_gpu_layers is not None else (26 if "e4b" in args.llm else None)
    if layers is not None:
        bot.llm_options["num_gpu"] = layers  # ısınma da aynı seçeneklerle yapılır (yoksa Ollama modeli yeniden yükler)
    if not args.no_skills:
        bot.router = Router(default_skills(city=persona.sehir, announce=bot.notify))
        import threading

        for s in bot.router.skills:
            if hasattr(s, "warm"):
                threading.Thread(target=s.warm, daemon=True).start()
        bot.phrases = PhraseCache(tts)
        from tom.brain.agent import ALL_FILLERS
        from tom.brain.persona import selam
        greetings = [selam(persona.hitap, dt.datetime(2026, 1, 1, h)) for h in (8, 13, 19, 23)]
        from tom.wake import PHRASES as WAKE_PHRASES
        n = bot.phrases.warm(bot.router.fixed_phrases() + ALL_FILLERS + greetings + [selam("", restarted=True)]
                             + WAKE_PHRASES)
        print(f"Hazır cümle sesleri: {len(bot.phrases.audio)} ({n} yeni üretildi)", flush=True)

    def warm_llm():
        # Isınma aynı seçeneklerle olmalı: num_ctx değişirse Ollama modeli baştan yükler (~6 s)
        for _ in stream_chat([{"role": "system", "content": bot.system_prompt()},
                              {"role": "user", "content": "Merhaba"}], args.llm, options=bot.llm_options):
            pass

    print(f"LLM ({args.llm}) ısınıyor…", flush=True)
    warm_llm()
    print(f"Hazır ({time.perf_counter() - t:.0f} s).", flush=True)

    if not args.no_wake and not (args.text or args.input_wav):  # denemelerde her cümle dinlenir
        import threading

        from tom.brain.ollama_client import unload
        from tom.skills.builtin import MediaSkill
        from tom.wake import WakeGate

        bot.wake = WakeGate(window_s=args.wake_window, idle_sleep_s=args.idle_sleep)
        bot.wake.touch()  # açılıştan hemen sonra "Hey TOM" demeden konuşulabilsin
        media = MediaSkill()
        bot.media_playing = lambda: any(media._status(p) == "Playing" for p in media._players())

        def on_sleep():
            def go():
                try:
                    unload(args.llm)
                    print(f"   💤 {args.llm} bellekten çıkarıldı.", flush=True)
                except Exception as e:  # noqa: BLE001
                    print(f"   ⚠️  LLM boşaltılamadı: {e}", flush=True)
                bot.free_gpu()
            threading.Thread(target=go, daemon=True).start()

        def on_wake():
            threading.Thread(target=warm_llm, daemon=True).start()  # ilk cevap beklerken yüklenir

        bot.on_sleep, bot.on_wake = on_sleep, on_wake

    return bot, tts, persona


def main():
    args = make_parser().parse_args()
    bot, tts, persona = build(args, need_stt=not args.text)

    if args.input_wav or args.text:
        out: list[np.ndarray] = []
        if args.text:
            for q in args.text:
                log = bot.respond_text(q, out.append)
                print(f"   ⏱  {log.line()}", flush=True)
                out.append(np.zeros(int(0.6 * tts.sample_rate), dtype=np.float32))
        else:
            bot.run(file_frames(args.input_wav), out.append, max_turns=1)
        if args.output_wav and out:
            import soundfile as sf
            sf.write(args.output_wav, np.concatenate(out), tts.sample_rate)
            print(f"Cevap: {args.output_wav}")
        return

    run_live(bot, tts, persona, args)


class Control:
    """Pencereden canlı döngüye komutlar (thread güvenli): yazılı soru, mikrofonu kapat, uyut/uyandır, sustur."""

    def __init__(self):
        import queue

        self.texts: "queue.Queue[str]" = queue.Queue()
        self.actions: "queue.Queue[str]" = queue.Queue()
        self.mic_muted = False
        self.player = None
        self.stopped = False


def run_live(bot, tts, persona, args, control: Control | None = None, module: str = "tom") -> None:
    """Mikrofon + hoparlörle canlı sohbet. control verilirse pencere komutları da işlenir."""
    import numpy as np  # noqa: F811

    from tom.audio.io import MicStream, Player
    from tom.brain.persona import selam
    from tom.tools.pc import bildir

    restarted = os.environ.get("TOM_RESTARTED") == "1"
    if restarted:
        restore_history(bot)
    player = Player(tts.sample_rate)
    if control is not None:
        control.player = player
    hello = selam(persona.hitap, reminders=bot.memory.data["hatirlaticilar"] if bot.memory else None,
                  restarted=restarted)
    print(f"Dinliyorum. Çıkmak için Ctrl+C.\n\n👋 TOM: {hello}", flush=True)
    bildir("TOM hazır", hello)
    bot.on_event("state", {"state": "idle"})
    bot.on_event("tom", {"text": hello})
    bot.speak(hello, player.play)
    try:
        with MicStream() as mic:
            def frames():
                silence = np.zeros(512, dtype=np.float32)
                while control is None or not control.stopped:
                    if control is not None:
                        _handle_control(bot, control, player)
                    fr = mic.frames.get()
                    yield silence if control is not None and control.mic_muted else fr

            bot.run(frames(), player.play, is_speaking=lambda: player.busy,
                    on_resume=mic.drain, barge_in=player.stop if args.barge_in else None,
                    interrupt=player.stop)  # konuşurken "sus / sessiz ol / uyu" ile hemen sus
    except KeyboardInterrupt:
        print("\nGörüşürüz.")
    except Exception as e:  # noqa: BLE001 — GPU belleği yetmedi vb.: kendini yeniden başlat
        player.close()
        restart_after_crash(bot, e, module=module)
    finally:
        player.close()


def _handle_control(bot, control: Control, player) -> None:
    """Canlı döngünün kendi thread'inde çalışır: asistan aynı anda tek yerden kullanılır."""
    import queue

    while True:
        try:
            a = control.actions.get_nowait()
        except queue.Empty:
            break
        if a == "stop_speaking":
            player.stop()
        elif a == "sleep":
            player.stop()
            bot.go_to_sleep(player.play)
        elif a == "wake" and bot.wake is not None and bot.wake.asleep:
            from tom.wake import PHRASE_HERE

            bot.wake.asleep = False
            bot.wake.touch()
            bot.on_wake()
            bot.on_event("state", {"state": "idle"})
            bot.on_event("tom", {"text": PHRASE_HERE})
            bot.speak(PHRASE_HERE, player.play)
    while True:
        try:
            text = control.texts.get_nowait()
        except queue.Empty:
            break
        if bot.wake is not None:
            if bot.wake.asleep:
                bot.wake.asleep = False
                bot.on_wake()
            bot.wake.touch()
        bot.on_event("state", {"state": "thinking"})
        try:
            bot.respond_text(text, player.play)
        finally:
            bot.on_event("state", {"state": "idle"})
            if bot.wake is not None:
                bot.wake.touch()


HISTORY_FILE = Path(__file__).resolve().parent.parent / "data" / "son_konusma.json"


def restart_after_crash(bot, err: Exception, window_s: float = 600, max_restarts: int = 3, module: str = "tom") -> None:
    """Çökünce süreci aynı argümanlarla baştan başlatır (GPU belleği tamamen temizlenir). 10 dk'da 3'ten fazla
    çökerse döngüye girmemek için durur. Son konuşma diske yazılır, yeni süreç kaldığı yerden devam eder."""
    import json
    import sys
    import traceback

    traceback.print_exception(err)
    now = time.time()
    times = [float(t) for t in os.environ.get("TOM_RESTART_TIMES", "").split(",") if t]
    times = [t for t in times if now - t < window_s] + [now]
    if len(times) > max_restarts:
        print(f"\n❌ {len(times) - 1} kez üst üste çöktü, duruyorum. Son hata: {err}", flush=True)
        raise SystemExit(1)
    try:
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        HISTORY_FILE.write_text(json.dumps({"zaman": now, "gecmis": bot.history[-12:]}, ensure_ascii=False))
    except Exception:  # noqa: BLE001
        pass
    print(f"\n🔄 Hata: {err}\n   Yeniden başlatıyorum ({len(times)}/{max_restarts})…\n", flush=True)
    os.environ["TOM_RESTARTED"] = "1"
    os.environ["TOM_RESTART_TIMES"] = ",".join(f"{t:.0f}" for t in times)
    os.execv(sys.executable, [sys.executable, "-m", module, *sys.argv[1:]])


def restore_history(bot, max_age_s: float = 600) -> None:
    import json

    try:
        d = json.loads(HISTORY_FILE.read_text())
        if time.time() - d["zaman"] < max_age_s:
            bot.history = d["gecmis"]
    except Exception:  # noqa: BLE001
        pass


if __name__ == "__main__":
    main()
