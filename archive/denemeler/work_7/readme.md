# 🎙️ Sesli Asistan Projesi

## 📝 Proje Açıklaması
Bu proje, Türkçe konuşma tanıma, metin üretme ve ses sentezleme özelliklerine sahip bir sesli asistan uygulamasıdır. Kullanıcıların sesli komutlarını algılayıp, uygun yanıtlar üreterek sesli geri bildirim sağlar.

## 🛠️ Temel Özellikler
- 🎤 Gerçek zamanlı ses tanıma (Faster Whisper)
- 🤖 Yapay zeka destekli metin üretimi (Mistral/Ollama)
- 🗣️ Kişiselleştirilmiş ses klonlama (XTTS)
- 🎮 Ev otomasyonu komut sistemi
- 🔊 Gerçek zamanlı ses çıkışı

## 💻 Kullanılan Teknolojiler
- Faster Whisper: Konuşma tanıma
- Langchain & Ollama: LLM entegrasyonu
- XTTS (XTensorTTS): Ses sentezleme
- PyGame: Ses çalma
- YouTube-DLP: YouTube ses indirme

## 📋 Komut Listesi
```python
commands_dict = {
    "ışıkları aç": 1,
    "ışıkları kapat": 2,
    "klimayı aç": 3,
    "klimayı kapat": 4,
    "tv aç": 5,
    "tv kapat": 6,
}
```

## 🚀 Kurulum
1. Gerekli Python paketlerini yükleyin:
```bash
pip install langchain-core langchain-ollama faster-whisper pygame yt-dlp torchaudio
```

2. Model dosyalarını hazırlayın:
   - XTTS model dosyaları
   - Whisper modeli
   - Ollama/Mistral modeli

3. Konuşmacı ses örneğini hazırlayın (`ugur_t.mp3`)

## 📦 Proje Yapısı
- `main.py`: Ana uygulama
- `fasterWhisper_deneme.py`: Ses tanıma modülü
- `ses_klonlama_2_00.py`: Ses sentezleme modülü
- `llm_model_test.py`: LLM entegrasyonu
- `play_soundfile_deneme.py`: Ses çalma modülü
- `youtube_ses_indirme.py`: YouTube ses indirme aracı

## 🎯 Kullanım
1. Ana uygulamayı başlatın:
```bash
python main.py
```

2. Sisteme sesli komut verin
3. Asistan komutu işleyip sesli yanıt verecektir

## 🔍 Önemli Notlar
- Sistem Türkçe dil desteği ile çalışmaktadır
- Ses kalitesi için sessiz bir ortam önerilir
- GPU kullanımı performansı artıracaktır

## 🤝 Katkıda Bulunma
Projeye katkıda bulunmak için:
1. Fork yapın
2. Feature branch oluşturun
3. Değişikliklerinizi commit edin
4. Pull request gönderin

## ⚠️ Gereksinimler
- Python 3.8+
- CUDA destekli GPU (önerilen)
- Mikrofon
- Hoparlör

## 📜 Lisans
Bu proje açık kaynak olarak paylaşılmıştır.
