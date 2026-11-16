"""Podcast / uzun kayıtlardan XTTS fine-tune veri seti üretir.

    PYTHONPATH=. .venv/bin/python -m tools.finetune.build_dataset podcastlar/ \
        --ref hedef_konusmaci_ornek.wav --out data/xtts_dataset --zip

Adımlar: ffmpeg ile çöz → (isteğe bağlı Demucs ile müziği ayır) → Whisper large-v3 kelime
zaman damgalı metin → cümle sınırlarında 3–11 sn klipler → metin normalleştirme (sayılar
yazıyla) → ses kalitesi süzgeci → klibi tekrar çözüp metni doğrula → ECAPA konuşmacı
kodlayıcısıyla hedef konuşmacıyı seç → 22050 Hz wav + metadata_train/eval.csv (coqui formatı).

--ref verilmezse en çok konuşan kişi hedef kabul edilir (podcast sunucusu). Konuk çoksa
--ref ile hedefin 10–30 sn'lik temiz bir örneğini ver. Konuşmacı ayrımı: ECAPA (SpeechBrain).
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
import torchaudio.functional as AF

from tools.finetune.dataset_lib import (Word, clip_bounds, clipping_ratio, merge_units, normalize_text_tr,
                                        rms_dbfs, sentence_units, split_train_eval, word_error_rate)

SR = 22050
AUDIO_EXT = {".mp3", ".m4a", ".wav", ".flac", ".ogg", ".opus", ".aac", ".webm", ".mp4", ".mkv"}


def decode(path: Path, sr: int = SR) -> np.ndarray:
    out = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(sr),
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.float32).copy()


def demucs_vocals(path: Path, tmp: Path) -> Path:
    try:
        subprocess.run([sys.executable, "-m", "demucs", "--two-stems", "vocals", "-n", "htdemucs",
                        "-o", str(tmp), str(path)], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        raise SystemExit(f"Demucs çalışmadı ({e}). Kurmak için: uv pip install --python .venv demucs")
    return tmp / "htdemucs" / path.stem / "vocals.wav"


def list_inputs(paths: list[str]) -> list[Path]:
    files = []
    for p in map(Path, paths):
        if p.is_dir():
            files += sorted(f for f in p.rglob("*") if f.suffix.lower() in AUDIO_EXT)
        elif p.exists():
            files.append(p)
        else:
            raise SystemExit(f"Bulunamadı: {p}")
    if not files:
        raise SystemExit("Ses dosyası bulunamadı.")
    return files


def to16k(a: np.ndarray) -> np.ndarray:
    return AF.resample(torch.from_numpy(a), SR, 16000).numpy()


def transcribe_words(whisper, audio16: np.ndarray, beam: int) -> list[list[Word]]:
    """Kelimeleri, güvenilmez segmentlerde bölünmüş gruplar halinde döner.

    Atılan bir segmentin iki yanı birleşirse klip sesi o kısmı içerir ama metni içermez;
    bu yüzden her güvenilir segment dizisi ayrı gruplanır.
    """
    segments, _ = whisper.transcribe(
        audio16, language="tr", beam_size=beam, word_timestamps=True, vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 400}, condition_on_previous_text=False,
    )
    runs, cur = [], []
    for seg in segments:
        bad = seg.no_speech_prob > 0.6 or seg.compression_ratio > 2.4 or seg.avg_logprob < -1.0
        if bad or not seg.words:
            if cur:
                runs.append(cur)
            cur = []
            continue
        cur += [Word(w.word.strip(), w.start, w.end, w.probability) for w in seg.words if w.word.strip()]
    if cur:
        runs.append(cur)
    return runs


class SpeakerEncoder:
    """ECAPA-TDNN (SpeechBrain, VoxCeleb) konuşmacı doğrulama modeli; ~80 MB, ilk çalıştırmada iner.

    XTTS'in kendi kodlayıcısı TTS seslerini ayırıyor ama gerçek kayıtlarda ECAPA daha güvenilir.
    """

    def __init__(self, savedir: str = "models/speechbrain/ecapa"):
        from speechbrain.inference.speaker import EncoderClassifier

        self.enc = EncoderClassifier.from_hparams("speechbrain/spkrec-ecapa-voxceleb", savedir=savedir,
                                                  run_opts={"device": "cuda"})

    def __call__(self, audio: np.ndarray) -> np.ndarray:
        with torch.inference_mode():
            w = AF.resample(torch.from_numpy(audio), SR, 16000)[None].cuda()
            e = self.enc.encode_batch(w).flatten().float().cpu().numpy()
        return e / (np.linalg.norm(e) + 1e-9)


def ref_embedding(enc: SpeakerEncoder, paths: list[str]) -> np.ndarray:
    embs = []
    for p in paths:
        a = decode(Path(p).expanduser())
        for k in range(0, max(1, len(a) - SR * 3), SR * 10):  # 10 sn'lik parçalar
            part = a[k : k + SR * 10]
            if len(part) >= SR * 3:
                embs.append(enc(part))
    m = np.mean(embs, axis=0)
    return m / np.linalg.norm(m)


def dominant_centroid(embs: np.ndarray, keep: float = 0.6, iters: int = 3) -> np.ndarray:
    """Referans yoksa: en kalabalık sesin merkezi (podcast sunucusu en çok konuşan kabul edilir)."""
    c = embs.mean(0)
    for _ in range(iters):
        c = c / np.linalg.norm(c)
        sims = embs @ c
        top = embs[sims >= np.quantile(sims, 1 - keep)]
        c = top.mean(0)
    return c / np.linalg.norm(c)


def level(audio: np.ndarray, target_dbfs: float = -20.0, peak: float = 0.95) -> np.ndarray:
    g = 10 ** ((target_dbfs - rms_dbfs(audio)) / 20)
    g = min(g, peak / (np.max(np.abs(audio)) + 1e-9))
    return (audio * g).astype(np.float32)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+", help="Ses dosyaları ya da klasörler")
    ap.add_argument("--out", default="data/xtts_dataset")
    ap.add_argument("--ref", nargs="*", help="Hedef konuşmacının temiz örneği (önerilir)")
    ap.add_argument("--speaker-threshold", type=float, default=0.5,
                    help="Hedefe ECAPA kosinüs benzerliği alt sınırı (aynı kişi ~0,6+, farklı ~0,3-)")
    ap.add_argument("--speaker-name", default="hedef")
    ap.add_argument("--whisper", default="large-v3")
    ap.add_argument("--beam", type=int, default=5)
    ap.add_argument("--min-s", type=float, default=3.0)
    ap.add_argument("--max-s", type=float, default=11.0, help="XTTS eğitimi 11,6 sn üstünü atar")
    ap.add_argument("--max-wer", type=float, default=0.15, help="Doğrulama çözümüyle izin verilen fark")
    ap.add_argument("--min-word-prob", type=float, default=0.2,
                    help="Klipteki en düşük Whisper kelime olasılığı (altı: uydurma kelime şüphesi)")
    ap.add_argument("--no-verify", action="store_true", help="Klibi ikinci kez çözme (hızlı, daha az güvenli)")
    ap.add_argument("--demucs", action="store_true", help="Önce müziği ayır (giriş/fon müziği varsa)")
    ap.add_argument("--eval-ratio", type=float, default=0.1)
    ap.add_argument("--zip", action="store_true", help="Colab'a yüklemek için zip'le")
    args = ap.parse_args()

    files = list_inputs(args.inputs)
    out = Path(args.out)
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"{out} boş değil; başka bir --out ver ya da klasörü sil.")
    (out / "wavs").mkdir(parents=True, exist_ok=True)

    from tom.brain.ollama_client import unload_all

    if unload_all():
        time.sleep(1)
    print(f"Konuşmacı kodlayıcısı (ECAPA) ve Whisper {args.whisper} yükleniyor…", flush=True)
    enc = SpeakerEncoder()  # önce: torch'un CUDA/cuDNN kitaplıkları ctranslate2'den önce yüklensin
    from faster_whisper import WhisperModel

    whisper = WhisperModel(args.whisper, device="cuda", compute_type="int8_float16")

    drops = Counter()
    total_audio = 0.0
    t0 = time.perf_counter()
    with tempfile.TemporaryDirectory() as tmp:
        # --- 1. aşama: metin + her cümlenin konuşmacı parmak izi -------------------------
        files_units = []  # (dosya, kaynak ses yolu, süre, tüm kelimeler, [(kelimeler, kopma, emb|None)])
        for fi, path in enumerate(files):
            src = demucs_vocals(path, Path(tmp)) if args.demucs else path
            audio = decode(src)
            dur = len(audio) / SR
            total_audio += dur
            print(f"[{fi + 1}/{len(files)}] {path.name}: {dur / 60:.1f} dk", flush=True)
            runs = transcribe_words(whisper, to16k(audio), args.beam)
            units = []
            for run in runs:
                units.append(([], True))  # güvenilmez segment sınırı: birleştirme
                for ws, brk in sentence_units(run, args.max_s):
                    emb = None
                    if ws and ws[-1].end - ws[0].start >= 1.0:  # kısa cümlede parmak izi güvenilmez
                        emb = enc(audio[int(ws[0].start * SR) : int(ws[-1].end * SR)])
                    units.append((ws, brk, emb))
            files_units.append((path, src, dur, [w for r in runs for w in r],
                                [u if len(u) == 3 else (u[0], u[1], None) for u in units]))
            print(f"    {sum(1 for u in units if u[0])} cümle ({time.perf_counter() - t0:.0f} s)", flush=True)

        all_embs = np.stack([u[2] for f in files_units for u in f[4] if u[2] is not None])
        target = ref_embedding(enc, args.ref) if args.ref else dominant_centroid(all_embs)
        sent_sims = all_embs @ target
        hist = np.histogram(sent_sims, bins=[-1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 1.01])[0]

        # --- 2. aşama: yalnız hedefe ait ardışık cümlelerden klip ------------------------
        records = []
        for path, src, dur, all_words, units in files_units:
            is_t = [None if e is None else float(e @ target) >= args.speaker_threshold for _, _, e in units]
            masked = []
            for k, (ws, brk, emb) in enumerate(units):
                ok = is_t[k]
                if ok is None and ws:  # kısa cümle: iki yanındaki cümleler hedefse hedef say
                    prev = next((is_t[j] for j in range(k - 1, -1, -1) if is_t[j] is not None), False)
                    nxt = next((is_t[j] for j in range(k + 1, len(units)) if is_t[j] is not None), False)
                    ok = prev and nxt
                if ws and not ok:
                    drops["başka konuşmacı (cümle)"] += 1
                masked.append((ws, brk) if ok else ([], True))
            audio = decode(src)
            index = {id(w): i for i, w in enumerate(all_words)}
            for clip in merge_units(masked, args.min_s, args.max_s):
                i0, i1 = index[id(clip.words[0])], index[id(clip.words[-1])]
                s, e = clip_bounds(clip.start, clip.end,
                                   all_words[i0 - 1].end if i0 > 0 else None,
                                   all_words[i1 + 1].start if i1 + 1 < len(all_words) else None, dur)
                seg = audio[int(s * SR) : int(e * SR)]
                text = normalize_text_tr(clip.text)
                if text is None:
                    drops["metin (sayı/simge okunuşu belirsiz)"] += 1
                    continue
                if not (args.min_s <= len(seg) / SR <= args.max_s + 0.5):
                    drops["süre"] += 1
                    continue
                if rms_dbfs(seg) < -40:
                    drops["çok sessiz"] += 1
                    continue
                if clipping_ratio(seg) > 0.001:
                    drops["kırpılmış ses"] += 1
                    continue
                if clip.min_prob < args.min_word_prob:
                    drops["düşük kelime güveni"] += 1
                    continue
                wer = 0.0
                if not args.no_verify:
                    segs, _ = whisper.transcribe(to16k(seg), language="tr", beam_size=args.beam,
                                                 condition_on_previous_text=False, without_timestamps=True)
                    wer = word_error_rate(clip.text, " ".join(x.text for x in segs))
                    if wer > args.max_wer:
                        drops["doğrulama (metin uyuşmuyor)"] += 1
                        continue
                sim = float(enc(seg) @ target)
                if sim < args.speaker_threshold:  # son güvenlik: klibin bütünü de hedef olmalı
                    drops["başka konuşmacı (klip)"] += 1
                    continue
                records.append(dict(src=path.name, start=s, end=e, text=text, wer=wer,
                                    min_prob=clip.min_prob, audio=seg, sim=sim))

    kept = records
    if not kept:
        raise SystemExit(f"Hiç klip kalmadı. Atılanlar: {dict(drops)}. --speaker-threshold'u düşürmeyi "
                         "ya da --ref vermeyi dene.")

    rows = []
    for k, r in enumerate(kept):
        name = f"wavs/{Path(r['src']).stem[:40].replace(' ', '_')}_{k:05d}.wav"
        sf.write(out / name, level(r["audio"]), SR, subtype="PCM_16")
        rows.append((name, r))
    train, ev = split_train_eval(rows, args.eval_ratio, seed=0)
    for fname, part in (("metadata_train.csv", train), ("metadata_eval.csv", ev)):
        with open(out / fname, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, delimiter="|", quoting=csv.QUOTE_NONE, escapechar="\\")
            w.writerow(["audio_file", "text", "speaker_name"])
            for name, r in part:
                w.writerow([name, r["text"].replace("|", " "), args.speaker_name])
    (out / "lang.txt").write_text("tr\n")

    # Dinleyip kontrol etmeye değer klipler: hedefe en az benzeyenler ve Whisper'ın en az emin olduğu
    review = sorted(rows, key=lambda nr: (nr[1]["sim"] - args.speaker_threshold) * 4 + nr[1]["min_prob"]
                    - nr[1]["wer"] * 2)[: max(10, len(rows) // 10)]
    with open(out / "gozden_gecir.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="|")
        w.writerow(["audio_file", "text", "benzerlik", "min_kelime_olasiligi", "dogrulama_wer", "kaynak", "baslangic_s"])
        for name, r in review:
            w.writerow([name, r["text"], f"{r['sim']:.3f}", f"{r['min_prob']:.2f}", f"{r['wer']:.2f}",
                        r["src"], f"{r['start']:.1f}"])

    kept_min = sum(len(r["audio"]) for r in kept) / SR / 60
    report = dict(
        giris_dosyasi=len(files), giris_dakika=round(total_audio / 60, 1), klip=len(kept), cumle=int(len(sent_sims)),
        kalan_dakika=round(kept_min, 1), egitim=len(train), dogrulama=len(ev),
        atilan=dict(drops), benzerlik_histogrami=dict(zip(
            ["<0.2", "0.2-0.3", "0.3-0.4", "0.4-0.5", "0.5-0.6", "0.6-0.7", "0.7-0.8", ">0.8"],
            map(int, hist))), sure_s=round(time.perf_counter() - t0),
    )
    (out / "rapor.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if kept_min < 15:
        print(f"\nUyarı: {kept_min:.1f} dk veri az. İyi sonuç için 20–60 dk hedefle (daha çok bölüm ekle).")
    if args.zip:
        z = shutil.make_archive(str(out), "zip", root_dir=out)
        print(f"Zip: {z}")


if __name__ == "__main__":
    main()
