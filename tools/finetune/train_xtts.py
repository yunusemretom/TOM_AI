"""XTTS v2 GPT fine-tune (Colab A100 için; yerelde --smoke ile duman testi).

    python train_xtts.py --dataset /content/dataset --out /content/drive/MyDrive/TOM_AI/xtts_runs
    python train_xtts.py --export-only RUN_DIR/best_model.pth --out .../xtts_runs   # yalnız dışa aktar

Veri seti: build_dataset.py çıktısı (wavs/ + metadata_train.csv + metadata_eval.csv, coqui formatı).
Yalnız GPT kısmı eğitilir; DVAE ve HiFiGAN vokoder donuk kalır (standart XTTS fine-tune).
Sürümler yereldeki çıkarım ortamıyla aynı olmalı: coqui-tts 0.25.3, transformers 4.46.2.

Çıktı: <out>/hazir_model/ → model.pth, config.json, vocab.json, speakers_xtts.pth, reference.wav
TOM'da kullanım: python -m tom --xtts <hazir_model> --ref <hazir_model>/reference.wav
"""

from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import shutil
from pathlib import Path

BASE_FILES = ["model.pth", "config.json", "vocab.json", "dvae.pth", "mel_stats.pth", "speakers_xtts.pth"]


def ensure_base(base_dir: Path, revision: str = "main") -> Path:
    """Temel XTTS v2 dosyaları yoksa Hugging Face'ten (coqui/XTTS-v2) indirir."""
    base_dir.mkdir(parents=True, exist_ok=True)
    missing = [f for f in BASE_FILES if not (base_dir / f).exists()]
    if missing:
        from huggingface_hub import hf_hub_download

        for f in missing:
            print(f"İndiriliyor: {f}", flush=True)
            p = hf_hub_download("coqui/XTTS-v2", f, revision=revision)
            shutil.copy(p, base_dir / f)
    return base_dir


def dataset_summary(ds: Path) -> dict:
    import soundfile as sf

    out = {}
    for name in ("metadata_train.csv", "metadata_eval.csv"):
        with open(ds / name, encoding="utf-8") as f:
            rows = list(csv.DictReader(f, delimiter="|"))
        dur = sum(sf.info(ds / r["audio_file"]).duration for r in rows)
        out[name] = {"klip": len(rows), "dakika": round(dur / 60, 1)}
    return out


