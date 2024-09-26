import subprocess
from fuzzywuzzy import fuzz

# Komutlar ve fonksiyonlar
def open_notepad():
    subprocess.Popen(['notepad.exe'])

def open_browser():
    subprocess.Popen(['C:/Program Files/Google/Chrome/Application/chrome.exe'])

commands = {
    "not defteri aç": open_notepad,
    "tarayıcı aç": open_browser
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
    if highest_score >= 70:
        commands[best_match]()  # İlgili fonksiyonu çağır
        return True
    return False

# Komutları sesli simüle etmek için loop
while True:
    command = input("Komut: ")  # Sesli komutu burada 'input' ile simüle ediyoruz
    if not handle_command(command):
        print("Komut anlaşılamadı.")
