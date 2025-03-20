
TOM AI, sesli komutları anlayabilen, işleyebilen ve sesli yanıt verebilen bir yapay zeka asistanıdır.
`Asistan şuan geliştirme aşamasındadır.`
## Proje Yapısı

```
TOM AI
├── README.md
├── TOM-Voice/              # Metinden sese (TTS) modülü
├── TOM-Listener/           # Sesten metne (STT) modülü
├── TOM-Bridge/             # LLM ile geri dönüş yapan kısım
├── TOM-UI/                 # Arayüz bileşenleri
├── TOM-Utils/              # Ortak kullanılacak yardımcı fonksiyonlar
└── docs/                   # Dökümantasyon
```

## Modüller

### TOM-Voice
Metinden sese dönüştürme (Text-to-Speech) işlemlerini gerçekleştiren modül.

### TOM-Listener
Sesten metne dönüştürme (Speech-to-Text) işlemlerini gerçekleştiren modül.

### TOM-Bridge
LLM (Large Language Model) ile iletişimi sağlayan ve yanıtları işleyen modül.

### TOM-UI
Kullanıcı arayüzü bileşenlerini içeren modüller.

#### Yapılması planlar:
---
- [ ] QT Designer ile tasarım yapılacak. 
- [ ] Audio Wave görselleştirilmesi yapılacak.
- [ ] Modern arayüz renklendirmesi yapılacak.
- [ ] Uygulamanın kilitlenmelerini önlemek için gerekli ayarlar yapılacak.

### TOM-Utils
Tüm modüller tarafından ortak kullanılan yardımcı fonksiyonları içeren modüller.
#### M4A ile MP3 Arasındaki Farklar

| **Özellik**              | **M4A**                          | **MP3**                 |
| ------------------------ | -------------------------------- | ----------------------- |
| **Ses Kalitesi**         | Daha iyi (AAC ile)               | Orta, eski algoritmalar |
| **Dosya Boyutu**         | Daha küçük                       | Daha büyük              |
| **Kayıpsız Destek**      | ALAC ile mümkün                  | Desteklemez             |
| **Destekleyen Cihazlar** | Apple cihazlarında daha yaygın   | Her yerde çalışır       |
| **Sıkıştırma Türü**      | AAC veya ALAC                    | Lossy (Kayıplı)         |
| **Kullanım Alanı**       | Apple Music, YouTube, Podcastler | Çoğu müzik çalar        |
## Kurulum

(Kurulum adımları eklenecek)

## Kullanım

(Kullanım talimatları eklenecek)

## Katkıda Bulunma

(Katkıda bulunma rehberi eklenecek)

## Lisans

(License)[]