def pick_reference(ds: Path, max_s: float = 11.0) -> Path:
    """Doğrulama setindeki en uzun (≤ max_s) klip: TOM'da klon referansı olarak kullanılır."""
    import soundfile as sf

    with open(ds / "metadata_eval.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="|"))
    rows += list(csv.DictReader(open(ds / "metadata_train.csv", encoding="utf-8"), delimiter="|"))
    best = max((r for r in rows if sf.info(ds / r["audio_file"]).duration <= max_s),
               key=lambda r: sf.info(ds / r["audio_file"]).duration)
    return ds / best["audio_file"]


def build(args, base: Path):
    from TTS.config.shared_configs import BaseDatasetConfig
    from TTS.tts.datasets import load_tts_samples
    from TTS.tts.layers.xtts.trainer.gpt_trainer import GPTArgs, GPTTrainer, GPTTrainerConfig
    from TTS.tts.models.xtts import XttsAudioConfig  # 0.25'te buraya taşındı (0.24'te gpt_trainer'daydı)

    ds = Path(args.dataset)
    dataset_cfg = BaseDatasetConfig(formatter="coqui", dataset_name="tom", path=str(ds),
                                    meta_file_train="metadata_train.csv", meta_file_val="metadata_eval.csv",
                                    language="tr")
    model_args = GPTArgs(
        max_conditioning_length=132300,  # 6 sn
        min_conditioning_length=66150,   # 3 sn
        debug_loading_failures=False,
        max_wav_length=int(args.max_audio_s * 22050),
        max_text_length=200,
        mel_norm_file=str(base / "mel_stats.pth"),
        dvae_checkpoint=str(base / "dvae.pth"),
        xtts_checkpoint=str(base / "model.pth"),
        tokenizer_file=str(base / "vocab.json"),
        gpt_num_audio_tokens=1026,
        gpt_start_audio_token=1024,
        gpt_stop_audio_token=1025,
        gpt_use_masking_gt_prompt_approach=True,
        gpt_use_perceiver_resampler=True,
    )
    config = GPTTrainerConfig(
        epochs=args.epochs,
        output_path=str(Path(args.out) / "egitim"),
        model_args=model_args,
        run_name="tom_xtts_tr",
        project_name="TOM_AI",
        dashboard_logger="tensorboard",
        audio=XttsAudioConfig(sample_rate=22050, dvae_sample_rate=22050, output_sample_rate=24000),
        batch_size=args.batch,
        batch_group_size=48,
        eval_batch_size=args.batch,
        num_loader_workers=args.workers,
        num_eval_loader_workers=min(2, args.workers),
        eval_split_max_size=256,
        print_step=25,
        plot_step=100,
        log_model_step=1000,
        save_step=args.save_step,
        save_n_checkpoints=1,
        save_checkpoints=True,
        save_best_after=0,
        print_eval=True,
        optimizer="AdamW",
        optimizer_wd_only_on_weights=True,
        optimizer_params={"betas": [0.9, 0.96], "eps": 1e-8, "weight_decay": 1e-2},
        lr=args.lr,
        lr_scheduler="MultiStepLR",
        lr_scheduler_params={"milestones": [50000 * 18, 150000 * 18, 300000 * 18], "gamma": 0.5, "last_epoch": -1},
        test_sentences=[],
        mixed_precision=False,  # XTTS GPT'de fp16 kararsız; A100'de TF32 zaten açık
    )
    model = GPTTrainer.init_from_config(config)
    train_samples, eval_samples = load_tts_samples([dataset_cfg], eval_split=True,
                                                   eval_split_max_size=config.eval_split_max_size,
                                                   eval_split_size=config.eval_split_size)
    return config, model, train_samples, eval_samples


def smoke(config, model, train_samples) -> Path:
    """Tek batch ileri + geri geçiş (optimizer yok): veri biçimi, yapılandırma ve kayıp hesabı doğru mu?"""
    import torch

    model.cuda().train()
    loader = model.get_data_loader(config, {}, is_eval=False, samples=train_samples, verbose=True, num_gpus=0)
    batch = model.format_batch(next(iter(loader)))
    batch = {k: v.cuda() if torch.is_tensor(v) else v for k, v in batch.items()}
    batch = model.format_batch_on_device(batch)
    _, loss = model.train_step(batch, None)
    loss["loss"].backward()
    grads = sum(p.grad is not None for p in model.parameters())
    print(f"DUMAN TESTİ: kayıp={loss['loss'].item():.3f} (metin {loss['loss_text_ce'].item():.3f}, "
          f"ses {loss['loss_mel_ce'].item():.3f}); gradyanı olan parametre: {grads}", flush=True)
    model.zero_grad(set_to_none=True)
    ck = Path(args_global.out) / "duman_checkpoint.pth"
    ck.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"model": model.state_dict()}, ck)  # Trainer'ın kaydettiği biçimin aynısı ("xtts." önekli)
    return ck


