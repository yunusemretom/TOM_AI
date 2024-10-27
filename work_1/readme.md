
# Otomatik Ses Kaydı ve Metne Dönüştürme Uygulaması

Bu proje, ses seviyesi belirli bir eşiğin üzerine çıktığında kaydın otomatik olarak başlatılmasını ve eşiğin altına düştüğünde kaydın durdurulmasını sağlayan bir ses işleme uygulamasıdır. Ardından kaydedilen ses, **Whisper** veya **Coqui STT** kullanılarak metne dönüştürülür. Bu iki farklı metne çeviri çözümünü destekleyen yapı sayesinde, kullanıcıya alternatif çözümlerle esneklik sağlanmaktadır.

## Projenin Amacı
- **Otomatik Kayıt Başlatma ve Sonlandırma:** Ses seviyesi eşiğini aşan durumlarda kayıt otomatik olarak başlar, bu eşiğin altına düştüğünde ise sonlandırılır.
- **Metne Dönüştürme (STT):** Elde edilen ses dosyası, Whisper veya Coqui STT kullanılarak metne dönüştürülür.
- **Yerel Çalışma:** Modeller yerel ortamda çalıştığından internet bağlantısı olmadan hızlı sonuçlar alınabilir.

## Kullanılan Teknolojiler ve Kütüphaneler
- **Python:** Uygulamanın temel programlama dili.
- **Whisper ve Coqui STT:** İki farklı STT çözümü; Whisper, OpenAI tarafından geliştirilmiştir, Coqui ise açık kaynaklı bir alternatiftir.
- **Pyaudio & Sounddevice:** Mikrofon girişinden ses almak için gerekli kütüphaneler.

## Özellikler
- **Ses Eşiğine Dayalı Kayıt:** Belirli bir desibel seviyesini geçtiğinde kayıt başlar ve seviyenin altına düştüğünde sona erer.
- **İki Farklı STT Seçeneği:** Whisper ve Coqui STT alternatifleri sayesinde esnek kullanım.
- **Yüksek Doğruluk Oranı:** Yerel çalışabilen çözümlerle güvenilir metin çıktıları elde edilir.

## Kurulum

1. **Python Kurulumu**  
   Python'u indirin ve kurun.

2. **Gerekli Python Kütüphanelerini Yükleyin**  
   ```bash
   pip install whisper coqui-stt pyaudio sounddevice numpy
   ```

3. **Modellerin İndirilmesi**  
   Whisper ve Coqui STT modellerini kullanmadan önce, model ağırlıklarını indirmeniz gerekebilir. Bu adım Whisper veya Coqui’nin ilk çalıştırılmasında otomatik olarak tamamlanır.

## Kullanım

### Ses Kayıt Süreci
Ses seviyesi belirli bir eşiğin üzerinde olduğunda kaydı başlatmak için `record_audio()` fonksiyonu çalıştırılır. Bu eşik değeri altına düştüğünde kayıt sona erer.

### Metne Dönüştürme Süreci
Ses dosyanızı metne dönüştürmek için Whisper için `transcribe_audio_with_whisper()`, Coqui STT için `transcribe_audio_with_coqui()` fonksiyonları kullanılır.

## İlgili Notlar

- **Ses Seviyesi Eşiği Ayarlama:** `THRESHOLD` değişkeni, ortam gürültüsüne bağlı olarak özelleştirilebilir.
- **Alternatif STT Kullanımı:** Proje, Whisper ve Coqui STT için destek sunar.

## Katkıda Bulunma

Bu projeye katkıda bulunmak isteyenler, Pull Request gönderebilir veya Issue açarak öneri ve hataları bildirebilirler.

