"""Klon ses için konuşmacı latent önbelleği.

XTTS her konuşmada referans sesi baştan analiz etmek zorunda değil: referanstan çıkan
iki tensör (`gpt_cond_latent`, `speaker_embedding`) bir kez hesaplanıp diske yazılır.
Anahtar; referans sesin içeriğine, latent ayarlarına ve model ağırlıklarına bağlıdır,
bunlardan biri değişirse yeniden hesaplanır.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

import torch


@dataclass
class SpeakerLatents:
    gpt_cond_latent: torch.Tensor
    speaker_embedding: torch.Tensor


def cache_key(ref_paths: Iterable[Path | str], params: dict, model_id: str) -> str:
    """Referans ses içerikleri + latent ayarları + model kimliğinden kısa anahtar."""
    h = hashlib.sha256()
    for p in ref_paths:  # sıra önemli: XTTS referansları sırayla birleştirir
        h.update(hashlib.sha256(Path(p).read_bytes()).digest())
    h.update(json.dumps(params, sort_keys=True).encode())
    h.update(model_id.encode())
    return h.hexdigest()[:16]


def load_or_compute(
    cache_dir: Path | str,
    voice_name: str,
    key: str,
    compute: Callable[[], SpeakerLatents],
) -> tuple[SpeakerLatents, bool]:
    """Önbellekte varsa okur, yoksa hesaplayıp yazar. (latents, önbellekten_mi) döner."""
    path = Path(cache_dir) / f"{voice_name}-{key}.pt"
    if path.exists():
        data = torch.load(path, map_location="cpu", weights_only=True)
        return SpeakerLatents(data["gpt_cond_latent"], data["speaker_embedding"]), True

    latents = compute()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    torch.save(
        {
            "gpt_cond_latent": latents.gpt_cond_latent.detach().cpu(),
            "speaker_embedding": latents.speaker_embedding.detach().cpu(),
        },
        tmp,
    )
    tmp.replace(path)
    return latents, False
