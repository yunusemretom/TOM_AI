import pyttsx3  # Text-to-speech kütüphanesini içe aktar

engine = pyttsx3.init()  # TTS motorunu başlat
engine.setProperty('rate', 150)  # Konuşma hızını ayarla
voices = engine.getProperty('voices')  # Mevcut sesleri al
engine.setProperty('voice', voices[3].id)  # Belirli bir sesi seç
engine.say("Bu bir deneme metnidir.")  # Metni seslendir
engine.runAndWait()  # Seslendirmeyi çalıştır ve tamamlanmasını bekle