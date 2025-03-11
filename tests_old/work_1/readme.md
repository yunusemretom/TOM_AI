
# Sesli Asistan Uygulaması Özeti 🎤🤖

Bu Python dosyası, ses tanıma ve yapay zeka destekli bir sesli asistan uygulamasını içermektedir. Proje, kullanıcı ile etkileşimi artırmak ve doğal bir deneyim sunmak amacıyla çeşitli teknolojileri bir araya getirmiştir. İşte temel özellikler ve kullanılan kütüphaneler:

## 1. Ses İşleme 🎶
- **`whisper_deneme_1_00`**: Bu kütüphane, kullanıcının konuşmalarını metne çevirmek için kullanılır. Yüksek doğruluk oranı ile ses tanıma işlemini gerçekleştirir.
- **`ses_klonlama_1_00`**: Metinleri doğal bir sesle seslendirmek için kullanılır. Ancak, şu anda seslerin robotik bir tonda olduğu ve daha fazla iyileştirme gerektirdiği gözlemlenmiştir. 

## 2. Yapay Zeka 🧠
- **`ollama`**: Bu, yapay zeka modeli entegrasyonu için kullanılır. Uygulamada "Naz" adında bir AI ajanı oluşturulmuş olup, kullanıcı ile etkileşimde bulunmasını sağlar.

## 3. Sistem Etkileşimi ⚙️
- **`subprocess`**: Sistem komutlarını çalıştırmak için kullanılır. Örneğin, kullanıcıdan gelen komutlarla not defterini açmak gibi işlemler yapılabilir.
- **`Library.klavye_yonet`**: Ses seviyesi kontrolü gibi klavye işlemlerini yönetmek için kullanılır, böylece kullanıcı deneyimi daha akıcı hale gelir.

## 4. Metin İşleme 📜
- **`fuzzywuzzy`**: Bu kütüphane, kullanıcı komutlarını tanımak için metin benzerliği karşılaştırması yapar. Böylece, asistan daha esnek ve doğru yanıtlar verebilir.

## 5. Harici Bilgi Kaynakları 🌍
- **`Library.Hava_durum`**: Hava durumu bilgilerini almak için kullanılır, böylece kullanıcıya anlık hava durumu raporları sunabilir.
- **`Library.Haber`**: Güncel haber bilgilerini çekmek için kullanılır, böylece kullanıcıya en son gelişmeleri aktarabilir.

## 6. Kullanıcı Arayüzü 💻
- **`rich_deneme`**: Zengin metin çıktısı için özelleştirilmiş bir print fonksiyonu sağlar. Bu sayede kullanıcı, metinlerin daha okunabilir ve hoş bir şekilde görüntülenmesini sağlar.

## Uygulama İşleyişi 🛠️
Uygulama, kullanıcının sesli komutlarını dinler, bunları metne çevirir ve **Ollama AI modeli** kullanarak yanıtlar üretir. Kullanıcıdan gelen belirli komutları (örneğin, uygulama açma, ses seviyesi ayarlama, haber okuma) doğrudan işleyebilir. 

Asistan, sürekli olarak kullanıcı girişi bekler, gelen komutları işler ve uygun yanıtları seslendirir. Bu yapı, kullanıcı ile doğal bir etkileşim sağlamayı amaçlar. Uygulama, ses tanıma, doğal dil işleme ve sistem kontrolü gibi çeşitli teknolojileri bir araya getirerek kapsamlı ve etkileşimli bir sesli asistan deneyimi sunmayı hedeflemektedir.

