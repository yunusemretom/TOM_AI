# TOM AI Asistan

TOM AI, yerelde çalışan, Türkçe konuşan ve anlık yanıt veren kişisel bir sesli asistandır.
`Asistan şu an geliştirme aşamasındadır.` Hedef platform: Linux.

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

## Kullanım

```bash
PYTHONPATH=. .venv/bin/python -m tom --deepspeed                 # mikrofon + hoparlör
PYTHONPATH=. .venv/bin/python -m tom --deepspeed --llm gemma4:e4b --silence-ms 400
PYTHONPATH=. .venv/bin/python -m tom --input-wav soru.wav --output-wav cevap.wav   # deneme
```

Asistan konuşurken mikrofon dinlenmez (yankı iptali yok). Kulaklıkla `--barge-in` araya girmeye izin verir.
Varsayılanlar: XTTS `~/.local/share/tts/...xtts_v2`, klon referansı `~/Downloads/optimized_model/reference.wav`
(`--xtts`, `--ref` ile değişir), STT `large-v3-turbo` (GPU, int8), LLM `gemma4:e2b`.

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
