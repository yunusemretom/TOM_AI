from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM
import fasterWhisper_deneme as stt
import ses_klonlama_2_00 as tts
from play_soundfile_deneme import play_sound
import os
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

# Model yollarını global olarak tanımla
model_path = r"C:\Users\TOM\Documents\Projeler\Ses_fine_tune\xtts-finetune-webui\finetune_models\ready\model.pth"
config_path = r"C:\Users\TOM\Documents\Projeler\Ses_fine_tune\xtts-finetune-webui\finetune_models\ready\config.json" 
vocab_path = r"C:\Users\TOM\Documents\Projeler\Ses_fine_tune\xtts-finetune-webui\finetune_models\ready\vocab.json"
speaker_path = r"C:\Users\TOM\Documents\Projeler\Ses_fine_tune\xtts-finetune-webui\finetune_models\ready\speakers_xtts.pth"
speaker_audio = "./ugur_t.mp3"

# Modeli ve şablonu başlangıçta yükle
model = tts.load_model(model_path, config_path, vocab_path, speaker_path)
llm_model = OllamaLLM(model="mistral")

# Komut şablonunu önceden oluştur
template = """
Aşağıdaki cümlede bir komut var mı analiz et. Eğer komut veya komuta yakın bir cümle varsa komut numarasını döndür.
Komut cümleleri genelikle soru cümleleri oluyor. buradaki komutları algıla ve komut numarasını döndür.
Eğer komut yoksa "None" döndür ve cevap kısmını soruda komut olmayan kısmının cevabını döndür. 
Eğer özel bir soru yoksa cevap kısmını da boş bırak.

Komut Listesi: {commands}
Cümle: {question}

Dönüş:
- "Komut Numarası": Tespit edilen komut numarası (eğer yoksa "None").
- "Cevap": Kullanıcının sorusuna uygun bir cevap.
"""

prompt = ChatPromptTemplate.from_template(template)

# Komutları önceden tanımla
commands_dict = {
    "ışıkları aç": 1,
    "ışıkları kapat": 2, 
    "klimayı aç": 3,
    "klimayı kapat": 4,
    "tv aç": 5,
    "tv kapat": 6,
}

def ses_olustur(text):
    if not text:
        return
        
    if not os.path.exists(speaker_audio):
        raise FileNotFoundError(f"Speaker audio file bulunamadı: {speaker_audio}")

    output_audio_path = tts.run_tts(model, "tr", text, speaker_audio)
    play_sound(output_audio_path)

def yanit(question):
    chain = prompt | llm_model
    return chain.invoke({"question": question, "commands": commands_dict})


transcriber = stt.AudioTranscriber()
while True:
    
    try:
        metin = transcriber.process_audio()
        if metin and len(metin) > 0:  # metin listesi boş değilse
            son_metin = metin[-1]  # listenin son elemanını al
            print("Gelen veri:", son_metin)
            responsive = yanit(son_metin)
            print("gelen yanit:", responsive)
            
            cevap_kismi = responsive.split("Cevap", 1)[1] if "Cevap" in responsive else None
            if cevap_kismi:
                print(cevap_kismi)
                ses_olustur(cevap_kismi)
                
    except Exception as e:
        print(e)