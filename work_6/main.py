from translatepy.translators.google import GoogleTranslate
import fasterWhisper_deneme as stt
import ses_klonlama_2_00 as tts
import os
from time import sleep
from play_soundfile_deneme import play_sound, start_sound
import threading
import torch
import gc
import pygame

def ceviri_yap(metin, hedef_dil='en'):
    """
    Verilen metni hedef dile çevirir
    
    Parametreler:
    metin (str): Çevrilecek metin
    hedef_dil (str): Hedef dilin kodu (örn: 'en' for English, 'tr' for Turkish)
    """
    try:
        # Google Translate nesnesini singleton olarak kullan
        if not hasattr(ceviri_yap, 'cevirmen'):
            ceviri_yap.cevirmen = GoogleTranslate()
        
        # Çeviriyi yap
        ceviri = ceviri_yap.cevirmen.translate(metin, hedef_dil)
        return str(ceviri)
    except Exception as e:
        print(f"Çeviri hatası: {str(e)}")
        return None

# Model dosyalarının yolları
model_path = r"C:\Users\TOM\Documents\Projeler\Ses_fine_tune\xtts-finetune-webui\finetune_models\ready\model.pth"
config_path = r"C:\Users\TOM\Documents\Projeler\Ses_fine_tune\xtts-finetune-webui\finetune_models\ready\config.json"
vocab_path = r"C:\Users\TOM\Documents\Projeler\Ses_fine_tune\xtts-finetune-webui\finetune_models\ready\vocab.json"
speaker_path = r"C:\Users\TOM\Documents\Projeler\Ses_fine_tune\xtts-finetune-webui\finetune_models\ready\speakers_xtts.pth"

# Modeli yükle
model = tts.load_model(model_path, config_path, vocab_path, speaker_path)
lang = "en"
speaker_audio = "./ugur_t.mp3"

if not os.path.exists(speaker_audio):
    raise FileNotFoundError(f"Speaker audio file bulunamadı: {speaker_audio}")

def clear_gpu_memory():
    """CUDA belleğini temizle"""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        gc.collect()

def process_text(text):
    """Metni çevir ve sese dönüştür"""
    translated = ceviri_yap(text)
    if translated:
        # Metni noktalara göre böl
        sentences = translated.split('.')
        # Boş cümleleri filtrele
        sentences = [s.strip() for s in sentences if s.strip()]
        
        for sentence in sentences:
            output_path = tts.run_tts(model, lang, sentence, speaker_audio)
            if output_path:
                # Her cümleyi sırayla çal ve bitene kadar bekle
                play_sound(output_path)  # Ses bitene kadar bekler
        
        clear_gpu_memory()  # İşlem sonrası belleği temizle

if __name__ == "__main__":
    pygame.mixer.init()  # Pygame mixer'ı başlat
    transcriber = stt.AudioTranscriber()
    print("Sistem hazır, dinlemeye başlıyorum...")
    
    processed_texts = set()  # İşlenmiş metinleri takip et
    last_text = None
    memory_clear_counter = 0
    
    while True:
        try:
            result = transcriber.process_audio()
            if result and result[-1] != last_text:  # Tekrar eden metinleri önle
                last_text = result[-1]
                
                # Eğer metin daha önce işlenmediyse işle
                if last_text not in processed_texts:
                    print(f"Algılanan metin: {last_text}")
                    processed_texts.add(last_text)
                    
                    # Set'in boyutunu kontrol et
                    if len(processed_texts) > 100:  # Son 100 metni tut
                        processed_texts.clear()
                    
                    # Metni işle ve ses oluştur
                    process_text(last_text)
                
            sleep(0.05)  # CPU kullanımını azalt
            
            # Her 100 döngüde bir belleği temizle
            memory_clear_counter += 1
            if memory_clear_counter >= 100:
                clear_gpu_memory()
                memory_clear_counter = 0
            
        except KeyboardInterrupt:
            print("\nProgram sonlandırılıyor...")
            break
        except Exception as e:
            print(f"Hata oluştu: {e}")
            continue
