"""LLM → cümle → TTS akışının uçtan uca ölçümü.

Kullanıcının sustuğu an t=0 kabul edilir (STT bu ölçüme dahil değil). Her istem için:
LLM ilk token, ilk cümle, ilk ses, toplam süre ve çalma sırasındaki takılma ölçülür.

    PYTHONPATH=. .venv/bin/python tools/pipeline_bench.py --llm gemma4:e2b gemma4:e4b \
        --model-dir ~/.local/share/tts/tts_models--multilingual--multi-dataset--xtts_v2 \
        --ref ~/Downloads/optimized_model/reference.wav --deepspeed --out logs/pipeline_bench
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import time
from pathlib import Path

import numpy as np
import soundfile as sf

from tom.brain.ollama_client import loaded_models, stream_chat, unload
from tom.brain.sentence_splitter import SentenceSplitter
from tom.pipeline.respond import respond
from tom.voice.xtts_engine import XttsEngine

SYSTEM = (
    "Sen TOM adında, Türkçe konuşan bir sesli asistansın. Cevapların sesli okunacak: "
    "kısa ve doğal konuş, genelde 1-3 cümle. Markdown, liste, emoji kullanma."
)

PROMPTS = [
    "Merhaba, nasılsın?",
    "Işıkları açar mısın?",
    "Kahve mi çay mı daha sağlıklı, kısaca anlatır mısın?",
    "Bana yarın sabah için kısa bir motivasyon cümlesi söyle.",
    "Güneş sistemindeki en büyük gezegen hangisi ve neden bu kadar büyük?",
]


def gpu_used_mib() -> int:
    out = subprocess.run(
        ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
        capture_output=True, text=True,
    ).stdout
    return int(out.strip().splitlines()[0])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--llm", nargs="+", default=["gemma4:e2b"])
    ap.add_argument("--model-dir", required=True)
    ap.add_argument("--ref", required=True, nargs="+")
    ap.add_argument("--deepspeed", action="store_true")
    ap.add_argument("--chunk-size", type=int, default=20)
    ap.add_argument("--num-ctx", type=int, default=2048)
    ap.add_argument("--first-min-chars", type=int, default=20)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    for m in args.llm:  # temiz başlangıç: TTS önce yer alsın
        try:
            unload(m)
        except Exception:
            pass
    time.sleep(1)

    base = gpu_used_mib()
    eng = XttsEngine(args.model_dir, use_deepspeed=args.deepspeed)
    eng.load()
    eng.set_voice(args.ref)
    eng.warmup()
    after_tts = gpu_used_mib()
    print(f"GPU: boş {base} MiB, XTTS sonrası {after_tts} MiB (deepspeed={args.deepspeed})")

    out = Path(args.out) if args.out else None
    if out:
        out.mkdir(parents=True, exist_ok=True)
    report = {"gpu_base_mib": base, "gpu_after_tts_mib": after_tts, "llms": {}}

    for model in args.llm:
        opts = {"num_ctx": args.num_ctx, "temperature": 0.7}
        t = time.perf_counter()
        for _ in stream_chat([{"role": "user", "content": "Merhaba"}], model, options=opts):
            pass
        t_load = time.perf_counter() - t
        ps = next((x for x in loaded_models() if x["name"].startswith(model)), {})
        gpu_frac = ps.get("size_vram", 0) / max(ps.get("size", 1), 1)
        used = gpu_used_mib()
        print(f"\n## {model}: yükleme+ilk yanıt {t_load:.1f} s, bellekte {ps.get('size', 0)/2**30:.1f} GiB, "
              f"GPU'da %{gpu_frac*100:.0f}, toplam GPU {used} MiB")

        rows = []
        for i, prompt in enumerate(PROMPTS):
            msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}]
            chunks: list[np.ndarray] = []
            tm = respond(
                stream_chat(msgs, model, options=opts),
                type("T", (), {"sample_rate": eng.sample_rate,
                               "stream": lambda self, s: eng.stream(s, chunk_size=args.chunk_size)})(),
                chunks.append,
                SentenceSplitter(first_min_chars=args.first_min_chars),
            )
            rows.append(dict(prompt=prompt, text=tm.text, sentences=tm.sentences,
                             llm_first_token=tm.llm_first_token, first_sentence=tm.first_sentence,
                             first_audio=tm.first_audio, llm_done=tm.llm_done, done=tm.done,
                             audio_s=tm.audio_seconds, stall_s=tm.stall_seconds))
            if out and chunks:
                sf.write(out / f"{model.replace(':', '_')}_{i}.wav", np.concatenate(chunks), eng.sample_rate)
            print(f"  [{i}] {prompt}\n      → {tm.text.strip()[:160]!r}")

        print("\n| istem | LLM ilk token | ilk cümle | **ilk ses** | LLM bitti | ses (s) | takılma (s) |")
        print("|---|---|---|---|---|---|---|")
        for i, r in enumerate(rows):
            print(f"| {i} | {r['llm_first_token']:.2f} | {r['first_sentence']:.2f} | **{r['first_audio']:.2f}** "
                  f"| {r['llm_done']:.2f} | {r['audio_s']:.1f} | {r['stall_s']:.2f} |")
        med = statistics.median(r["first_audio"] for r in rows)
        print(f"Medyan ilk ses: {med:.2f} s")
        report["llms"][model] = dict(load_s=t_load, gpu_frac=gpu_frac, gpu_used_mib=used,
                                     median_first_audio=med, rows=rows)
        unload(model)
        time.sleep(1)

    if out:
        (out / "sonuclar.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
        print(f"\nSesler ve JSON: {out}")


if __name__ == "__main__":
    main()
