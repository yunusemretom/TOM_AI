# AI Proje Kütüphanesi 🤖📚

Bu proje, çeşitli yapay zeka ve medya işleme araçlarını içeren bir kütüphane sunmaktadır. Aşağıda, projede kullanılan üç ana dosyanın özeti bulunmaktadır.

## 1. LLM Fail Model Testi (`work_7/llm_fail_model_test.py`) 🧠

Bu dosya, **Ollama** isimli bir yapay zeka modelini kullanarak kullanıcıdan gelen sorulara yanıt vermek için bir **Agent** sınıfı tanımlar. Ajan, belirli bir rol üstlenerek metin üretir. 

### Öne Çıkan Özellikler:
- **Ollama Client**: Yapay zeka modeline bağlanmak için bir istemci oluşturur.
- **Agent Sınıfı**: Kullanıcıdan gelen komutları işleyerek yanıtlar üretir.
- **Örnek Kullanım**: Kullanıcıdan gelen bir soruya yanıt almak için `generate` metodu kullanılır.

### Kullanım:
```python
ollama_response = Ada.generate("saatin kaç olduğunu öğrenmek istiyorum")
print(ollama_response)
```

---

## 2. LLM Model Testi (`work_7/llm_model_test.py`) 🔍

Bu dosya, kullanıcının sorularını analiz eden ve belirli komutları tanımlayan bir sistem içerir. **Langchain** kütüphanesi kullanılarak, kullanıcıdan gelen cümlelerdeki komutları tespit eder.

### Öne Çıkan Özellikler:
- **Komut Şablonu**: Kullanıcının cümlesinde bir komut olup olmadığını analiz eder.
- **Komut Sözlüğü**: Belirli komutları ve bunların numaralarını tanımlar.
- **Zincir Yapısı**: Şablon ve model birleştirilerek kullanıcıdan gelen sorular işlenir.

### Kullanım:
```python
result = chain.invoke({"question": "Sence türkiye nasl bir yer? içerisi çok sıcak oldu klimayı açar mısın?", "commands": commands_dict})
print(result)
```

---

## 3. YouTube Ses İndirme (`work_7/youtube_ses_indirme.py`) 🎵

Bu dosya, **yt-dlp** kütüphanesini kullanarak YouTube videolarından ses dosyası indirmeye yarayan bir fonksiyon içerir. Kullanıcı, belirli bir URL ile ses dosyasını MP3 formatında indirebilir.

### Öne Çıkan Özellikler:
- **Ses İndirme**: Belirtilen URL'den en iyi ses kalitesinde dosya indirir.
- **FFmpeg Kullanımı**: Ses dosyalarını MP3 formatına dönüştürür.

### Kullanım:
```python
liste = ["https://www.youtube.com/watch?v=TLGrrztZpfM"]
for i in liste:
    download_audio(i)
```

---

## Sonuç 🎉

Bu proje, yapay zeka ile etkileşim kurma ve medya dosyalarını işleme konularında güçlü araçlar sunmaktadır. Her bir dosya, belirli bir işlevselliği yerine getirerek kullanıcı deneyimini geliştirmeyi hedefler. Projeyi kullanarak kendi yapay zeka uygulamalarınızı geliştirebilir ve medya içeriklerinizi kolayca işleyebilirsiniz!