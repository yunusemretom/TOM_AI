"""TOM'un sesini dene: config/ses.yaml ayarlarıyla (ya da komut satırından verilenlerle) örnek cümleler üretir.

    PYTHONPATH=. .venv/bin/python tools/ses_dene.py                      # ses.yaml ile 4 örnek cümle
    PYTHONPATH=. .venv/bin/python tools/ses_dene.py --hiz 0.9 --sicaklik 0.6 --cal
    PYTHONPATH=. .venv/bin/python tools/ses_dene.py --ref benim_sesim.wav --cumle "Merhaba Yunus, nasılsın?"
    PYTHONPATH=. .venv/bin/python tools/ses_dene.py --model models/xtts_ince_test2

Çıktı: logs/ses_dene/<saat>_<n>.wav (her deneme ayrı; dinleyip karşılaştır). TOM açıkken GPU yetmeyebilir,
önce TOM'u kapat.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import soundfile as sf

SENTENCES = [
    "Merhaba Yunus, bugün nasılsın?",
    "Ankara'da hava parçalı bulutlu, akşama doğru yağmur bekleniyor; şemsiyeni almayı unutma.",
    "Bunu hiç düşünmemiştim, gerçekten ilginç bir fikir! Hemen araştırıyorum.",
    "Yarın sabah dokuzda toplantın var. Saat on dört, otuz beşte de annenle konuşacaktın.",
]


def main():
    from tom.voice.settings import VoiceSettings

    s = VoiceSettings.load()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default=s.model, help="XTTS klasörü (varsayılan: ses.yaml)")
    ap.add_argument("--ref", nargs="+", default=s.referans, help="Referans klip(ler)")
    ap.add_argument("--hiz", type=float, default=s.hiz)
    ap.add_argument("--sicaklik", type=float, default=s.sicaklik)
    ap.add_argument("--top-p", type=float, default=s.top_p)
    ap.add_argument("--tekrar-cezasi", type=float, default=s.tekrar_cezasi)
    ap.add_argument("--cumle", nargs="+", help="Kendi cümlelerin (varsayılan: 4 örnek)")
    ap.add_argument("--cal", action="store_true", help="Üretince hoparlörden çal")
    ap.add_argument("--deepspeed", action="store_true")
    ap.add_argument("--cihaz", default=None, help="cuda ya da cpu (TOM açıkken GPU yetmezse cpu: yavaş ama çalışır)")
    args = ap.parse_args()

    from tom.voice.xtts_engine import XttsEngine

    v = VoiceSettings(model=args.model, referans=args.ref, hiz=args.hiz, sicaklik=args.sicaklik, top_p=args.top_p,
                      top_k=s.top_k, tekrar_cezasi=args.tekrar_cezasi, uzunluk_cezasi=s.uzunluk_cezasi)
    if not v.model or not v.referans:
        raise SystemExit("Model ya da referans yok: config/ses.yaml'ı doldur ya da --model/--ref ver.")
    print(f"Model: {v.model}\nReferans: {', '.join(Path(r).name for r in v.referans)}\nAyarlar: {v.overrides()}")
    tts = XttsEngine(Path(v.model), use_deepspeed=args.deepspeed, gen_overrides=v.overrides(), device=args.cihaz)
    tts.load()
    tts.set_voice(v.referans)

    out = Path("logs/ses_dene")
    out.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%H%M%S")
    clips = []
    for i, text in enumerate(args.cumle or SENTENCES):
        t = time.perf_counter()
        w = tts.synthesize(text)
        f = out / f"{stamp}_{i}.wav"
        sf.write(f, w, tts.sample_rate)
        clips.append(w)
        print(f"  {f}  ({len(w) / tts.sample_rate:.1f} sn ses, {time.perf_counter() - t:.1f} sn'de)  {text}")
    if args.cal:
        import sounddevice as sd

        gap = np.zeros(int(0.5 * tts.sample_rate), dtype=np.float32)
        sd.play(np.concatenate([np.concatenate([c, gap]) for c in clips]), tts.sample_rate)
        sd.wait()


if __name__ == "__main__":
    main()
