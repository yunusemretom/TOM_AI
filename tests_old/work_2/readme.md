
# 🗣️ Sesli Komutlarla Çalışan Yapay Zeka Destekli Asistan

Bu proje, sesli komutlarla çalışan, yapay zeka destekli bir sesli asistan geliştirme sürecini ele alır. Kullanıcı sesini metne çevirir, AI modeliyle etkileşime geçer ve ardından sesi geri bildirir. 🤖 Ses tanıma, yapay zeka, ses sentezi ve sistem etkileşimi gibi farklı teknolojileri bir araya getirir.

---

## 📂 Proje Dosyaları

### 1. `work_2/whisper_main_deneme_1_01.py`

Bu dosya, asistanın temel işlemlerini yürüten ana dosyadır. Özellikleri:

- **Yapay Zeka:** Ollama adlı bir AI modeli kullanır. Bu model, **Naz** adı verilen bir AI ajanı olarak yapılandırılmıştır.
- **İşlem Fonksiyonları:** Not defteri açma, tarayıcıyı başlatma, ses ayarlarını yapma gibi çeşitli sistem komutlarını yürütür.
- **Ana Döngü:** Sürekli olarak kullanıcıdan komut alır, AI'ye iletir, sonuç döner ve gerekirse bir eylemi yerine getirir. 

Bu dosya, tüm sistemi yöneten merkezi bir yapıdır. 🎛️

---

### 2. `work_2/whisper_deneme_1_01.py`

Ses kaydı ve transkripsiyon için tasarlanmış bu dosya, konuşma tanıma işlevselliğinin temelini oluşturur:

- **Ses Kütüphaneleri:** `pyaudio`, `numpy`, `whisper` gibi kütüphaneleri kullanır.
- **Kayıt ve Dönüştürme:** Mikrofonu dinleyerek ses kaydı yapar ve Whisper modelini kullanarak kaydedilen sesi metne çevirir.
- **Ana İşleyiş:** Kullanıcıdan gelen sesi kaydeder, transkribe eder ve sonucu yazdırır.

Bu dosya, kullanıcının sesini yakalayıp metne dönüştürerek sistemin diğer bileşenlerine hazırlar. 🎙️

---

### 3. `work_2/ses_klonlama_1_01.py`

Bu dosya, metni sese dönüştürme (TTS) işlevselliğini sağlar:

- **Ses Klonlama:** `TTS` API'si kullanılarak metin sese çevrilir.
- **İşlem Hızı:** GPU varsa onu kullanarak hızlı işlem yapar, yoksa CPU ile devam eder.
- **Önbellekleme:** Aynı metin tekrarlanmak istendiğinde, yeniden ses sentezi yapmak yerine önceden oluşturulan ses dosyasını kullanır.
- **Senkron/Asenkron İşlem:** `speak_async` ve `speak` fonksiyonları, sesi çevirir ve çalar.

Bu dosya sayesinde, AI yanıtlarını sesli olarak iletir ve kullanıcının geri bildirim almasını sağlar. 🔊

---

## 🛠️ Proje Akışı

Bu sistem, aşağıdaki adımlarla çalışır:

1. **Ses Komutu:** Kullanıcı bir ses komutu verir.
2. **Transkripsiyon:** `whisper_deneme_1_01.py` ile komut metne çevrilir.
3. **AI Yanıtı:** `whisper_main_deneme_1_01.py` dosyası metni AI modeline gönderir ve bir cevap alır.
4. **Eylem:** AI’nın yanıtına göre sistem gerekirse bir işlem yapar.
5. **Geri Bildirim:** `ses_klonlama_1_01.py` kullanılarak AI cevabı sesli olarak kullanıcıya iletilir.

Bu yapıyla, kullanıcıyla doğal bir etkileşim sağlanır. 💡

playback delete false