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

## Ölçüm

```bash
export CUDA_HOME=/usr/local/cuda-12.4 PATH=/usr/local/cuda-12.4/bin:$PATH PYTHONPATH=.
XTTS=~/.local/share/tts/tts_models--multilingual--multi-dataset--xtts_v2
REF=~/Downloads/optimized_model/reference.wav
.venv/bin/python tools/tts_bench.py --model-dir $XTTS --ref $REF --deepspeed          # yalnız TTS
.venv/bin/python tools/pipeline_bench.py --llm gemma4:e2b --model-dir $XTTS --ref $REF --deepspeed --out logs/pipeline_bench
.venv/bin/python -m pytest -q tests
```

`PYTHONPATH=.` şart: kabuktaki ROS yolu pytest eklentilerini bozuyor.
