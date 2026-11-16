import subprocess  # Sistem komutlarını çalıştırmak için subprocess modülü
from ses_klonlama_1_01 import speak  # Konuşma sentezi için speak fonksiyonu
import ollama

# Ollama istemcisini başlat
ollama_client = ollama.Client()

# Ollama'nın karar vermesini istediğimiz sınıf
class Agent:
    def __init__(self, role, model="llama3.1"):
        self.role = role
        self.model = model

    def generate(self, prompt):
        # Ollama ile metin üret ve sonucu döndür
        return ollama_client.generate(prompt=prompt, system=self.role, model=self.model, stream=False)["response"]

# Naz isimli bir AI ajanı oluştur
Naz = Agent(role="Adın Naz. Sen bir yardımcı AI'sın. Komutları al ve hangi işlemi yapmam gerektiğini söyle.")

# Ollama tarafından verilen cevaba göre işlem yapan fonksiyonlar
def open_notepad():
    speak("Not defteri açılıyor.")
    subprocess.Popen(['notepad.exe'])

def open_browser():
    speak("Tarayıcı açılıyor.")
    subprocess.Popen(["chrome.exe"])

def volume_up():
    speak("Ses arttırılıyor.")
    # Buraya sesi arttıran kod eklenebilir

def volume_down():
    speak("Ses kısılıyor.")
    # Buraya sesi kısan kod eklenebilir

# Bir sözlüğe, Ollama'nın kararına göre yapılacak işlemleri tanımla
actions = {
    "not defteri aç": open_notepad,
    "tarayıcı aç": open_browser,
    "sesi arttır": volume_up,
    "sesi kıs": volume_down,
    # Buraya daha fazla komut ekleyebilirsin
}

def perform_action(ollama_response):
    """
    Ollama'nın verdiği cevaba göre uygun işlemi yap
    """
    for command, action in actions.items():
        if command in ollama_response.lower():
            action()  # İlgili işlemi çalıştır
            return True
    return False

# Sonsuz döngü içinde komutları dinle
while True:
    sonuc = input("Komut girin: ")  # Kullanıcının sesini metne çevir
    if sonuc:
        print(f"Kullanıcı komutu: {sonuc}")
        speak("Komut alındı, işleniyor...")
        
        # Ollama'ya komutu gönder
        ollama_response = Naz.generate(sonuc)
        print(f"Ollama cevabı: {ollama_response}")
        speak(ollama_response)
        
        # Ollama'nın verdiği cevaba göre aksiyon gerçekleştir
        if not perform_action(ollama_response):
            speak("Bu komutu anlayamadım, lütfen tekrar deneyin.")
        # Eğer perform_action() fonksiyonu False döndürürse, yani tanımlı bir komut bulunamazsa,
        # kullanıcıya anlaşılamadığını belirten bir mesaj verilir.
