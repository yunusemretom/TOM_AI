# TOM nasıl çalışır?

Bu belge TOM'un baştan sona nasıl çalıştığını, kodun nerede durduğunu ve **sesi kendin nasıl
değiştirebileceğini** anlatır. Kısa bir özet:

> TOM, bilgisayarında internete ihtiyaç duymadan çalışan Türkçe bir sesli asistan. Seni mikrofondan duyar
> (Silero VAD + Whisper), ne istediğini anlar (önce kural tabanlı hızlı komutlar, olmazsa Gemma 4 + araçlar)
> ve fine-tune edilmiş bir XTTS v2 klon sesiyle cevap verir. İnternete yalnızca sen bir şey arattığında çıkar.

---

## 1. Bir konuşmanın yolculuğu

```
 mikrofon ──▶ VAD ──▶ Whisper ──▶ "Hey TOM" kapısı ──▶ hızlı komut? ──evet──▶ anında cevap (0,2 sn)
 (16 kHz)   konuşma   metin      (uyku / sohbet        │                      saat, hava, ses, parlaklık…
            bitti mi?            penceresi / video)    hayır
                                                       ▼
                                          Gemma 4 e4b (Ollama) ──araç gerekirse──▶ web, hatırlatıcı, YouTube…
                                                       │  ◀────── araç sonucu ───────┘
                                                       ▼ cevap kelime kelime akar
                                           cümle bölücü ──▶ XTTS (klon ses, akışlı) ──▶ hoparlör
```

Adım adım, gerçek bir örnekle ("Hey TOM, Euro kaç lira?"):

