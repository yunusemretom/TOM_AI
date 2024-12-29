import torch
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", category=FutureWarning)

def main():
    # Model yolları
    model_paths = {
        "model": Path("path/to/model.pth"),
        "config": Path("path/to/config.json"),
        "vocab": Path("path/to/vocab.json"),
        "speaker": Path("path/to/speakers_xtts.pth"),
        "speaker_audio": Path("./ugur_t.mp3")
    }

    # Handler'ları başlat
    stt_handler = OptimizedAudioTranscriber(model_size="medium")
    llm_handler = OptimizedLLMHandler()
    tts_handler = OptimizedTTSHandler(
        model_path=str(model_paths["model"]),
        config_path=str(model_paths["config"]),
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
