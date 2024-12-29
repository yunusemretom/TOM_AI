# 🎙️ Optimize Edilmiş Sesli Asistan Projesi

## 📝 Proje Hakkında

Bu proje, yapay zeka tabanlı bir sesli asistan uygulamasıdır. Konuşma tanıma, doğal dil işleme ve ses sentezi teknolojilerini kullanarak kullanıcılarla etkileşime giren akıllı bir sistem oluşturulmuştur. Sistem, ev otomasyonu komutlarını anlayabilir ve doğal bir ses tonuyla yanıt verebilir.

## 🚀 Özellikler

- 🎤 Gerçek zamanlı konuşma tanıma
- 🧠 Doğal dil anlama ve işleme
- 🔊 Yüksek kaliteli ses sentezi
- ⚡ Optimize edilmiş performans
- 💾 Akıllı önbellekleme sistemi

## 🛠️ Teknik Detaylar

### 1. Ses Tanıma Modülü (`fasterWhisper_deneme.py`)

WhisperAI tabanlı bu modül, konuşmayı metne dönüştürmek için optimize edilmiş bir yapıya sahiptir. Önemli özellikler:

- Canlı mikrofon girişi desteği
- Gürültü filtreleme ve enerji eşiği ayarları
- Çoklu dil desteği (varsayılan: Türkçe)
- GPU hızlandırma optimizasyonları

```python
# Örnek Kullanım
transcriber = AudioTranscriber()
result = transcriber.process_audio()
```

### 2. Dil İşleme Modülü (`llm_model_test.py`)

LLaMA tabanlı doğal dil işleme modülü, kullanıcı komutlarını analiz eder ve uygun yanıtları oluşturur:

- Komut tanıma ve sınıflandırma
- Bağlama duyarlı yanıt üretimi
- Özelleştirilmiş komut şablonları
- Hafıza optimize edilmiş işleme

### 3. Ses Sentezi Modülü (`ses_klonlama_2_00.py`)

XTTS (Cross-Lingual Text-to-Speech) teknolojisini kullanan bu modül, doğal ve akıcı ses üretimi sağlar:

- Ses klonlama yetenekleri
- Çoklu dil desteği
- GPU hızlandırmalı ses üretimi
- Akıllı ses önbellekleme

### 4. Ses Çalma Modülü (`play_soundfile_deneme.py`)

Üretilen seslerin sorunsuz çalınmasını sağlayan optimize edilmiş modül:

- Asenkron ses çalma
- Kuyruk yönetimi
- Thread-safe operasyonlar
- Düşük gecikmeli çalma

## 🚦 Sistem Gereksinimleri

- NVIDIA GPU (en az 6GB VRAM)
- 16GB RAM
- M2 SSD
- Python 3.8+
- CUDA Toolkit
- FFmpeg

## 🛠️ Kurulum

1. Gerekli Python paketlerini yükleyin:
```bash
pip install torch torchaudio faster-whisper langchain-ollama TTS pygame
```

2. Model dosyalarını indirin ve yapılandırın:
```bash
# Model yollarını ayarlayın
model_path = "path/to/model.pth"
config_path = "path/to/config.json"
vocab_path = "path/to/vocab.json"
speaker_path = "path/to/speakers_xtts.pth"
```

3. Ses örneklerini hazırlayın:
```bash
# Konuşmacı ses örneği
speaker_audio = "./ugur_t.mp3"
```

## 💡 Performans İpuçları

1. **GPU Optimizasyonu**
   - CUDA hesaplama yeteneklerini etkinleştirin
   - Mixed precision training kullanın
   - Batch işleme boyutlarını optimize edin

2. **Bellek Yönetimi**
   - Önbellek boyutlarını sisteminize göre ayarlayın
   - Gereksiz model yüklemelerinden kaçının
   - Düzenli bellek temizliği yapın

3. **Disk I/O**
   - SSD kullanın
   - Önbellek klasörünü düzenli temizleyin
   - Geçici dosyaları RAM disk'e yönlendirin

## 🤝 Katkıda Bulunma

Projeye katkıda bulunmak için:

1. Fork yapın
2. Feature branch oluşturun
3. Değişikliklerinizi commit edin
4. Branch'inizi push edin
5. Pull Request oluşturun

## 📝 Notlar

- Sistem ilk başlatıldığında modellerin yüklenmesi biraz zaman alabilir
- GPU belleği yönetimi için periyodik temizlik önerilir
- Ses kalitesi/performans dengesini sistem özelliklerinize göre ayarlayın

## 🔑 Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için `LICENSE` dosyasına bakın.

---
*Bu README son güncelleme: 29.12.2024*
