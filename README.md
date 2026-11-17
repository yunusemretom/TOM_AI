# TOM AI Asistan

TOM AI, yerelde çalışan, Türkçe konuşan ve anlık yanıt veren kişisel bir sesli asistandır.
`Asistan şu an geliştirme aşamasındadır.` Hedef platform: Linux.

**Ayrıntılı anlatım ve sesi değiştirme rehberi: [docs/NASIL_CALISIR.md](docs/NASIL_CALISIR.md)**

## Ses ayarları

Sesin bütün ayarları `config/ses.yaml` içinde (model, referans klipler, hız, sıcaklık…). İlk kez: `cp config/ses.example.yaml config/ses.yaml`. Denemek için: `PYTHONPATH=. .venv/bin/python tools/ses_dene.py --cal`.

## Proje yapısı

```
TOM_AI/
├── tom/                 # Asıl kod (Python paketi)
│   ├── audio/           # Mikrofon girişi, hoparlör çıkışı, VAD
│   ├── listener/        # Sesten metne (STT)
│   ├── brain/           # LLM, komut algılama, sohbet bağlamı
│   ├── voice/           # Metinden sese (TTS), ses klonu önbelleği
│   └── pipeline/        # Hepsini birbirine bağlayan akış (dinle → düşün → konuş)
├── tools/               # Ölçüm ve teşhis scriptleri (CUDA testi vb.)
├── models/              # Model ağırlıkları (git dışı, bkz. models/README.md)
├── docs/
│   ├── moduller/        # Modül başına yapılacaklar listeleri
│   └── ses-formatlari.md
└── archive/             # Eski denemeler; yalnızca başvuru için, yeni kod buraya yazılmaz
    ├── denemeler/       # Eski tests_old (work_1 … work_12)
    ├── tom_listener_v0/ # İlk STT + PySide arayüz denemesi
    └── tom_main_llm_test_v0.py
```

En güncel çalışan prototip: `archive/denemeler/work_8/main.py`
(faster-whisper + Ollama + XTTS v2 klon ses).

## Modüller

Her modülün yapılacaklar listesi `docs/moduller/` altında:
[brain](docs/moduller/brain.md) · [voice](docs/moduller/voice.md) ·
[pipeline](docs/moduller/pipeline.md) · [ui](docs/moduller/ui.md) · [utils](docs/moduller/utils.md)

## Kurulum

Adımlar `requirements.txt` dosyasının başında (torch cu124 + coqui-tts + DeepSpeed, `uv` ile `.venv`).

## Masaüstünden başlatma

```bash
bash scripts/masaustune-ekle.sh        # bir kez: uygulama menüsüne "TOM" ekler (kaldırmak: --kaldir)
```

Menüden **TOM**'a tıkla → küçük pencere açılır (durum küresi, sohbet, Mikrofon/Uyut/Sus/Üstte düğmeleri, yazarak soru). Sağ tık: "TOM (hızlı model, e2b)", "TOM (terminalde, ayrıntılı kayıt)" ve "TOM'u kapat". Pencere kayıtları: `logs/tom-pencere.log`.
Zaten açıksa ikinci kez başlatmaz. Dock'a sabitlemek: sağ tık → "Sık kullanılanlara ekle".
Terminalden: `scripts/tom-pencere.sh` (pencere) ya da `scripts/tom-baslat.sh` (terminal); ek argümanlar TOM'a geçer. Kapatmak: `scripts/tom-kapat.sh`.

Ses denemesi için kendi cümlelerin: `config/ses_cumleler.txt` (her satıra bir cümle) ya da `tools/ses_dene.py --cumle "…"`.

## Kullanım

```bash
PYTHONPATH=. .venv/bin/python -m tom --deepspeed                 # mikrofon + hoparlör
PYTHONPATH=. .venv/bin/python -m tom --deepspeed --llm gemma4:e4b --silence-ms 400
PYTHONPATH=. .venv/bin/python -m tom --input-wav soru.wav --output-wav cevap.wav   # deneme
```

