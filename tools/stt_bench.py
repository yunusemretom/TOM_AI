"""STT hız/doğruluk ölçümü + VAD'ın gerçek kayıtlarda ifade kesmesinin kontrolü.

Girdi: `ses|metin` satırlı metadata (xtts-finetune-webui formatı: audio_file|text|speaker).

    PYTHONPATH=. .venv/bin/python tools/stt_bench.py \
        --data ~/Documents/Projeler/Ses_Klon/xtts-finetune-webui/finetune_models/dataset
"""

from __future__ import annotations

import argparse
import csv
import gc
import re
import statistics
import subprocess
import time
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
import torchaudio.functional as AF

from tom.audio.vad import EndpointConfig, Endpointer, SileroVad
from tom.listener.whisper_stt import WhisperSTT, tr_lower

CONFIGS = [
    # ad, model, cihaz, compute_type, beam
    ("turbo GPU int8f16 beam1", "large-v3-turbo", "cuda", "int8_float16", 1),
    ("turbo GPU int8f16 beam5", "large-v3-turbo", "cuda", "int8_float16", 5),
    ("turbo CPU int8 beam1", "large-v3-turbo", "cpu", "int8", 1),
    ("large-v3 GPU int8f16 beam1 (eski)", "large-v3", "cuda", "int8_float16", 1),
]


def norm(s: str) -> list[str]:
    return re.sub(r"[^\w\s]", " ", tr_lower(s)).split()


def wer_counts(ref: list[str], hyp: list[str]) -> tuple[int, int]:
    d = list(range(len(hyp) + 1))
    for i, r in enumerate(ref, 1):
        prev, d[0] = d[0], i
        for j, h in enumerate(hyp, 1):
            prev, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, prev + (r != h))
    return d[-1], len(ref)


def gpu_used() -> int:
    out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                         capture_output=True, text=True).stdout
    return int(out.split()[0])


def load_items(data: Path):
    items = []
    for name in ("metadata_train.csv", "metadata_eval.csv"):
        p = data / name
        if not p.exists():
            continue
        with p.open() as f:
            for row in csv.DictReader(f, delimiter="|"):
                wav, sr = sf.read(data / row["audio_file"], dtype="float32")
                if wav.ndim > 1:
                    wav = wav.mean(1)
                if sr != 16000:
                    wav = AF.resample(torch.from_numpy(wav), sr, 16000).numpy()
                items.append((row["audio_file"], row["text"], wav))
    return items


def vad_check(items):
    """Her kaydı 1 sn sessizlikle çevreleyip gerçek zamanlıymış gibi VAD'dan geçirir."""
    vad = SileroVad()
    cfg = EndpointConfig()
    found, cut_ratio = [], []
    for _, _, wav in items:
        vad.reset()
        ep = Endpointer(vad, cfg)
        pad = np.zeros(16000, dtype=np.float32)
        x = np.concatenate([pad, wav, pad, pad])
        n = 0
        for k in range(0, len(x) - cfg.frame + 1, cfg.frame):
            for ev in ep.feed(x[k : k + cfg.frame]):
                if ev.kind == "end":
                    n += 1
                    cut_ratio.append(len(ev.audio) / len(wav))
        found.append(n)
    t = time.perf_counter()
    for k in range(0, 16000 * 10, 512):
        vad(np.zeros(512, dtype=np.float32))
    per_frame_ms = (time.perf_counter() - t) / (16000 * 10 / 512) * 1000
    return found, cut_ratio, per_frame_ms


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--only", nargs="*", help="Yalnız adı bu metni içeren ayarlar")
    args = ap.parse_args()

    items = load_items(Path(args.data).expanduser())
    durs = [len(w) / 16000 for *_, w in items]
    print(f"{len(items)} kayıt, ortalama {statistics.mean(durs):.1f} s (en uzun {max(durs):.1f} s)")

    found, ratio, vms = vad_check(items)
    exact = sum(1 for n in found if n == 1)
    print(f"VAD: {exact}/{len(items)} kayıtta tam 1 ifade; "
          f"0 ifade: {found.count(0)}, 2+: {sum(1 for n in found if n > 1)}; "
          f"kesilen ses / kayıt oranı medyan {statistics.median(ratio):.2f}; "
          f"Silero {vms:.2f} ms/kare (32 ms'lik kare)")

    print("\n| ayar | medyan (ms) | p90 (ms) | RTF | WER | VRAM (MiB) |")
    print("|---|---|---|---|---|---|")
    for name, model, dev, ct, beam in CONFIGS:
        if args.only and not any(o in name for o in args.only):
            continue
        before = gpu_used()
        stt = WhisperSTT(model, device=dev, compute_type=ct, beam_size=beam)
        vram = gpu_used() - before
        stt.transcribe(items[0][2])  # ısınma
        lat, errs, words, rtf = [], 0, 0, []
        worst = []
        for fn, ref, wav in items:
            t = time.perf_counter()
            hyp = stt.transcribe_full(wav).text
            dt = time.perf_counter() - t
            lat.append(dt)
            rtf.append(dt / (len(wav) / 16000))
            e, n = wer_counts(norm(ref), norm(hyp))
            errs += e
            words += n
            if e:
                worst.append((e, ref, hyp))
        lat_ms = sorted(x * 1000 for x in lat)
        p90 = lat_ms[int(0.9 * (len(lat_ms) - 1))]
        print(f"| {name} | {statistics.median(lat_ms):.0f} | {p90:.0f} | {statistics.mean(rtf):.3f} "
              f"| {errs / words * 100:.1f}% | {vram} |")
        for e, ref, hyp in sorted(worst, reverse=True)[:3]:
            print(f"|   hata örneği | {ref!r} → {hyp!r} |||||")
        del stt
        gc.collect()
        time.sleep(1)


if __name__ == "__main__":
    main()
