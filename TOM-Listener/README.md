# TOM-Listener Modülü

Bu modül, TOM AI'ın sesten metne (Speech-to-Text, STT) dönüşüm işlemlerini gerçekleştiren bileşenidir. Gerçek zamanlı ses yakalama ve transkripsiyon özellikleri sunar.

## Kurulum

Gerekli kütüphaneleri yüklemek için aşağıdaki komutu kullanın:

```bash
pip install -r requirements.txt
```

## Kullanım

Uygulamayı başlatmak için aşağıdaki komutu kullanın:

```bash
python main.py --model large-v3 --device auto --language tr
```

### Komut Satırı Argümanları
- `--model`: Kullanılacak model (seçenekler: tiny, base, small, medium, large).
- `--device`: Cihaz (seçenekler: auto, cuda, cpu).
- `--energy_threshold`: Ses algılama eşiği.
- `--record_timeout`: Ses kaydı zaman aşımı süresi.
- `--phrase_timeout`: Ses kaydı tamamlanma süresi.
- `--language`: Kullanılacak dil (seçenekler: tr, en, auto).
- `--font_size`: Metin boyutu.
- `--text_color`: Metin rengi.
- `--max_lines`: Gösterilecek maksimum satır sayısı.

## Özellikler
- Gerçek zamanlı ses yakalama ve transkripsiyon.
- Kullanıcı dostu bir GUI ile metin görüntüleme.
- Gürültü filtreleme ve ses aktivitesi algılama.

## Yapılacaklar

- [ ] STT Motor Seçimi ve Entegrasyonu
  - [ ] Yerel STT motorlarının araştırılması (Vosk, DeepSpeech vb.)
  - [ ] Türkçe dil desteği olan en uygun çözümün seçilmesi

- [ ] Ses Algılama ve İşleme
  - [ ] Çoklu mikrofon desteği

- [ ] Performans İyileştirmeleri
  - [ ] Düşük latency optimizasyonu
  - [ ] Bellek kullanımı optimizasyonu
  - [ ] CPU kullanımı optimizasyonu

- [ ] API Geliştirme
  - [ ] Gerçek zamanlı dinleme endpoint'i
  - [ ] Ses dosyası işleme endpoint'i
  - [ ] Hata yönetimi ve loglama sistemi

## Gereksinimler

- `faster_whisper`
- `speech_recognition`
- `PySide6`
