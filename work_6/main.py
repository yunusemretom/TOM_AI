from translatepy.translators.google import GoogleTranslate
import fasterWhisper_deneme as stt
import ses_klonlama_2_00 as tts
from play_soundfile_deneme import start_sound
import os
from time import sleep
import torch
import gc

# Çeviri için singleton nesne
translator = GoogleTranslate()

def ceviri_yap(metin, hedef_dil='en'):
    """Metni hedef dile çevirir"""
    try:
        return str(translator.translate(metin, hedef_dil))
    except Exception as e:
        print(f"Çeviri hatası: {str(e)}")
        return None

# Model dosya yolları
model_path = r"C:\Users\TOM\Documents\Projeler\Ses_fine_tune\xtts-finetune-webui\finetune_models\ready\model.pth"
config_path = r"C:\Users\TOM\Documents\Projeler\Ses_fine_tune\xtts-finetune-webui\finetune_models\ready\config.json"
vocab_path = r"C:\Users\TOM\Documents\Projeler\Ses_fine_tune\xtts-finetune-webui\finetune_models\ready\vocab.json"
speaker_path = r"C:\Users\TOM\Documents\Projeler\Ses_fine_tune\xtts-finetune-webui\finetune_models\ready\speakers_xtts.pth"

# Model ve konuşmacı ses dosyası yükleme
model = tts.load_model(model_path, config_path, vocab_path, speaker_path)
speaker_audio = "./ugur_t.mp3"

if not os.path.exists(speaker_audio):
    raise FileNotFoundError(f"Speaker audio file bulunamadı: {speaker_audio}")

def clear_gpu_memory():
    """GPU belleğini temizler"""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        gc.collect()

def process_text(text):
    """Metni çevirip sese dönüştürür"""
    translated = ceviri_yap(text)  # Metni çevir
    if translated:
        sentences = [s.strip() for s in translated.split('.') if s.strip()]  # Cümlelere ayır
        for sentence in sentences:
            output_path = tts.run_tts(model, "en", sentence, speaker_audio)  # Ses oluştur
            #if output_path:
                #start_sound(output_path)  # Sesi çal
        clear_gpu_memory()  # Belleği temizle

if __name__ == "__main__":
    transcriber = stt.AudioTranscriber()  # Ses tanıma başlat
    print("Sistem hazır, dinlemeye başlıyorum...")
    
    processed_texts = set()  # İşlenmiş metinleri tut
    last_text = None
    
    while True:
        try:
            result = transcriber.process_audio()  # Sesi dinle
            if result and result[-1] != last_text:  # Yeni metin kontrolü
                last_text = result[-1]
                
                if last_text not in processed_texts:  # Tekrar kontrolü
                    print(f"Algılanan metin: {last_text}")
                    processed_texts.add(last_text)
                    
                    if len(processed_texts) > 10:  # Son 50 metni tut
                        processed_texts.clear()
                    
                    process_text(last_text)  # Metni işle
                
            sleep(0.05)  # CPU yükünü azalt
            
        except KeyboardInterrupt:
            print("\nProgram sonlandırılıyor...")
            break
        except Exception as e:
            print(f"Hata oluştu: {e}")
            continue
