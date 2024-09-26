import torch
from TTS.api import TTS

# Cihazı ayarla (GPU varsa kullan, yoksa CPU kullan)
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# TTS modelini başlat ve cihaza taşı
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)

# Metni tanımla
text = """Bu, ses modelimi test etmek için hazırladığım bir metindir. 
Modelin her kelimeyi doğru bir şekilde seslendirdiğinden emin olmalıyım. 
Uzun cümleleri ve kısa ifadeleri aynı doğrulukta okumalıdır. 
Hızlıca konuşulan bölümler ile yavaşça ifade edilen kısımlar arasında fark olup olmadığını kontrol edeceğim. 
Ayrıca, vurguların ve tonlamaların doğru olup olmadığını anlamak için farklı cümle yapılarını dinlemeliyim. 
Teknoloji her geçen gün gelişiyor ve ben de bu gelişmelere ayak uyduruyorum. 
Ses modelim bu metni sorunsuz bir şekilde okuyabiliyorsa, başarılı demektir."""

# Eğitim sonrası modeli kaydetmek için fonksiyon
def save_model(model, file_path):
    torch.save(model.state_dict(), file_path)
    print(f"Model {file_path} olarak kaydedildi.")

# Kaydedilen modeli yüklemek için fonksiyon
def load_model(model, file_path, device):
    model.load_state_dict(torch.load(file_path))
    model.to(device)
    print(f"Model {file_path} dosyasından başarıyla yüklendi.")
    return model

# 1. Aşama: Ses üretmeden önce model eğitimini kaydet
model_save_path = "tts_model.pth"
save_model(tts, model_save_path)

# 2. Aşama: Kaydedilen modeli yükle
tts = load_model(TTS("tts_models/multilingual/multi-dataset/xtts_v2"), model_save_path, device)

# 3. Aşama: Metni seslendir ve dosyaya kaydet
wav_packes = "edit.wav"
output_file = "output.wav"
tts.tts_to_file(text=text, speaker_wav=wav_packes, language="tr", file_path=output_file)

print(f"Ses üretimi tamamlandı ve {output_file} dosyasına kaydedildi.")
