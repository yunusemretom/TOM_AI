import torch
from TTS.api import TTS
import pygame
from rich_deneme import print
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
# Cihazı ayarla (GPU varsa kullan, yoksa CPU kullan)
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

wav_packes = "./BarisOzcan3.wav"
output_file = "output.wav"

# Metni tanımla
text_deneme = """Bu, ses modelimi test etmek için hazırladığım bir metindir. 
Modelin her kelimeyi doğru bir şekilde seslendirdiğinden emin olmalıyım. 
Uzun cümleleri ve kısa ifadeleri aynı doğrulukta okumalıdır. 
Hızlıca konuşulan bölümler ile yavaşça ifade edilen kısımlar arasında fark olup olmadığını kontrol edeceğim. 
Ayrıca, vurguların ve tonlamaların doğru olup olmadığını anlamak için farklı cümle yapılarını dinlemeliyim. 
Teknoloji her geçen gün gelişiyor ve ben de bu gelişmelere ayak uyduruyorum. 
Ses modelim bu metni sorunsuz bir şekilde okuyabiliyorsa, başarılı demektir."""

text_deneme2 ="""
Hello, I am reading this text for voice analysis and testing. 
I need to speak in different tones and speeds to ensure that the voice is recorded clearly and accurately. 
Throughout the day, we encounter different words and sentences. 
This test is to check whether my voice can correctly interpret all kinds of words. 
Now, let's go over a few short sentences: The weather is very nice today. I turned on my computer and started working.
Now, let's move on to longer and more complex sentences: 
Technology plays a big role in human life, so it is very important to keep up with new technologies. 
If this text is being read clearly, it means the voice model is working successfully.
"""

# Init TTS
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)


def speak(text):
    tts.tts_to_file(text=text, speaker_wav=wav_packes, language="tr", file_path="output.wav")
    print(f"Ses üretimi tamamlandı ve {output_file} dosyasına kaydedildi.")
    pygame.init()
    pygame.mixer.init()
    music = pygame.mixer.Sound("output.wav")
    channel2 = pygame.mixer.Channel(0)
    music.set_volume(0.3)
    
    channel2.play(music)

    while channel2.get_busy():
        pygame.time.Clock().tick(10)


if __name__ == "__main__":
    speak(text_deneme)