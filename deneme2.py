import subprocess
from fuzzywuzzy import fuzz

# Komutlar ve fonksiyonlar
def open_notepad():
    subprocess.Popen(['notepad.exe'])

def open_browser():
    subprocess.Popen(['chrome.exe'])

commands = {

    "not defteri aç": lambda: (speak("açılıyor"), subprocess.Popen(['notepad.exe'])),
    "tarayıcı aç":  lambda: (speak("açılıyor"),subprocess.Popen(["chrome.exe"])),
    "sesi arttır":  lambda: (speak("ses azaltılıyor"), ses_ac()),
    "sesi azalt":  lambda: (speak("ses azaltılıyor"),ses_kis()),
    "sesini değiştir":  lambda: speak("Değiştiriliyor"),
    "nasılsın":  lambda: speak((greetings[randint(0, len(greetings) - 1)]),),
    "görüşürüz":  lambda: (speak("Görüşmek Üzere"), exit()),
    "son dakika haberleri": lambda: speak(news),
    "merhaba tom":  lambda: speak("Merhabalar efendim"),
    "saat kaç":  lambda: speak("açılıyor"),
    "değiştir şarkıyı":  lambda: (speak("değiştiriliyor"), sonraki_sarki()),
    "arama yap":  lambda: speak("yapılıyor"),
    "parlaklığı arttır":  lambda: (speak("arttırılıyor")),
    "parlaklığı azalt":  lambda: speak("azaltılıyor"),
    "arka planı kapat":  lambda: speak("kapatılıyor")

}

# Belirli bir eşiğe göre komutları karşılaştır
def handle_command(command):
    best_match = None
    highest_score = 0

    for key in commands:
        score = fuzz.partial_ratio(key, command)  # Anahtar kelime ile komutun eşleşme oranını hesapla
        if score > highest_score:
            highest_score = score
            best_match = key

    # Eşleşme belirli bir eşik üzerindeyse (örneğin %70), komutu çalıştır
    print(highest_score)
    if highest_score >= 50:
        print(best_match)
        commands[best_match]()  # İlgili fonksiyonu çağır
        return True
    return False

# Komutları sesli simüle etmek için loop
while True:
    command = input("Komut: ")  # Sesli komutu burada 'input' ile simüle ediyoruz
    if not handle_command(command):
        print("Komut anlaşılamadı.")
