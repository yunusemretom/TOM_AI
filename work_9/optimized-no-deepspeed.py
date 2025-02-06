import torch
import torchaudio
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts
import hashlib
from pathlib import Path
import functools
from typing import Optional
import gc

class OptimizedTTSHandler:
    def __init__(self, model_path: str, config_path: str, vocab_path: str, 
                 speaker_path: str, cache_dir: str = "audio_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Model konfigürasyonu
        config = XttsConfig()
        config.load_json(config_path)
        
        # Model yükleme ve optimizasyon
        self.model = Xtts.init_from_config(config)
        self.model.load_checkpoint(
            config,
            checkpoint_path=model_path,
            vocab_path=vocab_path,
            speaker_file_path=speaker_path,
            use_deepspeed=False  # DeepSpeed kullanmıyoruz
        )
        
        # GPU optimizasyonları
        if torch.cuda.is_available():
            self.model.cuda()
            torch.backends.cudnn.benchmark = True
            # Daha verimli bellek kullanımı için
            torch.cuda.empty_cache()
        
        # Conditioning önbellekleme
        self.get_conditioning = functools.lru_cache(maxsize=10)(
            self._get_conditioning
        )

    def _get_conditioning(self, speaker_audio: str):
        try:
            # GPU belleğini temizle
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                
            return self.model.get_conditioning_latents(
                audio_path=speaker_audio,
                gpt_cond_len=self.model.config.gpt_cond_len,
                max_ref_length=self.model.config.max_ref_len,
                sound_norm_refs=False  # Daha az bellek kullanımı
            )
        except Exception as e:
            print(f"Conditioning Error: {e}")
            return None

    def _get_cache_path(self, text: str, lang: str) -> Path:
        text_hash = hashlib.md5(f"{text}_{lang}".encode()).hexdigest()
        return self.cache_dir / f"cache_{text_hash[:10]}.wav"

    def generate_speech(self, text: str, lang: str, speaker_audio: str) -> Optional[str]:
        try:
            # Önbellek kontrolü
            cache_path = self._get_cache_path(text, lang)
            if cache_path.exists():
                return str(cache_path)

            # GPU belleğini temizle
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                gc.collect()

            # Conditioning latents
            conditioning = self.get_conditioning(speaker_audio)
            if not conditioning:
                return None
                
            gpt_cond_latent, speaker_embedding = conditioning

            # Ses üretimi
            with torch.inference_mode():  # Daha az bellek kullanımı
                out = self.model.inference(
                    text=text,
                    language=lang,
                    gpt_cond_latent=gpt_cond_latent,
                    speaker_embedding=speaker_embedding,
                    temperature=0.7,  # Daha hızlı üretim
                    length_penalty=1.0,
                    repetition_penalty=1.0,
                    top_k=30,
                    top_p=0.9,
                    enable_text_splitting=True  # Uzun metinler için
                )

            # Ses dosyasını kaydet
            wav = torch.tensor(out["wav"]).unsqueeze(0)
            torchaudio.save(str(cache_path), wav, 22050)
            
            # Belleği temizle
            del out, wav
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            return str(cache_path)

        except Exception as e:
            print(f"TTS Error: {e}")
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            return None

    def clear_cache(self):
        """Önbelleği ve GPU belleğini temizle"""
        self.get_conditioning.cache_clear()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        # Eski önbellek dosyalarını temizle
        for file in self.cache_dir.glob("cache_*.wav"):
            try:
                file.unlink()
            except Exception:
                pass

def main():
    # Model yolları
    model_paths = {
        "model": r"C:\Users\TOM\Documents\Projeler\Ses_fine_tune\xtts-finetune-webui\finetune_models\ready\model.pth",
        "config": r"C:\Users\TOM\Documents\Projeler\Ses_fine_tune\xtts-finetune-webui\finetune_models\ready\config.json",
        "vocab":r"C:\Users\TOM\Documents\Projeler\Ses_fine_tune\xtts-finetune-webui\finetune_models\ready\vocab.json",
        "speaker": r"C:\Users\TOM\Documents\Projeler\Ses_fine_tune\xtts-finetune-webui\finetune_models\ready\speakers_xtts.pth",
        "speaker_audio": "./ugur_t.mp3"
    }   

    # TTS handler'ı başlat
    tts_handler = OptimizedTTSHandler(
        model_path=model_paths["model"],
        config_path=model_paths["config"],
        vocab_path=model_paths["vocab"],
        speaker_path=model_paths["speaker"]
    )

    # Test için örnek kullanım
    text = "Merhaba, bu bir test mesajıdır."
    audio_path = tts_handler.generate_speech(
        text=text,
        lang="tr",
        speaker_audio=model_paths["speaker_audio"]
    )

    if audio_path:
        print(f"Ses dosyası oluşturuldu: {audio_path}")
    else:
        print("Ses oluşturma başarısız oldu.")

if __name__ == "__main__":
    main()
