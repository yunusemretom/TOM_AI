# 🎙️ Sesli Transkripsiyon ve Anlık Çeviri Projesi

Bu proje, ses kaydı alarak transkript oluşturan, çeviri yapıp bu metni sesli okuyan bir Python uygulamasıdır. Üç temel bileşenden oluşur:

## 📂 Proje Dosyaları

### 1. `fasterWhisper_deneme.py` 🎤
Bu dosya, mikrofon ile ses kaydı yapıp anlık transkripsiyon sağlar.

- **Kullanılan Kütüphaneler**: `argparse`, `io`, `speech_recognition`, `faster_whisper`, `datetime`, `queue`, `time`, `tempfile`
- **Komut Satırı Argümanları**: 
    - Model, cihaz, enerji eşiği, kayıt zaman aşımı, ifade zaman aşımı, dil gibi parametreler alınır.
- **Ses Kaydı**: `speech_recognition` kullanılarak mikrofon aracılığıyla ses alınır, bir kuyrukta toplanır.
- **Transkripsiyon**: `WhisperModel` ile alınan ses metne dönüştürülür. Metin güncellenip saklanır.
- **Hata Yönetimi**: Olası hatalar yakalanıp konsola yazdırılır.

### 2. `anlik_ceviri.py` 🌍
Bu dosya, `fasterWhisper_deneme.py` ile alınan transkripti çevirir ve sesli olarak dinlemenizi sağlar.

- **Kullanılan Kütüphaneler**: `translatepy` ile Google Translate kullanılarak çeviri yapılır; `EdgeTTS_deneme` dosyasındaki `edge_run` fonksiyonu çağrılır.
- **Metin Güncelleme**: `update_text` fonksiyonu, gelen metni belirtilen dile çevirir ve çıktıyı döndürür.
- **Ana Fonksiyon**: `main` fonksiyonu, `sesanalizi` fonksiyonuyla transkripti alır ve boş olmayan metinleri çevirip seslendirir.
- **Sonsuz Döngü**: Program sürekli çalışarak metinleri alır, çevirir ve okur.

### 3. `EdgeTTS_deneme.py` 🔊
Bu dosya, metni sesli olarak okuyup bir dosyaya kaydeder.

- **Asenkron Fonksiyon**: `amain` fonksiyonu, belirtilen dildeki metni uygun sesi seçerek belirli bir dosyaya kaydeder.
- **Sesli Okuma**: `edge_run` fonksiyonu ile metin alınır, `amain` fonksiyonuna iletilir, ardından `pydub` ile ses dosyası oynatılır.
- **Sonsuz Döngü**: Kullanıcıdan sürekli olarak metin alır ve sesli okuma işlevini tekrar eder.

## 🧩 Genel İşleyiş
Bu üç dosya birlikte çalışarak, ses kaydı yapar, kaydı metne çevirir, çeviriyi yapıp sonucu sesli olarak okur. Kullanıcı, anlık transkripti dinleyip çeviri çıktısı alabilir.

## 🚀 Başlatma Talimatları
1. Python ve gerekli kütüphaneleri kurun.
2. `fasterWhisper_deneme.py` dosyasını çalıştırarak ses kaydı ve transkripsiyon işlemini başlatın.
3. `anlik_ceviri.py` dosyasını çalıştırarak çeviri ve sesli okuma işlemlerini başlatın.

## 💼 Kullanım Alanları
- Anlık sesli çeviri
- Dil öğrenme ve telaffuz geliştirme
- Sesli asistan projeleri

