# models/

Model ağırlıkları burada durur ama git'e eklenmez. Önerilen düzen:

```
models/
├── xtts/            # XTTS v2 fine-tune: model.pth, config.json, vocab.json, speakers_xtts.pth
├── voices/          # Referans sesler (ör. ugur_t.mp3) ve önceden hesaplanmış konuşmacı latent'leri (.pt)
└── whisper/         # faster-whisper (CTranslate2) modelleri, indirilirse
```

Ollama modelleri Ollama'nın kendi dizininde durur, buraya kopyalanmaz.
