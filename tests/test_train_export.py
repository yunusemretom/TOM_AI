import torch

from tools.finetune.train_xtts import export


def test_export_keeps_only_inference_weights(tmp_path):
    base = tmp_path / "base"
    base.mkdir()
    for f in ("config.json", "vocab.json", "speakers_xtts.pth"):
        (base / f).write_text("x")
    ck = tmp_path / "best_model.pth"
    torch.save({"model": {"xtts.gpt.w": torch.ones(2), "dvae.codebook": torch.ones(3),
                          "torch_mel_spectrogram_dvae.mel": torch.ones(1)},
                "optimizer": {"state": 1}, "step": 10}, ck)
    ref = tmp_path / "r.wav"
    ref.write_bytes(b"RIFF")
    dst = export(ck, base, tmp_path / "out", ref)
    saved = torch.load(dst / "model.pth", weights_only=False)
    assert list(saved) == ["model"] and list(saved["model"]) == ["xtts.gpt.w"]
    assert all((dst / f).exists() for f in ("config.json", "vocab.json", "speakers_xtts.pth", "reference.wav"))