| Adım | Ne olur | Süre | Kod |
|---|---|---|---|
| 1. Dinleme | Mikrofon 32 ms'lik parçalar halinde okunur | sürekli | `tom/audio/io.py` → `MicStream` |
| 2. Konuşma algılama | Silero VAD her parçaya "konuşma var mı" der; 0,6 sn sessizlik = cümle bitti | ~0 | `tom/audio/vad.py` → `Endpointer` |
| 3. Yazıya dökme | Whisper large-v3-turbo (GPU, int8) | ~0,3 sn | `tom/listener/whisper_stt.py` |
| 4. Uyandırma kapısı | "Hey TOM" var mı, sohbet penceresi açık mı, video çalıyor mu | ~0 | `tom/wake.py` |
| 5. Hızlı komut | Düzenli ifadelerle saat, ses, parlaklık… yakalanır; yakalanırsa LLM'e hiç gidilmez | ~0 | `tom/skills/` |
| 6. LLM + araç | Gemma 4 `doviz` aracını çağırır → "Bir bakayım." çalar → kur alınır → cevap yazılır | 1–4 sn | `tom/brain/agent.py`, `tom/tools/` |
| 7. Cümle bölme | Akan metin cümlelere bölünür, ilk cümle beklemeden sese gider | ~0 | `tom/brain/sentence_splitter.py` |
| 8. Ses | XTTS klon sesi parça parça üretir (RTF ~0,25: 4 sn ses ~1 sn'de) | ilk ses ~0,2 sn | `tom/voice/xtts_engine.py` |
| 9. Çalma | Parçalar sırayla hoparlöre gider; TOM konuşurken yalnız "sus/uyu" dinlenir | — | `tom/audio/io.py` → `Player` |

Hepsini birbirine bağlayan döngü `tom/app.py` içindeki `Assistant` sınıfıdır (`run()` → `answer()` → `respond_text()`).
Programın girişi ve modellerin yüklenmesi `tom/__main__.py` (`build()` ve `main()`).

---

## 2. Klasör haritası

```
TOM_AI/
├── tom/                      ← asistanın kendisi
│   ├── __main__.py           giriş: ayarları okur, modelleri yükler (XTTS → Whisper → LLM), döngüyü başlatır
│   ├── app.py                Assistant: dinle → anla → konuş döngüsü, geçmiş, uyku/uyandırma, susturma
│   ├── wake.py               "Hey TOM", sohbet penceresi, uyku, "sus" komutları
│   ├── audio/  io.py         mikrofon ve hoparlör (sounddevice)
│   │           vad.py        Silero VAD + konuşma başı/sonu algılama
│   ├── listener/whisper_stt.py   faster-whisper; halüsinasyon/tekrar süzgeci
│   ├── brain/  agent.py      araçlı ajan (LLM ↔ araç döngüsü, bozuk çağrı kurtarma)
│   │           ollama_client.py  Ollama'ya akışlı istek (metin + araç çağrıları)
│   │           persona.py    kişilik → sistem istemi; açılış selamı
│   │           sentence_splitter.py  akan metni cümlelere böler, markdown/emoji/kalıp kapanışları atar
│   ├── pipeline/respond.py   LLM akışı ile TTS'i paralel çalıştırır (iki thread), süreleri ölçer
│   ├── skills/               hızlı komutlar (LLM'siz): saat, hava, zamanlayıcı, medya, parlaklık, cihazlar
│   │   ├── router.py         cümleyi parçalara böler ("ve", "sonra da"), komutları eşleştirir
│   │   └── builtin.py        komutların kendisi
│   ├── tools/                LLM'in çağırdığı araçlar
│   │   ├── registry.py       araç listesi ve modelin gördüğü açıklamalar
│   │   ├── web.py            arama (ddgs), sayfa okuma (trafilatura), haberler
│   │   ├── info.py           hesap, döviz, hava tahmini
│   │   ├── memory.py         hafıza, notlar, hatırlatıcılar (data/hafiza.json)
│   │   └── pc.py             uygulama/site/YouTube açma, ses, parlaklık, sistem durumu, masaüstü bildirimi
│   └── voice/                SES (aşağıda ayrıntılı)
│       ├── settings.py       config/ses.yaml'ı okur
│       ├── xtts_engine.py    XTTS v2 motoru: yükleme, klon ses, akışlı üretim
│       ├── speaker_cache.py  referans ses analizini diske kaydeder (her açılışta yeniden yapılmaz)
│       ├── phrase_cache.py   sabit cümlelerin ("Tamam.", "Bir bakayım.") sesleri önceden üretilir
│       └── text_prep.py      TTS'e gitmeden metin düzeltmesi (sondaki noktayı atar)
├── config/
│   ├── kisilik.yaml          hitap, şehir, kişilik metni (git dışı; örneği kisilik.example.yaml)
│   └── ses.yaml              SESİN BÜTÜN AYARLARI (git dışı; örneği ses.example.yaml)
├── models/                   git dışı: xtts_ince_test1/2 (fine-tune modeller), voices/ (klipler + önbellek)
├── data/                     git dışı: hafiza.json (bilgiler, notlar, hatırlatıcılar), son_konusma.json
├── tools/                    yardımcı araçlar: ses_dene.py, ölçüm betikleri, finetune/ (veri seti + Colab)
├── tests/                    187 test (PYTHONPATH=. .venv/bin/python -m pytest -q tests)
└── docs/                     bu belge
```

---

## 3. Ses nasıl üretiliyor?

TOM'un sesi **XTTS v2** ile üretilir. XTTS iki şeyi birleştirir:

1. **Model** (`models/xtts_ince_test1/model.pth`): Türkçe konuşmayı bilen sinir ağı. Senin fine-tune ettiğin
   model test1 konuşmacısının kayıtlarıyla ek eğitim gördü; Türkçe telaffuzu orijinal XTTS'ten daha iyi.
2. **Referans klipler** (`models/voices/ugur/ref_*.wav`): "Bu kişi gibi konuş" örneği. XTTS bu kliplerden
   kişinin ses rengini çıkarır (iki vektör: `gpt_cond_latent` ve `speaker_embedding`). Buna **klonlama** denir.

Yani: **model nasıl konuşulacağını, referans kimin sesiyle konuşulacağını belirler.** Sesin
"istediğin gibi olmaması" çoğu zaman referans kliplerden gelir (boğukluk, yankı, tonlama), ince ayarlar
(hız, sıcaklık) ise doğallığı değiştirir.

Hız için yapılanlar (değiştirmen gerekmez, bilmen yeter):
- **Referans önbelleği:** klip analizi bir kez yapılır, `models/voices/<ad>-<özet>.pt` olarak saklanır.
  Klipleri ya da modeli değiştirince özet değişir ve analiz kendiliğinden yeniden yapılır.
- **Akışlı üretim:** cümlenin tamamı beklenmez, ilk ~0,2 sn'lik parça hazır olunca çalmaya başlar.
- **DeepSpeed:** `--deepspeed` ile XTTS'in GPT kısmı ~2 kat hızlanır.
- **Hazır cümleler:** "Tamam.", "Bir bakayım.", selamlar… açılışta bir kez üretilip saklanır, anında çalar.
  Ses ayarlarını değiştirince bunlar da kendiliğinden yeniden üretilir.
- **Cümle sonu noktası atılır:** XTTS noktada hemen susmayıp 1 sn'ye varan anlamsız ses üretiyordu
  (`tom/voice/text_prep.py`).

---

## 4. Sesi kendin değiştirmek

### 4.1 Tek dosya: `config/ses.yaml`

```yaml
model: models/xtts_ince_test1
referans:
  - models/voices/ugur/ref_1.wav
  - models/voices/ugur/ref_2.wav
  - models/voices/ugur/ref_3.wav
hiz: 1.0
sicaklik: 0.75
top_p: 0.85
top_k: 50
tekrar_cezasi: 5.0
```

| Ayar | Ne yapar | Ne zaman değiştir |
|---|---|---|
| `model` | Hangi XTTS: `xtts_ince_test1` (şu anki), `xtts_ince_test2` (53 dk veri, daha genel), orijinal XTTS | Telaffuz ya da ses rengi hiç olmuyorsa |
| `referans` | Klonlanacak ses (1-5 klip) | Sesin rengi, boğukluğu, tonu |
| `hiz` | 0,85 yavaş · 1,0 normal · 1,2 hızlı | Çok yavaş/hızlı konuşuyorsa |
| `sicaklik` | 0,3 düz, kararlı, robotik · 0,75 doğal · 0,9 canlı ama arada hata | Ses monotonsa artır, garip vurgular/sesler varsa azalt |
| `top_p` | Düşük = daha güvenli seçimler | Arada tuhaf heceler çıkıyorsa 0,7'ye indir |
| `tekrar_cezasi` | Yüksek = takılma/tekrar azalır | Kelime tekrarı ya da uzatma varsa artır (en fazla ~10) |

**İş akışı:** dosyayı düzenle → dene → beğenince TOM'u yeniden başlat.

```bash
PYTHONPATH=. .venv/bin/python tools/ses_dene.py                         # ses.yaml ile 4 örnek cümle
PYTHONPATH=. .venv/bin/python tools/ses_dene.py --hiz 0.92 --sicaklik 0.6 --cal   # dosyaya dokunmadan dene, çal
PYTHONPATH=. .venv/bin/python tools/ses_dene.py --ref yeni_klip.wav --cumle "Merhaba Yunus."
```

Çıktılar `logs/ses_dene/<saat>_<n>.wav` olarak kalır; farklı denemeleri yan yana dinleyebilirsin.
TOM açıkken GPU yetmeyebilir: önce TOM'u kapat ya da `--cihaz cpu` ver (yavaş ama çalışır).

### 4.2 Referans klipleri değiştirmek (sesin rengi için en etkili yol)

İyi bir referans klip:
- **Tek kişi**, müziksiz, yankısız, gürültüsüz; mikrofon yakın.
- **6-12 sn**; toplam 20-40 sn olacak şekilde 2-4 klip. Farklı cümleler, doğal tonlama.
- **İstediğin konuşma tarzında:** sakin bir asistan istiyorsan sakin anlatım; heyecanlı bir podcast parçası
  verirsen TOM da heyecanlı konuşur.
- 22-24 kHz ya da üstü wav (mp3'ten dönüştürmek de olur).

Bir kayıttan klip kesmek:

```bash
# 1:05'ten başlayan 10 sn'lik parça, mono 24 kHz
ffmpeg -ss 65 -t 10 -i kayit.mp3 -ac 1 -ar 24000 models/voices/yeni/ref_1.wav
```

Uzun bir kayıttan otomatik temiz klip çıkarmak (en iyi cümleleri seçer, başka konuşmacıları atar):

```bash
PYTHONPATH=. .venv/bin/python -m tools.finetune.build_dataset kayit.mp3 --out data/yeni_ses --no-verify
# en uzun 3 klibi referans yap:
ls -S data/yeni_ses/wavs | head -3
```

**Boğuk ses** düzeltmesi (Uğur kliplerine yaptığımız gibi): tizleri artıran bir EQ filtresi.
Kullandığımız filtre `models/voices/ugur/filtre.txt` içinde:

```bash
F="highpass=f=70,equalizer=f=250:t=o:w=1.2:g=-2,equalizer=f=3200:t=o:w=1.6:g=11,equalizer=f=6500:t=o:w=1.0:g=0,highshelf=f=8500:g=8,alimiter=limit=0.9"
ffmpeg -i ham.wav -af "$F" models/voices/yeni/ref_1.wav
```

- `equalizer=f=3200 … g=11` → netlik (konuşmanın anlaşılırlığı). Hâlâ boğuksa 13-14, cırtlaksa 7-8.
- `highshelf=f=8500:g=8` → parlaklık/hava. Cızırtılıysa düşür.
- `equalizer=f=250 … g=-2` → "kutu içinden" sesi azaltır.

Sonra `config/ses.yaml`'da `referans:` listesini yeni kliplerle değiştir.

### 4.3 Modeli değiştirmek

- `models/xtts_ince_test2`: daha fazla veriyle eğitildi, başka seslere de uyumlu (Uğur sesinde benzerlik
  daha yüksekti). Telaffuz test1'de sana daha iyi gelmişti.
- Orijinal XTTS: `~/.local/share/tts/tts_models--multilingual--multi-dataset--xtts_v2`.

### 4.4 Kendi sesini ya da başka bir sesi kalıcı öğretmek (fine-tune)

Referans klip sesi "taklit ettirir"; fine-tune ise modele o sesi **öğretir** (daha tutarlı, daha benzer).
Adımlar README'nin "XTTS fine-tune" bölümünde; kısaca:

1. 20-60 dk temiz kayıt (podcast, kendi okumaların).
2. `python -m tools.finetune.build_dataset kayitlar/ --ref ornek.wav --out data/xtts_dataset --zip`
3. Colab A100'de `tools/finetune/XTTS_FineTune_Colab.ipynb` (ya da Colab CLI ile; ~10-15 dk eğitim).
4. İnen `hazir_model` klasörünü `models/xtts_ince_<ad>/` yap ve `ses.yaml`'da `model:` olarak ver.

### 4.5 Tamamen başka bir ses motoru

Telefonda kullandığımız **Piper** (fahrettin/fettah/dfki) çok temiz ve hızlı ama klon değil.
Bilgisayarda da kullanılabilir; istersen `tom/voice/` altına `PiperEngine` eklenir (XttsEngine ile aynı
`stream()` / `synthesize()` arayüzü yeterli).

---

## 5. Beyin: hızlı komutlar, LLM ve araçlar

### 5.1 Hızlı komutlar (`tom/skills/`)

Düzenli ifadelerle eşleşen istekler LLM'e gitmeden ~0,2 sn'de yapılır: saat/tarih, kendi şehrinin
havası, zamanlayıcı, müzik/video, ses, sustur, parlaklık. Bir cümlede birden çok komut olabilir
("saat kaç, bir de sesi kıs"); komut olmayan kısım LLM'e gider.

Yeni komut eklemek: `builtin.py`'de bir `Skill` sınıfı yaz (`rules` + `run`), `default_skills()` listesine ekle.

### 5.2 LLM ve araçlar (`tom/brain/agent.py`, `tom/tools/`)

- Model: **gemma4:e4b** (Ollama, Q4_K_M). 6 GB kartta XTTS + Whisper ~3,2 GB tuttuğu için modelin
  26 katmanı GPU'da, kalanı işlemcide (`--llm-gpu-layers`). Daha hızlı ama daha zayıf: `--llm gemma4:e2b`.
- Model aracın adını ve parametrelerini yazar; ajan aracı çalıştırır, sonucu modele geri verir, model
  cevabı yazar. En fazla 3 tur.
- **Gemma 4 sorunları ve çözümleri:** `think=False` (hızlı mod) araç çağırmayı ~%30 bozuyor:
  - Çağrı ham metin olarak gelirse (`web_ara(sorgu="…")`) ajan kendisi çözer, **asla seslendirmez**.
  - Eylem isteğinde (hatırlat, aç, ses…) model aracı atlarsa: parametresiz araç doğrudan çağrılır,
    yoksa aracın adı söylenerek yeniden sorulur; model yapmadığı işi "yaptım" diyorsa son çare düşünme modu.
  - Bunun için cümlede eylem kalıbı aranır (`_HINTS` listesi); olumsuz cümlelerde ("istemiyorum") aranmaz.

Yeni araç eklemek: bir Python fonksiyonu yaz (metin döndürsün), `tom/tools/registry.py`'de
`Tool("ad", "açıklama", {"param": {...}}, ["zorunlu"], fonksiyon)` olarak ekle. Açıklamayı kısa ve net yaz:
model aracı ona bakarak seçer.

### 5.3 Kişilik ve hafıza

- `config/kisilik.yaml`: hitap ("Yunus"), şehir, kişilik metni, konuşma kuralları → sistem istemine girer.
- `data/hafiza.json`: "bunu hatırla" dediklerin (sistem istemine girer), notlar, hatırlatıcılar.
  Hatırlatıcılar arka planda izlenir; TOM kapalıyken kaçanlar açılışta söylenir.

---

### 5.4 Derin araştırma (`tom/research.py`)

Pencerede **Derin** düğmesini açıp soruyu yaz: TOM 4 farklı arama sorgusu planlar, ~8 sayfayı okur, her sayfadan
soruyla ilgili somut notlar çıkarır (ilgisizleri atar) ve kaynak numaralı bir rapor yazar (~2 dk). Rapor pencerede
biçimli görünür, `data/arastirmalar/` altına Markdown olarak kaydedilir ("📄 Raporu aç"), özeti sesli söylenir.
Araştırma sürerken sesli asistan çalışmaya devam eder. Asistanla aynı LLM ayarları kullanılır (model yeniden yüklenmez).

### 5.5 Yazılı sohbet: API + Open WebUI (`tom/api.py`)

`tom/api.py` küçük bir aiohttp sunucusu (127.0.0.1:8800). OpenAI'nin `/v1/models` ve `/v1/chat/completions` (akışlı
SSE) uçlarını taklit eder; böylece Open WebUI (ya da OpenAI uyumlu herhangi bir istemci) TOM'u bir model gibi görür.

- **tom** modeli: her istekte sohbet geçmişinin son 16 mesajı + `Persona.chat_prompt()` (sesli istemin yazılı hâli:
  kısa cevap şartı yok, Markdown serbest, kaynak göster) ile sesli TOM'daki `Agent` çalışır. Araç ipuçları ve
  kurtarma mantığı aynı; sesli dolgular ("Bir bakayım.") atılır, çağrılan araçlar alıntı satırı olarak akar.
  Open WebUI'deki sohbet sistem istemi varsa TOM'un istemine eklenir.
- **tom-derin**: `DeepResearch` aynen; ilerleme adımları alıntı satırı, ardından rapor ve kaynak listesi.
- Open WebUI'nin başlık / etiket / takip sorusu üretme istekleri (`### Task:` ile başlar) araçsız, doğrudan
  modele gider: hızlıdır ve hafızaya karışmaz.
- Model ayarı: sesli TOM çalışıyorsa (`pgrep`) onunla birebir aynı (`num_ctx 4096, num_gpu 26`) — farklı ayar
  Ollama'da modeli yeniden yükletir ve GPU'yu taşırırdı. Sesli TOM kapalıysa `num_ctx 8192`, katmanları Ollama seçer.
- Hafıza iki süreçte ortak: `Memory` her işlemde dosyayı (değiştiyse) yeniden okur ve `data/hafiza.lock` ile
  süreçler arası kilitler; biri ötekinin yazdığını ezmez.
- İsteğe bağlı anahtar: `TOM_API_KEY=… scripts/tom-api.sh` (Open WebUI'ye de aynı değişkenle verilir).

Open WebUI `scripts/openwebui.sh` ile Docker'da çalışır (host ağı, yalnız 127.0.0.1:3000, girişsiz, telemetri kapalı).
Bağlantılar ortam değişkeniyle hazır gelir: Ollama `127.0.0.1:11434`, TOM `127.0.0.1:8800/v1`. Arayüzden
Ayarlar → Bağlantılar'da da görülür/değiştirilir.

## 6. Uyandırma, uyku, susturma (`tom/wake.py`)

- **"Hey TOM"** ile başlayan cümleler dinlenir; cevaptan sonra 40 sn "Hey TOM" gerekmez (`--wake-window`).
- **Video/müzik çalarken** (MPRIS üzerinden bakılır) pencere kapalı: her cümlede "Hey TOM" gerekir.
- **Uyku:** "uyu" ya da 10 dk sessizlik (`--idle-sleep`) → Gemma 4 bellekten çıkarılır; Whisper ve ses açık
  kalır. "Hey TOM" → "Buradayım", LLM arkada yeniden yüklenir.
- **Konuşurken susturma:** TOM konuşurken mikrofon 2,5 sn'lik parçalarla dinlenir; "sus / sessiz ol / yeter
  / dur / uyu" duyulursa çalma kesilir. TOM'un kendi sesi mikrofona girdiği için, duyulan kelime TOM'un o an
  söylediği metinde de geçiyorsa yok sayılır.
- Kapatmak için: `--no-wake`.

---

## 7. Bellek (GPU) ve dayanıklılık

- Yükleme sırası önemli: **XTTS → Whisper → LLM** (önce torch modelleri, en son Ollama).
- Her cevaptan sonra `torch.cuda.empty_cache()`: XTTS'in ayırıp bıraktığı bellek Whisper'a kalır
  (önceden bir süre sonra Whisper "out of memory" veriyordu).
- Bellek hatasında önce boşaltıp yeniden denenir; olmazsa TOM **kendini yeniden başlatır**, son konuşmayı
  `data/son_konusma.json`'dan geri yükler ve "Kısa bir aksaklık oldu, yeniden başladım" der.
  10 dk'da 3'ten fazla çökerse döngüye girmemek için durur.

---

## 8. Komutlar

```bash
# Normal kullanım
PYTHONPATH=. .venv/bin/python -m tom --deepspeed
PYTHONPATH=. .venv/bin/python -m tom --deepspeed --llm gemma4:e2b       # daha hızlı LLM
PYTHONPATH=. .venv/bin/python -m tom --deepspeed --no-wake              # Hey TOM olmadan

# Deneme (mikrofonsuz)
PYTHONPATH=. .venv/bin/python -m tom --deepspeed --text "Saat kaç?" "Euro kaç lira?" --output-wav cevap.wav

# Ses
PYTHONPATH=. .venv/bin/python tools/ses_dene.py --cal

# Yazılı sohbet (Open WebUI)
scripts/tom-sohbet.sh

# Testler
PYTHONPATH=. .venv/bin/python -m pytest -q tests
```

`PYTHONPATH=.` şart: kabuktaki ROS ayarı pytest'i bozuyor. DeepSpeed için CUDA 12.4 (`CUDA_HOME`) gerekir;
`--deepspeed` bunu kendisi ayarlar.

---

## 9. Telefon tarafı (`feat/mobil` dalı)

Bu dalda değil, `feat/mobil` dalında: bilgisayardaki TOM'a telefondan bağlanan PWA (`tom/server.py`) ve
tamamen telefonda çalışan Android uygulaması (`mobile/android/`). Telefonda LLM çok yavaş olduğu için
uygulama şu an **TOM Not** (toplantıyı Whisper ile yazıya dökme) olarak açılıyor.

---

## 10. Bilinen sınırlar

- Yankı iptali yok: hoparlörle kullanırken TOM kendi sesini duyabilir (susturma metin karşılaştırmasıyla
  korunuyor). Kulaklık en iyisi.
- Araçlı cevaplarda ilk ses 2-4 sn (model aracı seçerken). Web araması 3-6 sn.
- Gemma 4 e4b'nin bir kısmı işlemcide çalıştığı için cevaplar e2b'den yavaş.
- Takvim ve e-posta yok (hesap bağlantısı gerekir).
