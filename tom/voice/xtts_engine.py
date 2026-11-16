"""XTTS v2 motoru: önbellekli klon ses + akışlı üretim.

work_8'deki `ses_klonlama_2_00.py`'den farkları:
- Referans ses her cümlede değil, bir kez analiz edilir (bkz. speaker_cache).
- `stream()` sesi parça parça verir; cümlenin tamamını beklemeden çalmaya başlanabilir.
- Çıkış örnekleme hızı modelden okunur (24000 Hz). Eski kod 22050 Hz yazıyordu,
  bu yüzden ses ~%8 yavaş ve kalın çalıyordu.
- Diske WAV yazılmaz; numpy float32 dizisi döner.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator, Sequence

import numpy as np
import torch

from tom.voice.speaker_cache import SpeakerLatents, cache_key, load_or_compute
from tom.voice.text_prep import tts_text


class XttsEngine:
    def __init__(
        self,
        model_dir: Path | str,
        *,
        checkpoint: Path | str | None = None,
        vocab: Path | str | None = None,
        config: Path | str | None = None,
        device: str | None = None,
        use_deepspeed: bool = False,
        cache_dir: Path | str = "models/voices",
        language: str = "tr",
    ):
        d = Path(model_dir)
        self.checkpoint = Path(checkpoint) if checkpoint else d / "model.pth"
        self.vocab = Path(vocab) if vocab else d / "vocab.json"
        self.config_path = Path(config) if config else d / "config.json"
        speakers = d / "speakers_xtts.pth"
        self.speaker_file = speakers if speakers.exists() else None
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.use_deepspeed = use_deepspeed
        self.cache_dir = Path(cache_dir)
        self.language = language
        self.model = None
        self.config = None
        self.latents: SpeakerLatents | None = None
        self.voice_key: str | None = None  # ses + model kimliği (hazır cümle önbelleği için)

    # ---- yükleme -------------------------------------------------------
    def load(self) -> None:
        from TTS.tts.configs.xtts_config import XttsConfig
        from TTS.tts.models.xtts import Xtts

        config = XttsConfig()
        config.load_json(str(self.config_path))
        model = Xtts.init_from_config(config)
        model.load_checkpoint(
            config,
            checkpoint_path=str(self.checkpoint),
            vocab_path=str(self.vocab),
            speaker_file_path=str(self.speaker_file) if self.speaker_file else None,
            use_deepspeed=self.use_deepspeed,
        )
        model.to(self.device).eval()
        self.model, self.config = model, config

    @property
    def sample_rate(self) -> int:
        return int(self.config.model_args.output_sample_rate) if self.config else 24000

    def _latent_params(self) -> dict:
        c = self.config
        return {
            "gpt_cond_len": c.gpt_cond_len,
            "gpt_cond_chunk_len": c.gpt_cond_chunk_len,
            "max_ref_len": c.max_ref_len,
            "sound_norm_refs": c.sound_norm_refs,
        }

    def _model_id(self) -> str:
        st = self.checkpoint.stat()
        return f"{self.checkpoint.resolve()}:{st.st_size}:{st.st_mtime_ns}"

    def compute_latents(self, ref_paths: Sequence[Path | str]) -> SpeakerLatents:
        """Referans sesi analiz eder (yavaş yol, önbelleksiz)."""
        p = self._latent_params()
        with torch.inference_mode():
            gpt, spk = self.model.get_conditioning_latents(
                audio_path=[str(x) for x in ref_paths],
                gpt_cond_len=p["gpt_cond_len"],
                gpt_cond_chunk_len=p["gpt_cond_chunk_len"],
                max_ref_length=p["max_ref_len"],
                sound_norm_refs=p["sound_norm_refs"],
            )
        return SpeakerLatents(gpt, spk)

    def set_voice(self, ref_paths: Sequence[Path | str], name: str | None = None) -> bool:
        """Klon sesi ayarlar. Önbellekten geldiyse True döner."""
        if isinstance(ref_paths, (str, Path)):
            ref_paths = [ref_paths]
        name = name or Path(ref_paths[0]).stem
        key = cache_key(ref_paths, self._latent_params(), self._model_id())
        self.voice_key = f"{name}-{key}"
        self.latents, hit = load_or_compute(
            self.cache_dir, name, key, lambda: self.compute_latents(ref_paths)
        )
        return hit

    # ---- üretim --------------------------------------------------------
    def _gen_kwargs(self, overrides: dict) -> dict:
        c = self.config
        kw = {
            "temperature": c.temperature,
            "length_penalty": c.length_penalty,
            "repetition_penalty": c.repetition_penalty,
            "top_k": c.top_k,
            "top_p": c.top_p,
        }
        kw.update(overrides)
        return kw

    def stream(
        self, text: str, *, chunk_size: int = 20, language: str | None = None, **overrides
    ) -> Iterator[np.ndarray]:
        """Sesi parça parça (float32, mono, `sample_rate` Hz) üretir."""
        assert self.latents is not None, "önce set_voice() çağır"
        with torch.inference_mode():
            for chunk in self.model.inference_stream(
                tts_text(text),
                language or self.language,
                self.latents.gpt_cond_latent,
                self.latents.speaker_embedding,
                stream_chunk_size=chunk_size,
                enable_text_splitting=False,
                **self._gen_kwargs(overrides),
            ):
                yield chunk.float().cpu().numpy().reshape(-1)

    def synthesize(self, text: str, *, language: str | None = None, **overrides) -> np.ndarray:
        """Cümlenin tamamını tek seferde üretir."""
        assert self.latents is not None, "önce set_voice() çağır"
        with torch.inference_mode():
            out = self.model.inference(
                tts_text(text),
                language or self.language,
                self.latents.gpt_cond_latent,
                self.latents.speaker_embedding,
                enable_text_splitting=False,
                **self._gen_kwargs(overrides),
            )
        return np.asarray(out["wav"], dtype=np.float32).reshape(-1)

    def warmup(self) -> None:
        """İlk CUDA çağrısının yavaşlığını kullanıcıya yansıtmamak için kısa bir üretim."""
        for _ in self.stream("Merhaba."):
            pass
