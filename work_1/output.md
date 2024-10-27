
# Otomatik Ses Kaydı ve Metne Dönüştürme Uygulaması

Bu proje, ses seviyesi belirli bir eşiğin üzerine çıktığında kaydın otomatik olarak başlatılmasını ve eşiğin altına düştüğünde durmasını sağlayan bir ses işleme uygulamasıdır. Kaydedilen ses, **Whisper** veya **Coqui STT** kullanılarak metne dönüştürülür. Kullanıcıya iki farklı metne dönüştürme seçeneği sunularak projeye esneklik kazandırılmıştır.

## Projenin Amacı
- **Otomatik Kayıt Başlatma ve Sonlandırma:** Belirlenen ses seviyesi eşiğini geçen durumlarda kayıt otomatik başlar ve eşiğin altına düştüğünde sona erer.
- **Metne Dönüştürme (STT):** Elde edilen ses dosyası, Whisper veya Coqui STT ile metne dönüştürülür.
- **Yerel Çalışma:** İki model de yerel ortamda çalışabildiğinden internet bağlantısına gerek kalmadan hızlı sonuçlar alınabilir.

## Kullanılan Teknolojiler ve Kütüphaneler
- **Python:** Uygulamanın temel dili.
- **Whisper ve Coqui STT:** İki farklı STT çözümü; Whisper, OpenAI tarafından geliştirilmişken, Coqui açık kaynaklı bir alternatiftir.
- **Pyaudio & Sounddevice:** Mikrofon girişinden ses almak için.
  
## Performans ve Hız Konusundaki Deneyimler

**Whisper** çözümünün doğruluk oranı yüksek olsa da, bazı hız kısıtlamaları bulunmakta. Özellikle gerçek zamanlı veya düşük gecikmeli uygulamalarda performans düşüşü yaşanabilir. Bu nedenle, Whisper ile çalışırken bazı durumlarda işleme süreleri uzayabilir. Alternatif olarak **Coqui STT**, yerel ortamlarda daha hızlı sonuçlar verebilir ve bu tür uygulamalarda hız avantajı sunabilir. Bu nedenle, ihtiyaçlarınıza göre her iki çözümü de karşılaştırarak en uygun olanı kullanabilirsiniz.

## Ses Klonlama ve Ses Kalitesi

Projede ses klonlama denemeleri de yapılmıştır. Ancak, şu anda ses klonlama sonucu elde edilen seslerin doğal bir insan sesinden çok robotik bir sese daha yakın olduğu görülmüştür. Doğal bir tonda klonlanmış sesler elde etmek için ses verilerinin artırılması, modelin ince ayarı (fine-tuning) ve daha gelişmiş modellerin kullanımı gerekebilir. Bununla birlikte, Coqui veya Whisper gibi daha fazla eğitimli modeller ve gelişmiş yapay zeka algoritmaları ile doğal ses klonlama başarıya ulaşabilir.

## Özellikler
- **Ses Eşiğine Dayalı Kayıt:** Belirli bir desibel seviyesini geçtiğinde kayıt başlar ve seviyenin altına düştüğünde sona erer.
- **İki Farklı STT Seçeneği:** Whisper ve Coqui STT sayesinde esnek kullanım.
- **Yüksek Doğruluk Oranı:** Yerel çözümlerle güvenilir metin çıktıları elde edilir.

## İlgili Notlar

- **Ses Seviyesi Eşiği Ayarlama:** `THRESHOLD` değişkeni ortam gürültüsüne bağlı olarak özelleştirilebilir.
- **Alternatif STT Kullanımı:** Hem Whisper hem de Coqui STT desteklenmektedir.