def export(ckpt: Path, base: Path, out: Path, reference: Path | None) -> Path:
    """Trainer checkpoint'inden çıkarıma hazır klasör: optimizer ve DVAE atılır (~1,8 GB kalır)."""
    import torch

    dst = out / "hazir_model"
    dst.mkdir(parents=True, exist_ok=True)
    state = torch.load(ckpt, map_location="cpu", weights_only=False)["model"]
    # GPTTrainer: çıkarım modeli "xtts.*" altında; "dvae.*" ve "torch_mel_spectrogram_*" yalnız eğitimde gerekir
    if any(k.startswith("xtts.") for k in state):
        state = {k: v for k, v in state.items() if k.startswith("xtts.")}
    torch.save({"model": state}, dst / "model.pth")
    for f in ("config.json", "vocab.json", "speakers_xtts.pth"):
        shutil.copy(base / f, dst / f)
    if reference:
        shutil.copy(reference, dst / "reference.wav")
    (dst / "kaynak.json").write_text(json.dumps({"checkpoint": str(ckpt)}, ensure_ascii=False, indent=2))
    print(f"Hazır model: {dst}", flush=True)
    return dst


def find_best(run_root: Path) -> Path:
    cands = sorted(glob.glob(str(run_root / "**" / "best_model*.pth"), recursive=True), key=os.path.getmtime)
    if not cands:
        cands = sorted(glob.glob(str(run_root / "**" / "checkpoint_*.pth"), recursive=True), key=os.path.getmtime)
    if not cands:
        raise SystemExit(f"{run_root} altında checkpoint yok.")
    return Path(cands[-1])


def main():
    global args_global
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", help="build_dataset.py çıktı klasörü")
    ap.add_argument("--out", required=True, help="Çıktı (Colab'da Drive'da olsun: bağlantı koparsa kaybolmaz)")
    ap.add_argument("--base-dir", default="/content/xtts_base", help="Temel XTTS v2 dosyaları (yoksa iner)")
    ap.add_argument("--base-revision", default="main")
    ap.add_argument("--epochs", type=int, default=15)
    ap.add_argument("--batch", type=int, default=8, help="A100 40 GB için 8; 80 GB'ta 16 denenebilir")
    ap.add_argument("--grad-accum", type=int, default=1)
    ap.add_argument("--lr", type=float, default=5e-6)
    ap.add_argument("--max-audio-s", type=float, default=11.6)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--save-step", type=int, default=10000, help="Ara checkpoint sıklığı (en iyi model her epoch)")
    ap.add_argument("--continue-path", help="Yarıda kalan eğitimin klasörü (kaldığı yerden sürdür)")
    ap.add_argument("--export-only", help="Yalnız bu checkpoint'i dışa aktar")
    ap.add_argument("--smoke", action="store_true", help="Tek batch ileri/geri geçiş + dışa aktarım (eğitim yok)")
    args = args_global = ap.parse_args()

    base = ensure_base(Path(args.base_dir), args.base_revision)
    out = Path(args.out)
    if args.export_only:
        ref = pick_reference(Path(args.dataset)) if args.dataset else None
        export(Path(args.export_only), base, out, ref)
        return
    if not args.dataset:
        raise SystemExit("--dataset gerekli")
    print(json.dumps(dataset_summary(Path(args.dataset)), ensure_ascii=False), flush=True)

    import torch

    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True
    config, model, train_samples, eval_samples = build(args, base)
    print(f"Eğitim örneği: {len(train_samples)}, doğrulama: {len(eval_samples)}", flush=True)

    if args.smoke:
        ck = smoke(config, model, train_samples)
        del model
        torch.cuda.empty_cache()
        export(ck, base, out, pick_reference(Path(args.dataset)))
        return

    from trainer import Trainer, TrainerArgs

    trainer = Trainer(
        TrainerArgs(restore_path=None, skip_train_epoch=False, start_with_eval=True,
                    grad_accum_steps=args.grad_accum, continue_path=args.continue_path or ""),
        config, output_path=config.output_path, model=model,
        train_samples=train_samples, eval_samples=eval_samples,
    )
    trainer.fit()
    best = find_best(Path(config.output_path))
    print(f"En iyi checkpoint: {best}", flush=True)
    export(best, base, out, pick_reference(Path(args.dataset)))


args_global = None

if __name__ == "__main__":
    main()
