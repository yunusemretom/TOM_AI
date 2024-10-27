# 🎙️ Sesli Asistan Uygulaması

Bu proje, ses tanıma ve yapay zeka destekli bir sesli asistan uygulaması geliştirmeyi hedeflemektedir. Uygulama, kullanıcıların sesli komutlarıyla etkileşim kurmasını sağlayarak doğal bir deneyim sunar.

## 🚀 Özellikler

### 1. Ses İşleme
- **`whisper_deneme_1_00`**: Konuşmayı metne çevirmek için kullanılır. Ancak, sesin yazıya çevrilme süresi oldukça yavaştır. Bu durumu iyileştirmek için daha hızlı bir ses tanıma modeli araştırmayı planlıyorum.
- **`ses_klonlama_1_00`**: Metni sese dönüştürmek için kullanılmaktadır. Coqui AI (TTS modülü) ile oldukça güzel sesler elde ediliyor; fakat bazı ses düzenlemeleri gerekmektedir. Ses hala robotik bir tınıya sahip, bu yüzden daha doğal bir ses oluşturmak için ses düzenleme teknikleri üzerinde çalışmayı düşünüyorum.

### 2. Yapay Zeka
- **`ollama`**: AI modeli entegrasyonu için kullanılır. Bu kütüphane ile "Naz" adında bir yapay zeka ajanı oluşturulmuştur.

### 3. Sistem Etkileşimi
- **`subprocess`**: Sistem komutlarını çalıştırmak için kullanılır (örneğin, not defteri açma).
- **`Library.klavye_yonet`**: Ses seviyesi kontrolü gibi klavye işlemleri için kullanılır.

### 4. Metin İşleme
- **`fuzzywuzzy`**: Kullanıcı komutlarını tanımak için metin benzerliği karşılaştırması yapar.

### 5. Harici Bilgi Kaynakları
- **`Library.Hava_durum`**: Hava durumu bilgilerini almak için kullanılır.
- **`Library.Haber`**: Güncel haber bilgilerini çekmek için kullanılmaktadır.

### 6. Kullanıcı Arayüzü
- **`rich_deneme`**: Zengin metin çıktısı için özelleştirilmiş bir print fonksiyonu sağlar.

## 🔧 Çözümler ve Geliştirme Planları

- **Ses Tanıma Hızını Artırmak**: Whisper ile denediğim STT modülünün ses yazıya çevirme süresi yavaş olduğu için, alternatif ve daha hızlı bir ses tanıma modeli araştırmayı planlıyorum.
  
- **Ses Kalitesini İyileştirmek**: Coqui AI ile elde edilen sesin robotik tınısını düzeltmek için ses düzenleme tekniklerini geliştireceğim. Bu sayede daha doğal bir ses elde etmeyi umuyorum.

- **Karar Mekanizmasını Geliştirmek**: Ana deneme dosyasında, asistanın gerekli görevleri yerine getirmesi için karar mekanizmasını düzenlemem gerekiyor. Bu, kullanıcı ile etkileşimi daha etkili hale getirecektir.

## 🛠️ Kullanım

Uygulama, kullanıcının sesli komutlarını dinleyerek bunları metne çevirir. Ollama AI modeli kullanılarak anlamlı yanıtlar üretilir. Kullanıcı, önceden tanımlanmış komutları (örneğin, uygulama açma, ses seviyesi ayarlama, haber okuma) sesli olarak verebilir.

Asistan, sürekli olarak kullanıcı girişi bekler, gelen komutları işler ve uygun yanıtları seslendirir. Bu yapı, kullanıcı ile doğal bir etkileşim sağlamayı amaçlamaktadır.

## 🌐 Teknolojiler

- Ses Tanıma
- Doğal Dil İşleme
- Sistem Kontrolü

