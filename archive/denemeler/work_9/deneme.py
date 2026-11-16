import os
import torch
import torchaudio
from pathlib import Path
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts
import hashlib
import time

# Önbellek için klasör
CACHE_DIR = "audio_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def get_cache_path(text):
    """Metin için önbellek dosya yolunu oluştur."""
    text_hash = hashlib.md5(f"{text}_tr".encode()).hexdigest()
    return f"cache_{text_hash}.wav"

def clear_gpu_cache():
    """GPU belleğini temizle."""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

def load_model(checkpoint_path, config_path, vocab_path, speaker_path):
    """Modeli yükle."""
    clear_gpu_cache()
    
    # Konfigürasyonu yükle
    config = XttsConfig()
    config.load_json(config_path)
    config.language = "tr"  # Türkçe diliyle sınırlandır
    config.languages = ["tr"]  # Sadece Türkçe destekle

    # Modeli başlat ve yapılandır
    xtts_model = Xtts.init_from_config(config)
    print("Model yükleniyor...")
    xtts_model.load_checkpoint(
        config,
        checkpoint_path=checkpoint_path,
        vocab_path=vocab_path,
        speaker_file_path=speaker_path,
        use_deepspeed=False
    )

    if torch.cuda.is_available():
        xtts_model.cuda()

    print("Model başarıyla yüklendi!")
    return xtts_model

def run_tts(model, tts_text, speaker_audio_file):
    """TTS modeliyle ses üret."""
    gpt_cond_latent, speaker_embedding = model.get_conditioning_latents(
        audio_path=speaker_audio_file,
        gpt_cond_len=model.config.gpt_cond_len,
        max_ref_length=model.config.max_ref_len,
        sound_norm_refs=model.config.sound_norm_refs
    )

    # İnferans işlemi
    out = model.inference(
        text=tts_text,
        language="tr",  # Türkçe sabit
        gpt_cond_latent=gpt_cond_latent,
        speaker_embedding=speaker_embedding,
        temperature=0.8,
        length_penalty=1.0,
        repetition_penalty=1.2,
        top_k=40,
        top_p=0.95,
        enable_text_splitting=True
    )

    # Ses çıktısını kaydet
    output_file_name = get_cache_path(tts_text)
    out_path = os.path.join(CACHE_DIR, output_file_name)
    out["wav"] = torch.tensor(out["wav"]).unsqueeze(0)
    torchaudio.save(out_path, out["wav"], 22050)
    
    print(f"Ses dosyası oluşturuldu: {out_path}")
    return out_path

if __name__ == "__main__":
    # Model dosyalarının yolları
    model_path = r"C:\\Users\\TOM\\Documents\\Projeler\\Ses_fine_tune\\xtts-finetune-webui\\finetune_models\\ready\\model.pth"
    config_path = r"C:\\Users\\TOM\\Documents\\Projeler\\Ses_fine_tune\\xtts-finetune-webui\\finetune_models\\ready\\config.json"
    vocab_path = r"C:\\Users\\TOM\\Documents\\Projeler\\Ses_fine_tune\\xtts-finetune-webui\\finetune_models\\ready\\vocab.json"
    speaker_path = r"C:\\Users\\TOM\\Documents\\Projeler\\Ses_fine_tune\\xtts-finetune-webui\\finetune_models\\ready\\speakers_xtts.pth"

    # Modeli yükle
    model = load_model(model_path, config_path, vocab_path, speaker_path)

    while True:
        input_text = input("Metni girin: ")
        if not input_text.strip():
            print("Metin boş olamaz!")
            continue

        start_time = time.time()
        speaker_audio = "./ugur_t.mp3"  # Konuşmacı ses dosyası

        if not os.path.exists(speaker_audio):
            raise FileNotFoundError(f"Konuşmacı ses dosyası bulunamadı: {speaker_audio}")

        output_audio_path = run_tts(model, input_text, speaker_audio)
        print(f"Ses oluşturma süresi: {time.time() - start_time:.2f} saniye")

        # Opsiyonel: Ses dosyasını çalma (play_soundfile_deneme modülünü ekleyerek)
        # from play_soundfile_deneme import start_sound
        # start_sound(output_audio_path)
