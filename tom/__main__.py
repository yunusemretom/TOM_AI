"""TOM'u başlat:  PYTHONPATH=. .venv/bin/python -m tom [--deepspeed] [--llm gemma4:e4b]

Deneme modları (mikrofon/hoparlör yerine):
    python -m tom --input-wav soru.wav --output-wav cevap.wav
    python -m tom --text "Saat kaç?" "Bana bir fıkra anlat" --output-wav cevap.wav
"""

from __future__ import annotations

import argparse
import os
import time
from pathlib import Path

import numpy as np

DEFAULT_XTTS = "~/.local/share/tts/tts_models--multilingual--multi-dataset--xtts_v2"
DEFAULT_REF = "~/Downloads/optimized_model/reference.wav"


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


def main():
    ap = argparse.ArgumentParser(prog="tom")
    ap.add_argument("--llm", default="gemma4:e2b")
    ap.add_argument("--xtts", default=DEFAULT_XTTS, help="XTTS model klasörü (model.pth, config.json, vocab.json)")
    ap.add_argument("--ref", default=[DEFAULT_REF], nargs="+", help="Klon ses referansı")
    ap.add_argument("--persona", default=None, help="Kişilik dosyası (varsayılan config/kisilik.yaml)")
    ap.add_argument("--stt-model", default="large-v3-turbo")
    ap.add_argument("--deepspeed", action="store_true")
    ap.add_argument("--silence-ms", type=int, default=600, help="Konuşma bitti saymak için sessizlik")
    ap.add_argument("--barge-in", action="store_true", help="Konuşurken araya girilebilsin (kulaklıkla)")
    ap.add_argument("--no-skills", action="store_true", help="Hızlı komutları kapat (her şey LLM'e)")
    ap.add_argument("--input-wav", help="Mikrofon yerine bu dosyayı dinle (deneme)")
    ap.add_argument("--text", nargs="+", help="Mikrofon yerine bu cümleleri sırayla sor (deneme)")
    ap.add_argument("--output-wav", help="Hoparlör yerine bu dosyaya yaz (deneme)")
    args = ap.parse_args()

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
    print("XTTS yükleniyor…", flush=True)
    tts = XttsEngine(Path(args.xtts).expanduser(), use_deepspeed=args.deepspeed)
    tts.load()
    tts.set_voice([Path(r).expanduser() for r in args.ref])
    tts.warmup()

    stt = None
    if not args.text:
        from tom.listener.whisper_stt import WhisperSTT

        print("Whisper yükleniyor…", flush=True)
        stt = WhisperSTT(args.stt_model)
        stt.transcribe(np.zeros(16000, dtype=np.float32))

    bot = Assistant(stt=stt, vad=SileroVad(), tts=tts, llm_model=args.llm, persona=persona,
                    vad_cfg=EndpointConfig(min_silence_ms=args.silence_ms))
    if not args.no_skills:
        bot.router = Router(default_skills(city=persona.sehir, announce=bot.notify))
        bot.phrases = PhraseCache(tts)
        n = bot.phrases.warm(bot.router.fixed_phrases())
        print(f"Hazır cümle sesleri: {len(bot.phrases.audio)} ({n} yeni üretildi)", flush=True)

    print(f"LLM ({args.llm}) ısınıyor…", flush=True)
    # Isınma aynı seçeneklerle olmalı: num_ctx değişirse Ollama modeli baştan yükler (~6 s)
    for _ in stream_chat([{"role": "system", "content": bot.system_prompt()},
                          {"role": "user", "content": "Merhaba"}], args.llm, options=bot.llm_options):
        pass
    print(f"Hazır ({time.perf_counter() - t:.0f} s).", flush=True)

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

    from tom.audio.io import MicStream, Player

    player = Player(tts.sample_rate)
    print("Dinliyorum. Çıkmak için Ctrl+C.\n", flush=True)
    try:
        with MicStream() as mic:
            def frames():
                while True:
                    yield mic.frames.get()

            bot.run(frames(), player.play, is_speaking=lambda: player.busy,
                    on_resume=mic.drain, barge_in=player.stop if args.barge_in else None)
    except KeyboardInterrupt:
        print("\nGörüşürüz.")
    finally:
        player.close()


if __name__ == "__main__":
    main()
