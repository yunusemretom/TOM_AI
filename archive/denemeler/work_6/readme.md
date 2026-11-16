# 🎙️ Gerçek Zamanlı Konuşma Çevirisi ve Ses Klonlama Sistemi 🤖

## 📝 Proje Genel Bakış
Bu etkileyici proje, konuşma tanıma, çeviri ve ses klonlama teknolojilerini birleştirerek gerçek zamanlı bir konuşmadan konuşmaya çeviri sistemi oluşturuyor. Sadece çeviri yapmakla kalmayıp, klonlanmış bir sesle konuşan kişisel bir tercüman gibi! 

## 🚀 Temel Özellikler
- 🎤 Faster Whisper ile gerçek zamanlı konuşma tanıma
- 🌐 Google Translate ile otomatik çeviri
- 🗣️ XTTS ile ses klonlama
- 🔊 Gerçek zamanlı ses çalma
- 💾 Daha iyi performans için ses önbellekleme sistemi

## 🛠️ Teknik Bileşenler

### 1. Konuşma Tanıma (fasterWhisper_deneme.py)
- Verimli konuşma tanıma için Faster Whisper modeli kullanır
- Çoklu dil desteği sunar
- Enerji eşiği algılama ile arka plan dinleme uygular
- Kuyruk sistemi ile gerçek zamanlı ses işleme

### 2. Çeviri Motoru (main.py)
- Metin çevirisi için Google Translate entegrasyonu
- Çevirmen örneği için tekil (singleton) desen uygulaması
- Doğal konuşma çıktısı için cümle segmentasyonu

### 3. Ses Klonlama (ses_klonlama_2_00.py)
- Yüksek kaliteli ses sentezi için XTTS modeli
- Referans ses ile konuşmacı adaptasyonu
- Oluşturulan sesler için önbellekleme sistemi
- GPU hızlandırma desteği

### 4. Ses Çalma (play_soundfile_deneme.py)
- Güvenilir ses çalma için Pygame kullanımı
- Bloklamayı önlemek için thread tabanlı çalma
- Senkronize ses kuyruğu yönetimi

## 💻 Nasıl Çalışır?
1. Sistem sürekli olarak konuşma girişini dinler
2. Konuşma algılandığında Faster Whisper ile yazıya dönüştürülür
3. Yazıya dönüştürülen metin hedef dile çevrilir
4. Çevrilen metin klonlanmış ses kullanılarak konuşmaya dönüştürülür
5. Oluşturulan ses gerçek zamanlı olarak çalınır

## 🔧 Sistem Gereksinimleri
- Python 3.x
- CUDA destekli GPU (önerilen)
- Gerekli Python paketleri:
  - faster-whisper
  - translatepy
  - TTS
  - pygame
  - torch
  - torchaudio

## 📂 Proje Yapısı
```
work_6/
├── main.py                    # Ana uygulama kontrolcüsü
├── fasterWhisper_deneme.py   # Konuşma tanıma modülü
├── ses_klonlama_2_00.py      # Ses klonlama modülü
└── play_soundfile_deneme.py  # Ses çalma işleyicisi
```

## 🎯 Kullanım Alanları
- Gerçek zamanlı tercüme hizmetleri
- Dil öğrenme uygulamaları
- Çok dilli iletişim için erişilebilirlik araçları
- Seslendirme üretimi
- Özel sesli kişisel AI asistanı

## ⚠️ Önemli Notlar
- Sistem, ses klonlama için özel model dosyaları gerektirir
- Ses kalitesi seçilen model boyutuna bağlıdır
- GPU hızlandırması performansı önemli ölçüde artırır
- Optimal sonuçlar için uygun mikrofon kurulumu önemlidir

## 🔜 Gelecek İyileştirmeler
- Daha fazla dil desteği ekleme
- Daha iyi gürültü azaltma
- Bellek kullanımını optimize etme
- Web arayüzü ekleme
- Gerçek zamanlı performansı iyileştirme

## 🤝 Katkıda Bulunma
Bu projeye katkıda bulunmaktan çekinmeyin! Hata düzeltmeleri, yeni özellikler veya dokümantasyon iyileştirmeleri olsun, tüm katkılar memnuniyetle karşılanır.

## 📜 Lisans
Bu proje açık kaynaklıdır ve standart açık kaynak lisansları altında kullanılabilir.

---
*Not: Sistemi çalıştırmadan önce her bileşenin gereksinimlerini ve kurulum talimatlarını kontrol ettiğinizden emin olun.*