Asistan konuşurken mikrofon dinlenmez (yankı iptali yok). Kulaklıkla `--barge-in` araya girmeye izin verir.
Varsayılanlar: XTTS `models/xtts_ince_test1` (fine-tune edilmiş), klon referansı `models/voices/ugur/ref_{1,2,3}.wav`
(EQ ile açılmış; filtre `filtre.txt` içinde). Bunlar yoksa temel XTTS (`~/.local/share/tts/...xtts_v2`) ve
`~/Downloads/optimized_model/reference.wav` kullanılır. `--xtts`, `--ref` ile değişir. STT `large-v3-turbo`
(GPU, int8), LLM `gemma4:e4b` (28 katman GPU'da; `--llm gemma4:e2b` daha hızlı).

TTS'e giden metnin sonundaki nokta kaldırılır (`tom/voice/text_prep.py`): XTTS noktada hemen durmayıp
1 sn'ye varan fazladan ses üretiyordu.

## Araçlar (internet, hatırlatıcı, hafıza…)

LLM (varsayılan `gemma4:e4b`, 6 GB kartta 28 katmanı GPU'da) gerektiğinde araç çağırır; araç çalışırken
"Bir bakayım." der. Hızlı komutlar (saat, zamanlayıcı, müzik, ses, kendi şehrinin havası) LLM'e hiç gitmez.

| Araç | Ne yapar |
|---|---|
| `web_ara`, `web_oku` | İnternette arar (ddgs, anahtarsız), en iyi 3 sayfanın metnini okur |
| `haberler` | Son haber başlıkları |
| `hava_tahmini` | Herhangi bir şehir, 7 güne kadar (Open-Meteo) |
| `doviz`, `hesapla` | Güncel kur (open.er-api.com), güvenli hesap makinesi |
| `hatirlatici_kur` / `_listele` / `_sil` | Saatli hatırlatıcı ("yarın 9'da toplantı"), kapalıyken kaçan açılışta söylenir |
| `not_al`, `notlari_oku` | Notlar |
| `hatirla`, `unut` | Kalıcı bilgi ("kahvemi sütsüz içerim"), sistem istemine girer |
| `uygulama_ac`, `site_ac` | Kurulu uygulama (.desktop) ya da tarayıcıda site; kabuk komutu çalıştırılmaz |
| `sistem_durumu` | İşlemci, RAM, disk, pil, GPU |

Hafıza, notlar ve hatırlatıcılar `data/hafiza.json` içinde (git dışı). `--no-tools` araçları kapatır.

Gemma 4 notu: `think=False` (hızlı) araç çağırmayı ~%30 bozuyor (çağrı ham metin olarak geliyor ya da hiç
çağrılmıyor). Ajan ham çağrıyı kendisi çözer ve asla seslendirmez; eylem isteklerinde (hatırlat, aç, not al…)
ilk cevabı bekletir, model aracı atlarsa soruyu düşünme moduyla yeniden sorar (20/20 doğru araç).

## Ölçüm

```bash
export CUDA_HOME=/usr/local/cuda-12.4 PATH=/usr/local/cuda-12.4/bin:$PATH PYTHONPATH=.
XTTS=~/.local/share/tts/tts_models--multilingual--multi-dataset--xtts_v2
REF=~/Downloads/optimized_model/reference.wav
.venv/bin/python tools/tts_bench.py --model-dir $XTTS --ref $REF --deepspeed          # yalnız TTS
.venv/bin/python tools/pipeline_bench.py --llm gemma4:e2b --model-dir $XTTS --ref $REF --deepspeed --out logs/pipeline_bench
.venv/bin/python tools/stt_bench.py --data ~/Documents/Projeler/Ses_Klon/xtts-finetune-webui/finetune_models/dataset
.venv/bin/python -m pytest -q tests
```

`PYTHONPATH=.` şart: kabuktaki ROS yolu pytest eklentilerini bozuyor.

## XTTS fine-tune (podcast → veri seti → Colab)

1. **Veri seti (yerelde):** podcast bölümlerini bir klasöre koy, hedef konuşmacının 10–30 sn'lik temiz
   bir örneğini ver (konuk varsa önemli). Hedef: 20–60 dk temiz konuşma.
   ```bash
   PYTHONPATH=. .venv/bin/python -m tools.finetune.build_dataset podcastlar/ --ref sunucu_ornek.wav \
       --out data/xtts_dataset --zip     # müzik varsa: --demucs (uv pip install --python .venv demucs)
   ```
   Çıktı: `wavs/`, `metadata_train.csv`, `metadata_eval.csv`, `rapor.json` (atılan klipler ve
   nedenleri), `gozden_gecir.csv` (dinlenmeye değer şüpheli klipler).
2. **Eğitim (Colab A100):** `tools/finetune/XTTS_FineTune_Colab.ipynb` dosyasını Colab'da aç,
   `data/xtts_dataset.zip`'i Drive'da `MyDrive/TOM_AI/` altına yükle, hücreleri sırayla çalıştır.
   Notebook `make_notebook.py` ile `train_xtts.py` ve `eval_xtts.py`'den üretilir.
3. **Kullanım:** indirilen `hazir_model` klasörüyle
   `python -m tom --deepspeed --xtts hazir_model --ref hazir_model/reference.wav`.
