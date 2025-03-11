import asyncio
from ollama import Client
import fasterWhisper_deneme as stt
import ses_klonlama_2_00 as tts
from play_soundfile_deneme import start_sound
import os
import warnings
from fuzzywuzzy import fuzz
import re
import torch
import gc
warnings.filterwarnings("ignore", category=FutureWarning)

# CUDA ayarları ve optimizasyonları
def setup_cuda():
    if torch.cuda.is_available():
        torch.backends.cudnn.benchmark = True
        torch.backends.cudnn.deterministic = False
        # Otomatik bellek yönetimi
        torch.cuda.empty_cache()
        # Varsayılan CUDA cihazını ayarla
        torch.cuda.set_device(0)
        return True
    return False

# Bellek temizleme fonksiyonu
def clear_gpu_memory():
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        gc.collect()

# Komutların bir sözlükte tanımlanması
COMMANDS = {
    "Işıkları açar mısın": "turn_on_light()",
    "Müzik çalar mısın": "play_music()",
    "Kapıları açar mısın": "open_doors()",
}

# Komut fonksiyonları simülasyonu
def turn_on_light():
    print("Işıklar açıldı.")
    ses_olustur("Açıldı")
def play_music():
    print("Müzik çaldı.")

def open_doors():
    print("Kapılar açıldı.")

# Noktalama işaretlerine göre cümleyi parçalara ayıran fonksiyon
def split_sentence(sentence):
    return re.split(r'([?.!])', sentence)

# Komutları çıkaran ve geriye kalan metni LLM modeline gönderen işlem
def process_input(input_text, commands):
    parts = split_sentence(input_text)
    best_match_score = 65
    best_command = ""
    command_text = ""
    
    for part in parts:
        if not part.strip():
            continue
        for key in commands:
            score = fuzz.ratio(part.lower(), key.lower())
            if score > best_match_score:
                best_match_score = score
                best_command = key
                command_text = part
    
    if best_match_score > 65:
        input_text = input_text.replace(command_text, "").strip()
        exec(commands[best_command])
    
    return input_text

# Model yollarını global olarak tanımla
model_path = r"C:\Users\TOM\Documents\Projeler\Ses_fine_tune\xtts-finetune-webui\finetune_models\ready\model.pth"
config_path = r"C:\Users\TOM\Documents\Projeler\Ses_fine_tune\xtts-finetune-webui\finetune_models\ready\config.json" 
vocab_path = r"C:\Users\TOM\Documents\Projeler\Ses_fine_tune\xtts-finetune-webui\finetune_models\ready\vocab.json"
speaker_path = r"C:\Users\TOM\Documents\Projeler\Ses_fine_tune\xtts-finetune-webui\finetune_models\ready\speakers_xtts.pth"
speaker_audio = "./ugur_t.mp3"

# CUDA kurulumunu yap
has_cuda = setup_cuda()

# Modeli başlangıçta yükle
model = tts.load_model(model_path, config_path, vocab_path, speaker_path)

def ses_olustur(text):
    if not text:
        return
        
    if not os.path.exists(speaker_audio):
        raise FileNotFoundError(f"Speaker audio file bulunamadı: {speaker_audio}")

    # GPU belleğini temizle
    if has_cuda:
        clear_gpu_memory()

    output_audio_path = tts.run_tts(model, "tr", text, speaker_audio)
    start_sound(output_audio_path)

def chat(content):
    client = Client(host='http://localhost:11434')
    # GPU kullanımını optimize et
    gpu_count = 1 if has_cuda else 0
    response = client.chat(
        model='llama3.1',
        messages=[{'role': 'user', 'content': content}],
        options={
            'num_gpu': gpu_count,
            'num_thread': os.cpu_count(),  # CPU thread sayısını optimize et
            'batch_size': 8 if has_cuda else 4  # GPU varsa batch size'ı artır
        }
    )
    return response.message['content']

# Transcriber'ı CUDA ile başlat
transcriber = stt.AudioTranscriber(use_cuda=has_cuda)
print("Model hazır, dinlemeye başlıyor...")

Kontrol = False

while True:
    try:
        # Periyodik bellek temizliği
        if has_cuda and gc.get_count()[0] > 1000:
            clear_gpu_memory()
            
        metin = transcriber.process_audio()
        
        if metin and len(metin) > 0:
            son_metin = metin[-1]
            if "Ada" in son_metin:
                Kontrol = True
    
            if Kontrol:    
                if "..." in son_metin:
                    continue
                print("Gelen veri:", son_metin)
                
                processed_text = process_input(son_metin, COMMANDS)
                if processed_text:
                    print("processed_text:",processed_text)
                    response = chat(processed_text)
                    print("Gelen yanıt:", response)
                    ses_olustur(response)
                if "görüşürüz" in son_metin:
                    Kontrol=False
                    # Oturum sonunda belleği temizle
                    if has_cuda:
                        clear_gpu_memory()
    
    except Exception as e:
        print(f"Hata: {e}")
        # Hata durumunda belleği temizle
        if has_cuda:
            clear_gpu_memory()
