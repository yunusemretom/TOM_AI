"""XTTS hız ölçümü: eski yol (her cümlede referans analizi + tam üretim) ile
yeni yol (önbellekli latent + akışlı üretim) karşılaştırması.

Çalıştırma (Coqui TTS kurulu ortamla):
    PYTHONPATH=. /path/to/venv/bin/python tools/tts_bench.py \
        --model-dir ~/.local/share/tts/tts_models--multilingual--multi-dataset--xtts_v2 \
        --ref ~/Downloads/optimized_model/reference.wav --out /tmp/tts_bench
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

import numpy as np
import soundfile as sf
import torch

from tom.voice.xtts_engine import XttsEngine

SENTENCES = [
    "Tamam, ışıkları açtım.",
    "Bugün hava parçalı bulutlu, akşama doğru yağmur bekleniyor.",
    "Merhaba! Sana nasıl yardımcı olabilirim? İstersen önce takvimine bakalım, sonra günün planını çıkaralım.",
]


def sync():
    if torch.cuda.is_available():
        torch.cuda.synchronize()


def timed(fn):
    sync()
    t = time.perf_counter()
    r = fn()
    sync()
    return r, time.perf_counter() - t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-dir", required=True)
    ap.add_argument("--ref", required=True, nargs="+")
    ap.add_argument("--cache-dir", default="models/voices")
    ap.add_argument("--out", default=None, help="Üretilen sesleri buraya yaz (dinlemek için)")
    ap.add_argument("--chunk-size", type=int, default=20)
    ap.add_argument("--repeats", type=int, default=2)
    ap.add_argument("--deepspeed", action="store_true")
    args = ap.parse_args()

    torch.manual_seed(0)
    eng = XttsEngine(args.model_dir, cache_dir=args.cache_dir, use_deepspeed=args.deepspeed)
    _, t_load = timed(eng.load)
    vram_model = torch.cuda.memory_allocated() / 2**20 if torch.cuda.is_available() else 0
    print(f"Model yükleme: {t_load:.1f} s, VRAM (model): {vram_model:.0f} MiB, cihaz: {eng.device}")

    # Referans analizi (eski kodun her cümlede ödediği bedel)
    eng.compute_latents(args.ref)  # ilk çağrı ısınma
    t_lat = [timed(lambda: eng.compute_latents(args.ref))[1] for _ in range(3)]
    hit, t_set = timed(lambda: eng.set_voice(args.ref))
    hit2, t_set2 = timed(lambda: eng.set_voice(args.ref))
    print(f"Referans analizi: {statistics.mean(t_lat)*1000:.0f} ms/çağrı")
    print(f"set_voice: 1. {t_set*1000:.0f} ms ({'önbellek' if hit else 'hesaplandı'}), "
          f"2. {t_set2*1000:.0f} ms ({'önbellek' if hit2 else 'hesaplandı'})")

    eng.warmup()
    torch.cuda.reset_peak_memory_stats() if torch.cuda.is_available() else None

    out = Path(args.out) if args.out else None
    if out:
        out.mkdir(parents=True, exist_ok=True)

    rows = []
    for i, text in enumerate(SENTENCES):
        for r in range(args.repeats):
            # Eski yol: referans analizi + tam üretim
            def old():
                eng.compute_latents(args.ref)
                return eng.synthesize(text)

            wav_old, t_old = timed(old)
            wav_full, t_full = timed(lambda: eng.synthesize(text))

            # Yeni yol: akışlı
            sync()
            t0 = time.perf_counter()
            ttfa, chunks = None, []
            for ch in eng.stream(text, chunk_size=args.chunk_size):
                if ttfa is None:
                    sync()
                    ttfa = time.perf_counter() - t0
                chunks.append(ch)
            sync()
            t_stream = time.perf_counter() - t0
            wav_stream = np.concatenate(chunks)
            dur = len(wav_stream) / eng.sample_rate

            rows.append(dict(i=i, rep=r, chars=len(text), audio_s=dur,
                             old_s=t_old, full_s=t_full, ttfa_s=ttfa,
                             stream_s=t_stream, rtf=t_stream / dur))
            if out and r == 0:
                sf.write(out / f"{i}_stream.wav", wav_stream, eng.sample_rate)
                sf.write(out / f"{i}_eski_22050.wav", wav_old, 22050)  # eski kodun yazdığı gibi
                sf.write(out / f"{i}_dogru_24000.wav", wav_old, eng.sample_rate)

    peak = torch.cuda.max_memory_allocated() / 2**20 if torch.cuda.is_available() else 0

    print("\n| cümle | ses (s) | eski yol: ilk ses (s) | önbellekli tam (s) | akış: ilk ses (s) | akış toplam (s) | RTF |")
    print("|---|---|---|---|---|---|---|")
    for i in range(len(SENTENCES)):
        rs = [x for x in rows if x["i"] == i]
        m = lambda k: statistics.mean(x[k] for x in rs)
        print(f"| {i} ({rs[0]['chars']} kr) | {m('audio_s'):.1f} | {m('old_s'):.2f} | {m('full_s'):.2f} "
              f"| {m('ttfa_s'):.2f} | {m('stream_s'):.2f} | {m('rtf'):.2f} |")
    print(f"\nÜretim sırasında en yüksek VRAM: {peak:.0f} MiB")

    if out:
        (out / "sonuclar.json").write_text(json.dumps(
            dict(load_s=t_load, latent_ms=statistics.mean(t_lat) * 1000,
                 set_voice_ms=[t_set * 1000, t_set2 * 1000], vram_model_mib=vram_model,
                 vram_peak_mib=peak, rows=rows), indent=2, ensure_ascii=False))
        print(f"Sesler ve JSON: {out}")


if __name__ == "__main__":
    main()
