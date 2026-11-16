
# 🚀 Yapay Zeka Tabanlı Sesli Asistan Geliştirme Rehberi: Whisper, TTS ve Ollama Entegrasyonu

## 🎯 Proje Genel Bakış

Bu projede, ses tanıma 🎙️, metin-konuşma dönüşümü 🗣️ ve yapay zeka 🤖 entegrasyonu ile gelişmiş bir sesli asistan uygulaması geliştireceğiz. **Whisper** ile ses tanıma, **TTS (Text-to-Speech)** ile metinlerin sese dönüştürülmesi ve **Ollama** yapay zeka modeli ile etkileşimli bir asistan oluşturacağız.

## 🛠️ Temel Bileşenler

Proje üç ana bileşenden oluşuyor:

- **🎙️ Ses Tanıma**: Kullanıcının konuşmalarını gerçek zamanlı olarak tanıyan **Whisper** modeli kullanılıyor.
- **🗣️ Metin-Konuşma Dönüşümü**: Yanıtların doğal bir şekilde seslendirilmesi için **TTS API** entegre ediliyor.
- **🤖 Yapay Zeka Asistanı**: **Ollama** tabanlı yapay zeka ile kullanıcının sorularına yanıt veren bir asistan.

## 📁 Dosya Yapısı ve İşlevler

Projenin işlevsel dosya yapısını adım adım inceleyelim:

### 1️⃣ **whisper_deneme_1_01.py**

- **Mikrofon Dinleme ve Ses Kaydetme 🎤**: Mikrofon üzerinden konuşmaları dinleyip kaydediyor.
- **MP3'e Dönüştürme 🎧**: Kaydedilen ses dosyasını MP3 formatına çeviriyor.
- **Whisper ile Ses Tanıma 📝**: Whisper modeli ile sesler yazılı metne dönüştürülüyor.

### 2️⃣ **whisper_main_deneme.py**

- **Ana Program Akışı 🚦**: Komut tanıma ve asistanla etkileşimi sağlayan ana işleyiş.
- **Komut Tanıma ve İşleme 🧠**: Kullanıcının verdiği komutları algılayıp yanıt üretiyor.
- **Yapay Zeka Asistanı 🤖**: Asistan **Naz**, kullanıcının sorularını yanıtlayıp görevleri yerine getiriyor.

### 3️⃣ **ses_klonlama_1_01.py**

- **Metin-Konuşma Dönüşümü 🗣️**: TTS ile metinleri sese dönüştürüyor.
- **Ses Önbellekleme 💾**: Aynı sesler tekrar kullanılacaksa, hız için önbelleğe alınıyor.
- **Asenkron Ses Üretimi ⏩**: Sesin gecikme olmadan oynatılması için asenkron yapı kullanılıyor.

## 🌟 Öne Çıkan Özellikler

- **⚡ Gerçek Zamanlı Ses Tanıma**: Whisper, konuşmalarınızı hızlı ve doğru şekilde tanır.
- **🗣️ Özelleştirilebilir Ses Klonlama**: Kişisel ses klonlama ile konuşmaların belirli bir sesle yapılmasını sağlar.
- **🎛️ Sesle Sistem Kontrolü**: Bilgisayarınızdaki işlemleri sesli komutlarla yönetebilirsiniz.
- **🌦️ Güncel Bilgilere Erişim**: Hava durumu, haberler gibi güncel bilgilere hızlıca ulaşabilirsiniz.
- **🚀 GPU Hızlandırma Desteği**: Yüksek işlem gücü gerektiren işlemler için GPU desteği mevcuttur.

## 🧰 Kullanılan Teknolojiler

- **Python 🐍**
- **PyAudio, NumPy, Wave, Pydub**: Ses işleme kütüphaneleri 🎶
- **Whisper**: Ses tanıma için kullanılan yapay zeka modeli 📝
- **TTS (Text-to-Speech)**: Metinleri sesli yanıt haline getiren dönüşüm sistemi 🗣️
- **Ollama**: Yapay zeka asistanın temelini oluşturan AI modeli 🤖
- **PyTorch**: Derin öğrenme işlemleri için kullanılan framework 🧠

## 📈 Geliştirme Alanları

- **🔍 Daha Geniş Komut Seti**: Asistanın anlayabileceği komutları genişletmek.
- **🧠 Gelişmiş Doğal Dil İşleme (NLP)**: Konuşmaları daha doğal anlaması için NLP tekniklerini iyileştirmek.
- **🎨 Kullanıcı Arayüzü**: Kullanıcı deneyimini iyileştiren daha gelişmiş bir görsel ve sesli geri bildirim.

## 🚀 Sonuç

Bu proje, ses tanıma, metin-konuşma dönüşümü ve yapay zeka entegrasyonunu bir araya getirerek etkileşimli bir sesli asistan oluşturuyor. **Whisper** ile gelişmiş ses tanıma, **TTS** ile doğal sesli yanıtlar ve **Ollama** yapay zeka modeli ile kullanıcı etkileşimleri, bu projenin çekirdek yapılarını oluşturuyor. Bu projeyi takip ederek, siz de kendi **AI destekli sesli asistanınızı** geliştirebilir ve bu yenilikçi teknolojilerle tanışabilirsiniz!

---

Bu rehberi izleyerek kendi projelerinizi geliştirmek için adım adım ilham alabilirsiniz. Hazırsanız, 🚀 **başlayalım**!

---