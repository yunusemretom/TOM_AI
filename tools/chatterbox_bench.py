"""Chatterbox Multilingual (Türkçe) hız ölçümü; tts_bench.py ile aynı cümleler.

Chatterbox ayrı ortamda çalışır (transformers 5.x ister, XTTS ortamı 4.46'ya sabit):
    PYTHONPATH=. .venv-chatterbox/bin/python tools/chatterbox_bench.py \
        --ref ~/Downloads/optimized_model/reference.wav --out logs/chatterbox_bench

Akışlı üretim yok: cümle tamamen üretilince ses gelir. Cümle cümle boru hattında
"ilk ses" = ilk cümlenin üretim süresi.
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

import soundfile as sf
import torch

SENTENCES = [
    "Tamam, ışıkları açtım.",
    "Bugün hava parçalı bulutlu, akşama doğru yağmur bekleniyor.",
    "Merhaba! Sana nasıl yardımcı olabilirim? İstersen önce takvimine bakalım, sonra günün planını çıkaralım.",
]


def timed(fn):
    torch.cuda.synchronize()
    t = time.perf_counter()
    r = fn()
    torch.cuda.synchronize()
    return r, time.perf_counter() - t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--repeats", type=int, default=2)
    ap.add_argument("--cfg-weight", type=float, default=0.5)
    ap.add_argument("--exaggeration", type=float, default=0.5)
    ap.add_argument("--no-watermark", action="store_true", help="Perth filigranını atla (hız farkı için)")
    args = ap.parse_args()

    from chatterbox.mtl_tts import ChatterboxMultilingualTTS

    torch.manual_seed(0)
    model, t_load = timed(lambda: ChatterboxMultilingualTTS.from_pretrained(device="cuda"))
    if args.no_watermark:
        model.watermarker.apply_watermark = lambda wav, sample_rate: wav
    vram_model = torch.cuda.memory_allocated() / 2**20
    print(f"Model yükleme: {t_load:.1f} s, VRAM (model): {vram_model:.0f} MiB, sr={model.sr}")

    _, t_cond = timed(lambda: model.prepare_conditionals(args.ref, exaggeration=args.exaggeration))
    print(f"Referans analizi (bir kez): {t_cond*1000:.0f} ms")

    gen = lambda text: model.generate(text, language_id="tr", cfg_weight=args.cfg_weight,
                                      exaggeration=args.exaggeration)
    gen("Merhaba.")  # ısınma
    torch.cuda.reset_peak_memory_stats()

    out = Path(args.out) if args.out else None
    if out:
        out.mkdir(parents=True, exist_ok=True)
    rows = []
    for i, text in enumerate(SENTENCES):
        for r in range(args.repeats):
            wav, dt = timed(lambda: gen(text))
            dur = wav.shape[-1] / model.sr
            rows.append(dict(i=i, chars=len(text), audio_s=dur, gen_s=dt, rtf=dt / dur))
            if out and r == 0:
                sf.write(out / f"{i}_chatterbox.wav", wav.squeeze(0).numpy(), model.sr)
    peak = torch.cuda.max_memory_allocated() / 2**20

    print("\n| cümle | ses (s) | üretim = ilk ses (s) | RTF |")
    print("|---|---|---|---|")
    for i in range(len(SENTENCES)):
        rs = [x for x in rows if x["i"] == i]
        m = lambda k: statistics.mean(x[k] for x in rs)
        print(f"| {i} ({rs[0]['chars']} kr) | {m('audio_s'):.1f} | {m('gen_s'):.2f} | {m('rtf'):.2f} |")
    print(f"\nÜretim sırasında en yüksek VRAM: {peak:.0f} MiB")
    if out:
        (out / "sonuclar.json").write_text(json.dumps(
            dict(load_s=t_load, cond_ms=t_cond * 1000, vram_model_mib=vram_model,
                 vram_peak_mib=peak, rows=rows, args=vars(args)), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
