import torch
import torchaudio
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts
import hashlib
from pathlib import Path
import functools
from typing import Optional

class OptimizedTTSHandler:
    def __init__(self, model_path: str, config_path: str, vocab_path: str, 
                 speaker_path: str, cache_dir: str = "audio_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Model konfigürasyonu
        config = XttsConfig()
        config.load_json(config_path)
        
        # Model optimizasyonları
        self.model = Xtts.init_from_config(config)
        self.model.load_checkpoint(
            config,
            checkpoint_path=model_path,
            vocab_path=vocab_path,
            speaker_file_path=speaker_path,
            use_deepspeed=True  # DeepSpeed optimizasyonu
        )
        
        # GPU kullanımı
        if torch.cuda.is_available():
            self.model.cuda()
            torch.backends.cudnn.benchmark = True  # CUDA optimizasyonu
        
        # Önbellekleme
        self.get_conditioning = functools.lru_cache(maxsize=10)(
            self._get_conditioning
        )

    def _get_conditioning(self, speaker_audio: str):
        return self.model.get_conditioning_latents(
            audio_path=speaker_audio,
            gpt_cond_len=self.model.config.gpt_cond_len,
            max_ref_length=self.model.config.max_ref_len
        )

    def _get_cache_path(self, text: str, lang: str) -> Path:
        text_hash = hashlib.md5(f"{text}_{lang}".encode()).hexdigest()
        return self.cache_dir / f"cache_{text_hash}.wav"

    def generate_speech(self, text: str, lang: str, speaker_audio: str) -> Optional[str]:
        try:
            cache_path = self._get_cache_path(text, lang)
            if cache_path.exists():
                return str(cache_path)

            # Koşullu gizli değişkenleri al
            gpt_cond_latent, speaker_embedding = self.get_conditioning(speaker_audio)

            # Çıktı oluştur
            with torch.cuda.amp.autocast():  # Mixed precision
                out = self.model.inference(
                    text=text,
                    language=lang,
                    gpt_cond_latent=gpt_cond_latent,
                    speaker_embedding=speaker_embedding,
                    temperature=0.7,
                    length_penalty=1.0,
                    repetition_penalty=1.0,
                    top_k=30,
                    top_p=0.9
                )

            # Ses dosyasını kaydet
            wav = torch.tensor(out["wav"]).unsqueeze(0)
            torchaudio.save(cache_path, wav, 22050)
            
            return str(cache_path)

        except Exception as e:
            print(f"TTS Error: {e}")
            return None

    def clear_cache(self):
        """Önbelleği temizle"""
        self.get_conditioning.cache_clear()
        for file in self.cache_dir.glob("cache_*.wav"):
            file.unlink()
