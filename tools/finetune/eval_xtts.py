"""Fine-tune öncesi/sonrası karşılaştırma: aynı cümleler, aynı referans ses.

    python eval_xtts.py --models temel=/content/xtts_base ince=/content/drive/.../hazir_model \
        --ref .../hazir_model/reference.wav --out /content/drive/.../degerlendirme

Her model için: Whisper ile anlaşılırlık (WER, düşük iyi) ve ECAPA ile referansa ses benzerliği
(yüksek iyi). Dinlemek için wav'lar da yazılır; son karar kulakla verilmeli.
"""

from __future__ import annotations

import argparse
import gc
import json
import re
import time
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
import torchaudio.functional as AF

SENTENCES = [
    "Merhaba Yunus, bugün nasılsın?",
    "Ankara'da hava parçalı bulutlu, akşama doğru yağmur bekleniyor.",
    "Veri yapıları sınavın için endişelenme, birlikte tekrar edebiliriz.",
    "Saat on dört, otuz beş. Toplantına yarım saat kaldı.",
    "Bunu hiç düşünmemiştim, gerçekten ilginç bir fikir!",
    "Işıklar için henüz bir bağlantım yok ama yakında olacak.",
]


def wer(ref: str, hyp: str) -> float:
    norm = lambda s: re.sub(r"[^\w\s]", " ", s.replace("I", "ı").replace("İ", "i").lower()).split()
    r, h = norm(ref), norm(hyp)
    d = list(range(len(h) + 1))
    for i, rw in enumerate(r, 1):
        prev, d[0] = d[0], i
        for j, hw in enumerate(h, 1):
            prev, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, prev + (rw != hw))
    return d[-1] / max(1, len(r))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--models", nargs="+", required=True, help="ad=klasör (model.pth, config.json, vocab.json)")
    ap.add_argument("--ref", required=True, help="Klon referansı (hedef konuşmacının temiz klibi)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--whisper", default="large-v3")
    args = ap.parse_args()

    from speechbrain.inference.speaker import EncoderClassifier
    from TTS.tts.configs.xtts_config import XttsConfig
    from TTS.tts.models.xtts import Xtts

    enc = EncoderClassifier.from_hparams("speechbrain/spkrec-ecapa-voxceleb", savedir="/tmp/ecapa",
                                         run_opts={"device": "cuda"})

    def emb(wav, sr):
        e = enc.encode_batch(AF.resample(torch.as_tensor(wav, dtype=torch.float32), sr, 16000)[None].cuda())
        e = e.flatten().cpu().numpy()
        return e / np.linalg.norm(e)

    ref_wav, ref_sr = sf.read(args.ref, dtype="float32")
    ref_emb = emb(ref_wav if ref_wav.ndim == 1 else ref_wav.mean(1), ref_sr)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    results = {}
    audio = {}
    for spec in args.models:
        name, d = spec.split("=", 1)
        cfg = XttsConfig()
        cfg.load_json(str(Path(d) / "config.json"))
        m = Xtts.init_from_config(cfg)
        m.load_checkpoint(cfg, checkpoint_dir=d, eval=True)
        m.cuda()
        g, s = m.get_conditioning_latents(audio_path=[args.ref], gpt_cond_len=cfg.gpt_cond_len,
                                          gpt_cond_chunk_len=cfg.gpt_cond_chunk_len, max_ref_length=cfg.max_ref_len)
        audio[name] = []
        sims, t0 = [], time.perf_counter()
        for i, text in enumerate(SENTENCES):
            torch.manual_seed(i)
            w = np.asarray(m.inference(text, "tr", g, s, temperature=0.65)["wav"], dtype=np.float32)
            sf.write(out / f"{name}_{i}.wav", w, 24000)
            audio[name].append(w)
            sims.append(float(emb(w, 24000) @ ref_emb))
        results[name] = {"benzerlik": round(float(np.mean(sims)), 3), "sure_s": round(time.perf_counter() - t0, 1)}
        del m, g, s
        gc.collect()
        torch.cuda.empty_cache()
    del enc
    gc.collect()
    torch.cuda.empty_cache()

    from faster_whisper import WhisperModel

    wh = WhisperModel(args.whisper, device="cuda", compute_type="int8_float16")
    for name, wavs in audio.items():
        ws = []
        for text, w in zip(SENTENCES, wavs):
            segs, _ = wh.transcribe(AF.resample(torch.from_numpy(w), 24000, 16000).numpy(), language="tr",
                                    beam_size=5, condition_on_previous_text=False)
            ws.append(wer(text, " ".join(x.text for x in segs)))
        results[name]["wer"] = round(float(np.mean(ws)), 3)

    (out / "sonuc.json").write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print("\n| model | referansa benzerlik (↑) | WER (↓) |\n|---|---|---|")
    for name, r in results.items():
        print(f"| {name} | {r['benzerlik']:.3f} | {r['wer']:.3f} |")
    print(f"\nSesler: {out}")


if __name__ == "__main__":
    main()
