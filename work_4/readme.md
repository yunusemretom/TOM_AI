


# 🎙️ Google Colab Üzerinde Coqui TTS Kullanarak Türkçe Ses Klonlama Eğitimi

Bu rehberde, **Google Colab** üzerinde **Coqui TTS** veya benzeri bir TTS modelini Türkçe bir ses veri seti ile nasıl eğitebileceğimizi adım adım öğreneceğiz. Bu yöntemle doğal tonlama ve vurgulara sahip bir Türkçe ses klonlama modeli geliştirebileceksin!

## 🛠️ Gerekli Kütüphaneleri Kurma

Öncelikle, Colab üzerinde çalışmak için gerekli kütüphaneleri yükleyelim. Bu kütüphaneler Coqui TTS, sox (ses işleme) ve diğer bağımlılıkları içerir.

```python
!pip install TTS
!apt-get install sox
```

## 📂 Veri Setini Hazırlama ve Yükleme

### 1. Ses Dosyalarını Hazırlayın
   - Ses dosyalarını `.wav` formatında **16-bit** olacak şekilde düzenle.
   - Tüm dosyalar, Colab'da oluşturulacak `wavs` klasöründe saklanmalıdır.

### 2. `metadata.csv` Dosyasını Oluşturun
Her ses dosyasına karşılık gelen konuşma metinlerini saklamak için bir `metadata.csv` dosyası oluşturmalısın. Bu dosyanın yapısı aşağıdaki gibi olmalıdır:

```plaintext
data/
├── wavs/
│   ├── 0001.wav
│   ├── 0002.wav
│   └── ...
└── metadata.csv
```

`metadata.csv` formatı:

```plaintext
<dosya_adı>|<konuşma_metni>
```

Örneğin:
```plaintext
0001|Merhaba, bu bir deneme cümlesidir.
0002|Yapay zeka ses klonlama işlemi yapılıyor.
```

### 📤 Colab'a Dosya Yükleme
Dosyaları Google Colab'e şu komut ile yükleyebilirsin:

```python
from google.colab import files
uploaded = files.upload()
```

## 🔍 Modeli İndirme ve Yapılandırma

Eğitim için kullanacağımız Coqui TTS modelini indirelim ve yapılandıralım. **xtts_v2** modelini kullanarak eğitim yapacağız.

```python
from TTS.utils.manage import ModelManager

model_manager = ModelManager()
model_path, config_path, _ = model_manager.download_model("tts_models/multilingual/multi-dataset/xtts_v2")
```

## ⚙️ Model Konfigürasyonlarını Düzenleme

Config dosyasını açarak eğitim parametrelerini ayarlayacağız. Config dosyasında batch boyutu, öğrenme hızı (learning rate) gibi parametreleri değiştirebiliriz.

```python
import json

# Config dosyasını düzenle
with open(config_path, "r") as f:
    config = json.load(f)

config["batch_size"] = 32  # Modelin boyutuna göre bu değeri değiştirebilirsin
config["learning_rate"] = 0.0001  # Eğitim hızını ayarlamak için
config["output_path"] = "/content/output/"  # Eğitim çıktıları bu klasörde olacak

# Değişiklikleri kaydet
with open(config_path, "w") as f:
    json.dump(config, f)
```

## 🚀 Model Eğitimini Başlatma

Artık modeli eğitmeye başlayabiliriz. Eğitim işlemi birkaç saat sürebilir, bu yüzden sabırlı olman gerekebilir. Eğitim sırasında GPU kullanımı için Colab ortamında **GPU**'yu etkinleştirdiğinden emin ol.

```python
from TTS.tts import Trainer

trainer = Trainer(
    config_path=config_path,
    model_path=model_path,
    run_name="turkish_tts"
)
trainer.fit()
```

> 💡 **Not**: Eğer Colab GPU'yu kullanmazsa, Menüden `Runtime` > `Change Runtime Type` kısmından GPU seçimini yapabilirsin.

## 💾 Eğitimi Tamamladıktan Sonra Modeli Kaydetme

Eğitim süreci tamamlandığında, eğitilen modelin çıktısını sıkıştırarak indirilebilir hale getirebilirsin.

```python
import shutil
shutil.make_archive("/content/turkish_tts_model", 'zip', "/content/output/")
```

## 🎙️ Eğitilmiş Modeli Test Etme

Modelin eğitimi bittiğinde, test etmek için örnek bir cümle yazabilir ve bu cümlenin sesli çıktısını oluşturabilirsin.

```python
from TTS.api import TTS

# Eğitilen modeli yükle
tts = TTS(model_path=model_path, config_path=config_path)

# Test metnini seslendir
tts.tts_to_file(text="Merhaba, bu eğitilmiş bir Türkçe sestir.", speaker_wav="/content/wavs/0001.wav", file_path="test_output.wav")
```

## 🎉 Sonuç

Bu adımları takip ederek Türkçe ses klonlama modelini başarıyla eğitebilirsin! Modelin çıktısındaki sesin doğal ve akıcı olması için veri setinin kalitesi oldukça önemli. Eğer ek ayarlamalara ihtiyaç duyarsan, eğitim parametrelerini optimize edebilirsin.

Umarım faydalı olmuştur, bol şans! 🎈
```

---

Bu `.md` dosyası ile adımları kolayca takip edebilirsin. Geri bildirimlerin veya takıldığın yerler olursa yine yardımcı olmaktan memnuniyet duyarım.