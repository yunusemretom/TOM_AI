import torch
import warnings
from pathlib import Path
from optimized_tts import OptimizedTTSHandler
from optimized_stt import OptimizedAudioTranscriber
from transformers import AutoModelForCausalLM, AutoTokenizer
warnings.filterwarnings("ignore", category=FutureWarning)

def main():
    # Model yolları
    model_paths = {
        "model": Path(r"C:\Users\TOM\Documents\Projeler\Ses_fine_tune\xtts-finetune-webui\finetune_models\ready\model.pth"),
        "config": Path(r"C:\Users\TOM\Documents\Projeler\Ses_fine_tune\xtts-finetune-webui\finetune_models\ready\config.json"),
        "vocab": Path(r"C:\Users\TOM\Documents\Projeler\Ses_fine_tune\xtts-finetune-webui\finetune_models\ready\vocab.json"),
        "speaker": Path(r"C:\Users\TOM\Documents\Projeler\Ses_fine_tune\xtts-finetune-webui\finetune_models\ready\speakers_xtts.pth"),
        "speaker_audio": Path("./ugur_t.mp3")
    }

    # Handler'ları başlat
    stt_handler = OptimizedAudioTranscriber(model_size="large")
    llm_handler = OptimizedLLMHandler()
    tts_handler = OptimizedTTSHandler(
        model_path=str(model_paths["model"]),
        config_path=str(model_paths["config"]),w
        vocab_path=str(model_paths["vocab"]),
        speaker_path=str(model_paths["speaker"])
    )

    # Komut sözlüğü
    commands = {
        "ışıkları aç": 1,
        "ışıkları kapat": 2,
        "klimayı aç": 3,
        "klimayı kapat": 4,
        "tv aç": 5,
        "tv kapat": 6
    }

    print("Sistem hazır, dinlemeye başlıyor...")

    while True:
        try:
            # Ses tanıma
            transcription = stt_handler.process_audio()
            if transcription and transcription[-1].strip():
                metin = transcription[-1]
                print(f"Algılanan metin: {metin}")

                # LLM işleme
                response = llm_handler.process(metin, commands)
                if response:
                    print(f"LLM yanıtı: {response}")
                    
                    # Ses üretimi
                    audio_path = tts_handler.generate_speech(
                        response,
                        "tr",
                        str(model_paths["speaker_audio"])
                    )
                    if audio_path:
                        start_sound(audio_path)

        except KeyboardInterrupt:
            print("\nProgram sonlandırılıyor...")
            break
        except Exception as e:
            print(f"Hata: {e}")
            continue

if __name__ == "__main__":
    main()
