
#sesi yazıya çevirmek için veri seti
from ses_klonlama_1_01 import speak  # Konuşma sentezi için speak fonksiyonunu içe aktar
from whisper_deneme_1_01 import transcript  # Ses tanıma için transcript fonksiyonunu içe aktar

from Library.Hava_durum import hava, temp  # Hava durumu bilgilerini almak için fonksiyonları içe aktar
from Library.arka_plan import background  # Arka plan işlemleri için background fonksiyonunu içe aktar
from Library.Haber import news  # Haber bilgilerini almak için news fonksiyonunu içe aktar
from Library.klavye_yonet import *  # Klavye yönetimi için tüm fonksiyonları içe aktar
import subprocess  # Sistem komutlarını çalıştırmak için subprocess modülünü içe aktar
from fuzzywuzzy import fuzz  # Metin benzerliği için fuzz modülünü içe aktar
from random import choice  # Rastgele seçim yapmak için choice fonksiyonunu içe aktar

import ollama  # Ollama AI modelini kullanmak için ollama modülünü içe aktar
from rich_deneme import print  # Zengin metin çıktısı için özel print fonksiyonunu içe aktar

class Agent:  # AI ajanını temsil eden sınıf
    def __init__(self, role, model="llama3.1"):  # Sınıfın yapıcı metodu
        self.role = role  # Ajanın rolünü ayarla
        self.model = model  # Kullanılacak AI modelini ayarla
        self.ollama_client = ollama.Client()  # Ollama istemcisini oluştur

    def generate(self, prompt):  # Metin üretmek için metot
        return self.ollama_client.generate(prompt=prompt, system=self.role, model=self.model, stream=False)["response"]  # Ollama ile metin üret ve yanıtı döndür

Naz = Agent(role="Adın Naz.")  # Naz adında bir AI ajanı oluştur

greetings = ["Merhaba! Nasıl yardımcı olabilirim?",  # Selamlama mesajları listesi
             "Selam! Ne yapmak istersin?", 
             "Merhaba! Bir komut ver, ben de çalıştırayım."]

commands = {  # Komutlar ve ilgili işlevler sözlüğü
    "not defteri aç": lambda: (speak("açılıyor"), subprocess.Popen(['notepad.exe'])),  # Not defterini aç
    "tarayıcı aç": lambda: (speak("açılıyor"), subprocess.Popen(["chrome.exe"])),  # Tarayıcıyı aç
    "sesi arttır": lambda: (speak("ses arttırılıyor"), ses_ac()),  # Ses seviyesini arttır
    "sesi azalt": lambda: (speak("ses azaltılıyor"), ses_kis()),  # Ses seviyesini azalt
    "sesini değiştir": lambda: speak("Değiştiriliyor"),  # Ses değiştirme bildirimi
    "nasılsın": lambda: speak(choice(greetings)),  # Rastgele bir selamlama mesajı seç ve söyle
    "görüşürüz": lambda: (speak("Görüşmek Üzere"), exit()),  # Programdan çık
    "son dakika haberleri": lambda: speak(news),  # Son dakika haberlerini oku
    "merhaba tom": lambda: speak("Merhabalar efendim"),  # Selamlama yanıtı
    "saat kaç": lambda: speak("açılıyor"),  # Saat bilgisi (henüz uygulanmamış)
    "değiştir şarkıyı": lambda: (speak("değiştiriliyor"), sonraki_sarki()),  # Şarkıyı değiştir
    "arama yap": lambda: speak("yapılıyor"),  # Arama yapma bildirimi
    "parlaklığı arttır": lambda: speak("arttırılıyor"),  # Parlaklık arttırma bildirimi
    "parlaklığı azalt": lambda: speak("azaltılıyor"),  # Parlaklık azaltma bildirimi
    "arka planı kapat": lambda: speak("kapatılıyor")  # Arka plan kapatma bildirimi
}

def handle_command(command):  # Komutları işleyen fonksiyon
    best_match = max(commands.keys(), key=lambda k: fuzz.partial_ratio(k, command))  # En iyi eşleşen komutu bul
    if fuzz.partial_ratio(best_match, command) >= 60:  # Eşleşme oranı %60'tan fazlaysa
        commands[best_match]()  # Komutu çalıştır
        return True
    return False

print("Başlıyoruz...")  # Başlangıç mesajını yazdır
speak("Merhaba ben Naz. Sana nasıl yardımcı olabilirim?")  # Karşılama mesajını seslendir

while True:  # Sonsuz döngü
    sonuc = transcript()  # Ses girişini metne çevir
    if sonuc:  # Eğer bir sonuç varsa
        print(sonuc, color="purple")  # Sonucu mor renkte yazdır
        print("loading...")  # Yükleniyor mesajını yazdır
        Nazdan_cevap = Naz.generate(sonuc)  # AI'dan yanıt al
        print(Nazdan_cevap, color="cyan")  # AI yanıtını cyan renkte yazdır
        speak(Nazdan_cevap)  # AI yanıtını seslendir
    #handle_command(sonuc)  # Komutu işle (şu an yorum satırında)