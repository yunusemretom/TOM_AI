from TTS.api import TTS
import torch

# Get device
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# GPU desteğiyle TTS modelini başlat
tts = TTS("tts_models/en/vctk/fast_pitch", progress_bar=False, gpu=False)

# Mevcut konuşmacıları listeleyin
speakers = tts.speakers
print(speakers)  # Konuşmacıları listelemek için

# Konuşmacı kimliği ekleyin
speaker = speakers[7]  # İstediğiniz konuşmacıyı seçin (örneğin 6. konuşmacıyı)

# GPU kullanarak ses üretimi yapmaya çalıştığınızda tüm işlemleri GPU'da gerçekleştirdiğinizden emin olun
# Text to speech to a file
tts.tts_to_file(text="Hello world!", speaker=speaker, file_path="output.wav")
