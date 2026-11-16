import wave  # Ses dosyalarını işlemek için
import pyaudio  # Ses girişi ve çıkışı için
from vosk import KaldiRecognizer, Model  # Ses tanıma için
from Library.Hava_durum import hava, temp  # Hava durumu bilgisi için
from Library.arka_plan import background  # Arka plan işlemleri için
from Library.Haber import news  # Haber bilgisi için
from Library.klavye_yonet import *  # Klavye kontrolü için
import subprocess  # Sistem komutlarını çalıştırmak için
from fuzzywuzzy import fuzz  # Metin benzerliği için
from random import randint  # Rastgele sayı üretmek için

#sesi yazıya çevirmek için veri seti
from ses_klonlama import speak  # Konuşma sentezi için

model = Model("vosk-model-small-tr-0.3")  # Türkçe ses tanıma modeli
recognizer = KaldiRecognizer(model,16000)  # Ses tanıyıcı oluşturma


#mikrofon için gerekli ayaralar. Değiştirilmesi önerilmez!
FORMAT = pyaudio.paInt16  # Ses formatı
CHANNELS = 1  # Tek kanal (mono)
RATE = 16000  # Örnekleme hızı
CHUNK = 1024  # Her okumada alınacak örnek sayısı
WAVE_OUTPUT_FILENAME = "file.wav"  # Çıktı dosyası adı
 
#burada ses verisini alıyoruz
mic = pyaudio.PyAudio()  # PyAudio nesnesi oluşturma
stream = mic.open(format=FORMAT, channels=CHANNELS,
                rate=RATE, input=True,
                frames_per_buffer=CHUNK)  # Ses akışı başlatma

stream.start_stream()  # Ses akışını başlatma

#sesimizi kaydetmek ve göndermek için
def record():
    data = stream.read(4096)  # Ses verisini okuma
    if recognizer.AcceptWaveform(data):  # Ses verisini tanıma
        text = recognizer.Result()  # Tanıma sonucunu alma
        texty = text[14:-3]  # Sonucu düzenleme
        print(text[14:-3])  # Sonucu yazdırma
        if texty != "" :
            #responsive(texty)
            return texty  # Boş olmayan sonucu döndürme
        else:
            return record()  # Boşsa tekrar deneme

greetings = ["Merhaba! Nasıl yardımcı olabilirim?", 
                 "Selam! Ne yapmak istersin?", 
                 "Merhaba! Bir komut ver, ben de çalıştırayım."]  # Selamlama mesajları

commands = {  # Komutlar ve ilgili işlevler

    "not defteri aç": lambda: (speak("açılıyor"), subprocess.Popen(['notepad.exe'])),  # Not defteri açma
    "tarayıcı aç":  lambda: (speak("açılıyor"),subprocess.Popen(["chrome.exe"])),  # Tarayıcı açma
    "sesi arttır":  lambda: (speak("ses azaltılıyor"), ses_ac()),  # Ses seviyesini arttırma
    "sesi azalt":  lambda: (speak("ses azaltılıyor"),ses_kis()),  # Ses seviyesini azaltma
    "sesini değiştir":  lambda: speak("Değiştiriliyor"),  # Ses değiştirme bildirimi
    "nasılsın":  lambda: speak((greetings[randint(0, len(greetings) - 1)]),),  # Rastgele selamlama
    "görüşürüz":  lambda: (speak("Görüşmek Üzere"), exit()),  # Programdan çıkış
    "son dakika haberleri": lambda: speak(news),  # Haber okuma
    "merhaba tom":  lambda: speak("Merhabalar efendim"),  # Selamlama yanıtı
    "saat kaç":  lambda: speak("açılıyor"),  # Saat bilgisi (henüz uygulanmamış)
    "değiştir şarkıyı":  lambda: (speak("değiştiriliyor"), sonraki_sarki()),  # Şarkı değiştirme
    "arama yap":  lambda: speak("yapılıyor"),  # Arama yapma bildirimi
    "parlaklığı arttır":  lambda: (speak("arttırılıyor")),  # Parlaklık arttırma bildirimi
    "parlaklığı azalt":  lambda: speak("azaltılıyor"),  # Parlaklık azaltma bildirimi
    "arka planı kapat":  lambda: speak("kapatılıyor")  # Arka plan kapatma bildirimi

}

# Belirli bir eşiğe göre komutları karşılaştır
def handle_command(command):
    best_match = None  # En iyi eşleşme
    highest_score = 0  # En yüksek benzerlik skoru

    for key in commands:
        score = fuzz.partial_ratio(key, command)  # Anahtar kelime ile komutun eşleşme oranını hesapla
        if score > highest_score:
            highest_score = score
            best_match = key

    # Eşleşme belirli bir eşik üzerindeyse (örneğin %70), komutu çalıştır
    if highest_score >= 60:
        commands[best_match]()  # İlgili fonksiyonu çağır
        return True
    return False

while True:
    handle_command(record())  # Sürekli olarak komutları dinleme ve işleme