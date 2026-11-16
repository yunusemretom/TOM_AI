import subprocess  # Sistem komutlarını çalıştırmak için
from fuzzywuzzy import fuzz  # Metin benzerliği için

# Komutlar ve fonksiyonlar
def open_notepad():  # Not defteri açma fonksiyonu
    subprocess.Popen(['notepad.exe'])  # Not defterini aç

def open_browser():  # Tarayıcı açma fonksiyonu
    subprocess.Popen(['chrome.exe'])  # Chrome'u aç

commands = {  # Komutlar ve ilgili işlevler sözlüğü

    "not defteri aç": lambda: (speak("açılıyor"), subprocess.Popen(['notepad.exe'])),  # Not defterini aç
    "tarayıcı aç":  lambda: (speak("açılıyor"),subprocess.Popen(["chrome.exe"])),  # Tarayıcıyı aç
    "sesi arttır":  lambda: (speak("ses azaltılıyor"), ses_ac()),  # Sesi arttır
    "sesi azalt":  lambda: (speak("ses azaltılıyor"),ses_kis()),  # Sesi azalt
    "sesini değiştir":  lambda: speak("Değiştiriliyor"),  # Ses değiştirme bildirimi
    "nasılsın":  lambda: speak((greetings[randint(0, len(greetings) - 1)]),),  # Rastgele selamlama
    "görüşürüz":  lambda: (speak("Görüşmek Üzere"), exit()),  # Programdan çık
    "son dakika haberleri": lambda: speak(news),  # Haberleri oku
    "merhaba tom":  lambda: speak("Merhabalar efendim"),  # Selamlama yanıtı
    "saat kaç":  lambda: speak("açılıyor"),  # Saat bilgisi (henüz uygulanmamış)
    "değiştir şarkıyı":  lambda: (speak("değiştiriliyor"), sonraki_sarki()),  # Şarkıyı değiştir
    "arama yap":  lambda: speak("yapılıyor"),  # Arama yapma bildirimi
    "parlaklığı arttır":  lambda: (speak("arttırılıyor")),  # Parlaklık arttırma bildirimi
    "parlaklığı azalt":  lambda: speak("azaltılıyor"),  # Parlaklık azaltma bildirimi
    "arka planı kapat":  lambda: speak("kapatılıyor")  # Arka plan kapatma bildirimi

}

# Belirli bir eşiğe göre komutları karşılaştır
def handle_command(command):  # Komut işleme fonksiyonu
    best_match = None  # En iyi eşleşme
    highest_score = 0  # En yüksek skor

    for key in commands:  # Tüm komutları döngüyle kontrol et
        score = fuzz.partial_ratio(key, command)  # Anahtar kelime ile komutun eşleşme oranını hesapla
        if score > highest_score:  # Eğer yeni skor daha yüksekse
            highest_score = score  # En yüksek skoru güncelle
            best_match = key  # En iyi eşleşmeyi güncelle

    # Eşleşme belirli bir eşik üzerindeyse (örneğin %70), komutu çalıştır
    print(highest_score)  # Eşleşme skorunu yazdır
    if highest_score >= 50:  # Eğer skor 50'den büyük veya eşitse
        print(best_match)  # En iyi eşleşen komutu yazdır
        commands[best_match]()  # İlgili fonksiyonu çağır
        return True  # Başarılı işlem
    return False  # Başarısız işlem


while True:  # Sonsuz döngü
    command = input("Komut: ")  # Kullanıcıdan komut al
    if not handle_command(command):  # Eğer komut işlenemediyse
        print("Komut anlaşılamadı.")  # Hata mesajı yazdır
    else:
        print("Komut işlendi.")  # Başarılı işlem mesajı yazdır
        # Komutu işle ve sonucunu kontrol et
        handle_command(command)