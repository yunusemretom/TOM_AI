"""Colab notebook'unu repodaki betiklerden üretir (kod tek yerde kalsın diye betikler gömülür).

    python tools/finetune/make_notebook.py   # → tools/finetune/XTTS_FineTune_Colab.ipynb
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).parent


def md(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip("\n").splitlines(keepends=True)}


def code(text: str) -> dict:
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": text.strip("\n").splitlines(keepends=True)}


def writefile(name: str) -> dict:
    return code(f"%%writefile /content/{name}\n" + (HERE / name).read_text(encoding="utf-8"))


CELLS = [
    md("""
# TOM: XTTS v2 Türkçe fine-tune (Colab, A100)

**Önce:** Çalışma zamanı → Çalışma zamanı türünü değiştir → **A100 GPU**.

1. Yerelde veri setini hazırla ve zip'le:
   `PYTHONPATH=. .venv/bin/python -m tools.finetune.build_dataset podcastlar/ --out data/xtts_dataset --zip`
2. `data/xtts_dataset.zip` dosyasını Drive'da **`MyDrive/TOM_AI/xtts_dataset.zip`** yoluna yükle.
3. Hücreleri sırayla çalıştır ("Tümünü çalıştır" da olur; oturum yeniden başlamaz).

Checkpoint'ler Drive'a yazılır: bağlantı koparsa `CONTINUE_PATH` ile kaldığın yerden sürdürebilirsin.
Sürümler yereldeki TOM ortamıyla aynıdır (Python 3.10, torch 2.6 cu124, coqui-tts 0.25.3, transformers 4.46.2);
farklı sürümle eğitilen checkpoint yerelde açılmayabilir.
"""),
    md("""
## 1. Kurulum (~3–5 dk)
Colab'ın Python'u (3.12+) coqui-tts 0.25.3'ü desteklemiyor. Bu yüzden `uv` ile ayrı bir **Python 3.10**
ortamı (`/content/venv`) kurulur; eğitim ve değerlendirme o ortamda çalışır. Colab'ın kendi Python'una
dokunulmaz, oturum yeniden başlamaz. Hücre tekrar çalıştırılırsa kurulumu atlar.
"""),
    code("""
import os
PY = '/content/venv/bin/python'
!nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
if not os.path.exists(PY):
    !pip -q install uv
    !uv venv /content/venv --python 3.10 -q
    !uv pip install -q --python {PY} torch==2.6.0 torchaudio==2.6.0 coqui-tts==0.25.3 transformers==4.46.2 "numpy<2" faster-whisper==1.2.1 speechbrain==1.0.3
!{PY} -c "import torch, transformers, TTS; print('torch', torch.__version__, '| CUDA:', torch.cuda.is_available(), '|', torch.cuda.get_device_name(0), '| transformers', transformers.__version__, '| coqui-tts', TTS.__version__)"
"""),
    md("## 2. Ayarlar ve Drive"),
    code("""
from google.colab import drive
drive.mount('/content/drive')

VERI = 'xtts_test2'   # Drive'daki zip'in adı (uzantısız): xtts_test2 ya da xtts_test1
DATASET_ZIP = f'/content/drive/MyDrive/TOM_AI/{VERI}.zip'
OUT_DIR = f'/content/drive/MyDrive/TOM_AI/xtts_runs_{VERI}'   # checkpoint ve hazır model buraya
DATASET_DIR = f'/content/dataset_{VERI}'

EPOCHS = 15        # 30–60 dk veri için 10–20; ~10 dk veride 25. En iyi checkpoint zaten saklanır
BATCH = 8          # A100 40 GB: 8, 80 GB: 16
GRAD_ACCUM = 1
LR = 5e-6
CONTINUE_PATH = '' # yarıda kalan eğitim: OUT_DIR/egitim/tom_xtts_tr-... klasörü
assert os.path.exists(DATASET_ZIP), f'{DATASET_ZIP} yok: zip\\'i Drive\\'da MyDrive/TOM_AI/ altına yükle'
"""),
    md("## 3. Veri setini aç ve kontrol et"),
    code("""
import os, zipfile, json
os.makedirs(DATASET_DIR, exist_ok=True)
zipfile.ZipFile(DATASET_ZIP).extractall(DATASET_DIR)
print(open(f'{DATASET_DIR}/rapor.json').read() if os.path.exists(f'{DATASET_DIR}/rapor.json') else '')
!head -4 {DATASET_DIR}/metadata_train.csv
"""),
    md("## 4. Betikler"),
    writefile("train_xtts.py"),
    writefile("eval_xtts.py"),
    md("## 5. Eğitim\nİlerlemeyi görmek için isteğe bağlı: `%load_ext tensorboard` ve `%tensorboard --logdir {OUT_DIR}/egitim`"),
    code("""
cont = f'--continue-path "{CONTINUE_PATH}"' if CONTINUE_PATH else ''
!cd /content && {PY} train_xtts.py --dataset {DATASET_DIR} --out {OUT_DIR} --epochs {EPOCHS} \\
    --batch {BATCH} --grad-accum {GRAD_ACCUM} --lr {LR} --workers 8 {cont}
"""),
    md("## 6. Değerlendirme: temel model ve fine-tune edilmiş model aynı cümleleri okur"),
    code("""
!cd /content && {PY} eval_xtts.py --models temel=/content/xtts_base ince={OUT_DIR}/hazir_model \\
    --ref {OUT_DIR}/hazir_model/reference.wav --out {OUT_DIR}/degerlendirme
from IPython.display import Audio, display
for i in range(6):
    for name in ('temel', 'ince'):
        print(name, i); display(Audio(f'{OUT_DIR}/degerlendirme/{name}_{i}.wav'))
"""),
    md("""
## 7. İndir ve TOM'da kullan

`OUT_DIR/hazir_model` klasörünü (≈1,9 GB) Drive'dan indir, sonra yerelde:

```bash
PYTHONPATH=. .venv/bin/python -m tom --deepspeed --xtts ~/indirilen/hazir_model --ref ~/indirilen/hazir_model/reference.wav
```

Daha uzun bir referans istersen `--ref` ile veri setinden birkaç temiz klip verebilirsin.
"""),
    code("""
import shutil
shutil.make_archive('/content/hazir_model', 'zip', f'{OUT_DIR}/hazir_model')
from google.colab import files
files.download('/content/hazir_model.zip')   # ya da Drive'dan indir
"""),
]


def main():
    nb = {"cells": CELLS, "metadata": {"accelerator": "GPU", "colab": {"gpuType": "A100", "provenance": []},
                                       "kernelspec": {"display_name": "Python 3", "name": "python3"},
                                       "language_info": {"name": "python"}},
          "nbformat": 4, "nbformat_minor": 0}
    out = HERE / "XTTS_FineTune_Colab.ipynb"
    out.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
