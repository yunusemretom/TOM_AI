# TOM-Main Modülü

Bu modül, kullanıcıdan alınan cümleleri analiz ederek komutları tespit eden bir dil modeli içerir. Kullanıcıdan gelen cümleleri değerlendirir ve uygun yanıtlar üretir.

## Kurulum

Gerekli kütüphaneleri yüklemek için aşağıdaki komutu kullanın:

```bash
pip install langchain langchain-ollama
```

## Kullanım

Uygulamayı başlatmak için aşağıdaki komutu kullanın:

```bash
python llm_test.py
```

Kullanıcıdan bir cümle girmesi istenir. Cümle girildiğinde, model komutları analiz eder ve yanıt üretir.

## Özellikler
- Kullanıcıdan alınan cümleleri analiz etme.
- Komutları tespit etme ve yanıt üretme.
- Türkçe dil desteği.

## Gereksinimler

- `langchain`
- `langchain-ollama`
