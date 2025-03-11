import os  # İşletim sistemi ile ilgili işlemler için
import hashlib  # Metin hash'leme için
import asyncio  # Asenkron programlama için
import torch  # PyTorch kütüphanesi için
from TTS.api import TTS  # Text-to-Speech API'si için
from pydub import AudioSegment  # Ses dosyası işlemleri için
from pydub.playback import play  # Ses çalma işlemi için
from rich import print  # Zengin konsol çıktısı için
import warnings  # Uyarıları yönetmek için

warnings.filterwarnings("ignore", category=FutureWarning)  # Gelecek uyarılarını görmezden gel

device = "cuda" if torch.cuda.is_available() else "cpu"  # GPU varsa kullan, yoksa CPU kullan
print(f"Using device: {device}")  # Kullanılan cihazı yazdır

WAV_PACKAGE = ["./ugur_t.mp3"]  # Örnek ses dosyası
CACHE_DIR = "audio_cache"  # Önbellek dizini

tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False).to(device)  # TTS modelini yükle

os.makedirs(CACHE_DIR, exist_ok=True)  # Önbellek dizinini oluştur (varsa hata verme)

# Geçici dizini ayarlayın
os.environ['TMPDIR'] = 'C:/Users/TOM/Documents/Temp'  # Yazma iznine sahip olduğunuz bir dizine değiştirin

def get_cache_path(text, language):  # Önbellek dosya yolunu oluştur
    text_hash = hashlib.md5(f"{text}_{language}".encode()).hexdigest()  # Metin ve dil bilgisinden hash oluştur
    return os.path.join(CACHE_DIR, f"cache_{text_hash}.wav")  # Önbellek dosya yolunu döndür

async def generate_audio(text, language, cache_path):  # Ses dosyası oluştur
    tts.tts_to_file(text=text, speaker_wav=WAV_PACKAGE, language=language, file_path=cache_path,split_sentences=True,speed=1.3)  # TTS ile ses oluştur
    print(f"Ses üretimi tamamlandı ve {cache_path} dosyasına kaydedildi.")  # Bilgi mesajı yazdır

def play_audio(file_path):  # Ses dosyasını çal
    audio = AudioSegment.from_wav(file_path)  # Ses dosyasını yükle
    play(audio)  # Sesi çal

async def speak_async(text, language="tr"):  # Asenkron konuşma fonksiyonu
    cache_path = get_cache_path(text, language)  # Önbellek dosya yolunu al
    
    if not os.path.exists(cache_path):  # Eğer önbellekte yoksa
        print("Ses dosyası oluşturuluyor...")  # Bilgi mesajı yazdır
        await generate_audio(text, language, cache_path)  # Ses dosyası oluştur
    else:
        print("Önbellekten ses dosyası kullanılıyor.")  # Bilgi mesajı yazdır
    
    play_audio(cache_path)  # Ses dosyasını çal

def speak(text, language="tr"):  # Senkron konuşma fonksiyonu
    asyncio.run(speak_async(text, language))  # Asenkron fonksiyonu çalıştır

if __name__ == "__main__":  # Ana program
    while True:  # Sonsuz döngü
        a = input("Söylemek istediğiniz metni girin: ")  # Kullanıcıdan metin al
        text ="""Yağmur yağıyordu. Adı yağmur ormanları zaten. Hamakta yatıp onu seyretmek keyifliydi, her gün olsa bile. Bunu yaparken kahve içmekse harika. Tek kötülüğü bitene kadar elinde tutmalıydın. Bittikten sonra yan yana yatılabiliyordu cam kavanozla. Kahve fincanı olarak kullandığım bir kavanozdu bu ama bazen çorba da koyuyordum içine ve bazen siyah fasulye. Hamakta yemek güzel oluyordu. Bitince, içinde ne varsa artık, kolunu dışarı uzatıp yağmurda yıkayabiliyordun. Deterjan kullanmadığım için temiz oluyordu. Sadece bazen biraz yağ kalıyordu galiba. Kahvenin üstünde sırt üstü yüzüyordu yağ… Bazen ama…
        """  # Örnek metin
        speak(a)  # Kullanıcının girdiği metni seslendir
