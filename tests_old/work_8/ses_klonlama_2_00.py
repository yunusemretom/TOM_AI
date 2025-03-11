import os
import torch
import torchaudio
from pathlib import Path
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts
import requests
import tempfile
import hashlib


CACHE_DIR = "audio_cache"
os.makedirs(CACHE_DIR, exist_ok=True)  # Klasör yoksa oluştur


def get_cache_path(text, language):  # Önbellek dosya yolunu oluştur
    text_hash = hashlib.md5(f"{text}_{language}".encode()).hexdigest()  # Metin ve dil bilgisinden hash oluştur
    return f"cache_{text_hash}.wav"  # Önbellek dosya yolunu döndür

# GPU kontrolü
def clear_gpu_cache():
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

# Modeli indirme
def download_file(url, destination):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(destination, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Downloaded file to {destination}")
        return destination
    except Exception as e:
        print(f"Failed to download the file: {e}")
        return None

# Model yükleme fonksiyonu
def load_model(xtts_checkpoint, xtts_config, xtts_vocab, xtts_speaker):
    clear_gpu_cache()
    if not xtts_checkpoint or not xtts_config or not xtts_vocab:
        raise ValueError("Model dosyaları eksik!")
    
    # Konfigürasyonu yükle
    config = XttsConfig()
    config.load_json(xtts_config)
    
    # Modeli başlat
    xtts_model = Xtts.init_from_config(config)
    print("Model yükleniyor...")
    xtts_model.load_checkpoint(
        config,
        checkpoint_path=xtts_checkpoint,
        vocab_path=xtts_vocab,
        speaker_file_path=xtts_speaker,
        use_deepspeed=False
    )
    if torch.cuda.is_available():
        xtts_model.cuda()
    print("Model başarıyla yüklendi!")
    return xtts_model

# TTS çalıştırma fonksiyonu
def run_tts(model, lang, tts_text, speaker_audio_file):
    gpt_cond_latent, speaker_embedding = model.get_conditioning_latents(
        audio_path=speaker_audio_file,
        gpt_cond_len=model.config.gpt_cond_len,
        max_ref_length=model.config.max_ref_len,
        sound_norm_refs=model.config.sound_norm_refs
    )

    out = model.inference(
        text=tts_text,
        language=lang,
        gpt_cond_latent=gpt_cond_latent,
        speaker_embedding=speaker_embedding,
        temperature=0.8,  # Özelleştirilebilir parametreler
        length_penalty=1.0,
        repetition_penalty=1.2,
        top_k=50,
        top_p=0.95,
        enable_text_splitting=True
    )

    # Ses çıktısını `audio_cache` klasörüne kaydet
    output_file_name = get_cache_path(tts_text,"tr")  # İlk 20 karakteri dosya adı yap
    out_path = os.path.join(CACHE_DIR, output_file_name)

    out["wav"] = torch.tensor(out["wav"]).unsqueeze(0)
    print(out["wav"].dtype)
    torchaudio.save(out_path, out["wav"], 22050)

    waveform, sample_rate = torchaudio.load(out_path)
    torchaudio.save("fixed_audio.wav", waveform, sample_rate)


    print(f"Ses dosyası oluşturuldu ve kaydedildi: {out_path}")
    return out_path

# Ana kod
if __name__ == "__main__":
    
    # Model dosyalarının yolları
    model_path = r"C:\Users\TOM\Documents\Projeler\Ses_fine_tune\xtts-finetune-webui\finetune_models\ready\model.pth"  # Model dosyanızın URL'si
    config_path = r"C:\Users\TOM\Documents\Projeler\Ses_fine_tune\xtts-finetune-webui\finetune_models\ready\config.json"
    vocab_path = r"C:\Users\TOM\Documents\Projeler\Ses_fine_tune\xtts-finetune-webui\finetune_models\ready\vocab.json"
    speaker_path = r"C:\Users\TOM\Documents\Projeler\Ses_fine_tune\xtts-finetune-webui\finetune_models\ready\speakers_xtts.pth"
    
    # Modeli yükle
    model = load_model(model_path, config_path, vocab_path, speaker_path)

    # TTS kullanarak ses oluştur
    input_text = "Merhaba, bu bir sesli metin dönüşümüdür."
    while True:
        input_text = input("Metni girini: ")
        lang = "tr"  # Türkçe
        speaker_audio = "./ugur_t.mp3"  # Konuşmacı örnek ses dosyası

        if not os.path.exists(speaker_audio):
            raise FileNotFoundError(f"Speaker audio file bulunamadı: {speaker_audio}")

        output_audio_path = run_tts(model, lang, input_text, speaker_audio)
        print(f"Ses dosyası oluşturuldu: {output_audio_path}")
