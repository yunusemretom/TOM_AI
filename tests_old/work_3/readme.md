
# 🎙️ FasterWhisper Gerçek Zamanlı Ses Tanıma Uygulaması

Bu proje, Python kullanılarak oluşturulmuş ve **Faster Whisper** modeli ile çalışan, gerçek zamanlı ses tanıma ve transkripsiyon uygulamasıdır. **fasterWhisper_deneme.py** dosyası, ses verisini anlık olarak kaydeder, işler ve hızlı bir şekilde metne dönüştürür. Proje, konuşma tabanlı komut sistemleri ve canlı altyazı uygulamaları gibi gerçek zamanlı senaryolar için ideal bir altyapı sağlar.

## 📋 İçerik

1. [Kütüphane ve Bağımlılıklar](#-kütüphane-ve-bağımlılıklar)
2. [Kurulum](#-kurulum)
3. [Dosya Bileşenleri ve Detaylı Açıklamalar](#-dosya-bileşenleri-ve-detaylı-açıklamalar)
4. [Özellikler](#-özellikler)
5. [Kullanım](#-kullanım)
6. [Geliştirme Notları](#-geliştirme-notları)

---

## 📚 Kütüphane ve Bağımlılıklar

Bu proje, aşağıdaki ana kütüphaneleri kullanmaktadır:
- **argparse**: Komut satırı argümanlarını ayrıştırmak için.
- **speech_recognition**: Mikrofon ve ses tanıma yönetimi için.
- **faster_whisper**: Whisper modelinin hızlı versiyonu ile sesin metne dönüştürülmesi için.
- **queue, datetime, tempfile, io**: Ses işleme ve kuyruk yönetimi için yardımcı kütüphaneler.

---

## 🛠️ Kurulum

Bu projeyi kullanmak için, aşağıdaki adımları izleyebilirsiniz:

1. Gerekli Python bağımlılıklarını yükleyin:
   ```bash
   pip install argparse speech_recognition faster_whisper datetime queue tempfile
   ```

2. **Faster Whisper** modelini indirin ve sisteminize kurun. Model boyutları dosya içinde ayarlanabilir.

---

## 📂 Dosya Bileşenleri ve Detaylı Açıklamalar

### 1. `work_3/fasterWhisper_deneme.py`

Bu dosya, gerçek zamanlı ses tanıma ve transkripsiyon işlemlerinin ana dosyasıdır. İşte ana bileşenlerin detaylı açıklamaları:

- **Kütüphane İmportları**  
  Ses tanıma, zaman işleme, kuyruk yönetimi ve geçici dosya oluşturma için çeşitli kütüphaneler projeye dahil edilmiştir:
  ```python
  import argparse, io, speech_recognition as sr, ...
  ```

- **Argüman Ayrıştırma**  
  `argparse` kullanılarak, model boyutu, cihaz tipi, enerji eşiği ve kayıt zaman aşımı gibi parametreler komut satırından ayarlanabilir.
  
- **Ana Bileşenler**  
  Ses tanıma bileşenleri ve değişkenleri oluşturulur. Örneğin:
  ```python
  data_queue = Queue()
  recorder = sr.Recognizer()
  ```

- **Ses Kaydı Callback Fonksiyonu**  
  Mikrofon ses algıladığında çalışır ve veriyi bir kuyruğa ekler.
  
- **Ana İşlem Döngüsü**  
  Ses verisini işleyerek, Faster Whisper modeli ile metne dönüştürür ve çıktıyı sağlar.

- **Program Başlatma**  
  Uygulama sürekli çalışarak, her an gelen sesleri işlemek üzere bekler.

---

## ✨ Özellikler

- **Gerçek Zamanlı Ses Tanıma:** Mikrofon üzerinden sürekli ses dinleme ve anında metne dönüştürme.
- **Faster Whisper Modeli:** Hızlı ve doğruluğu yüksek bir ses tanıma deneyimi sağlar.
- **Kullanıcı Ayarları:** Enerji eşiği, kayıt zaman aşımı ve cihaz gibi parametreler komut satırından ayarlanabilir.

---

## 🚀 Kullanım

Projeyi çalıştırmak için şu komutu kullanın:

```bash
python fasterWhisper_deneme.py --model-size medium --device cuda
```

### Argümanlar

- `--model-size`: Kullanılacak modelin boyutunu ayarlar (`small`, `medium`, `large` vb.)
- `--device`: İşlemci tipi (`cpu` veya `cuda` gibi).

---

