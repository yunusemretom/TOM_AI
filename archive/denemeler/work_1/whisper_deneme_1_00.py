import pyaudio
import numpy as np
import wave
from pydub import AudioSegment
import os
import whisper
import time
from rich_deneme import print

def record():
    # PyAudio ayarları
    chunk = 4096  # Ses parçası boyutu: 2048 örn.
    sample_format = pyaudio.paInt16  # Ses formatı
    channels = 1  # Mono ses
    fs = 16000  # Örnekleme frekansı
    record_seconds = 5  # Kayıt süresi (saniye)
    output_wav_file = "output.wav"  # Geçici olarak kaydedilecek WAV dosyası
    output_mp3_file = "output.mp3"  # Kaydedilecek MP3 dosyası

    # PyAudio başlat
    p = pyaudio.PyAudio()
    stream = p.open(format=sample_format, channels=channels, rate=fs, input=True, frames_per_buffer=chunk)
    print("Mikrofon dinleniyor...",color="blue")

    # WAV dosyası oluştur
    wf = wave.open(output_wav_file, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(sample_format))
    wf.setframerate(fs)

    print(f"{record_seconds} saniye boyunca kayıt yapılıyor...",color="blue")

    # Belirtilen süre boyunca ses kaydı
    for _ in range(0, int(fs / chunk * record_seconds)):
        data = stream.read(chunk)
        wf.writeframes(data)

    # Kayıt bitti
    print("Kayıt tamamlandı.",color="blue")

    # Akışı kapat
    stream.stop_stream()
    stream.close()
    p.terminate()

    # WAV dosyasını kapat
    wf.close()

    # WAV dosyasını MP3 formatına çevir
    audio = AudioSegment.from_wav(output_wav_file)
    audio.export(output_mp3_file, format="mp3")
    print(f"WAV dosyası MP3 formatına dönüştürüldü: {output_mp3_file}",color="blue")

    # WAV dosyasını sil (isteğe bağlı)
    #os.remove(output_wav_file)
    #print(f"{output_wav_file} dosyası silindi.")
    return output_mp3_file


def transcript():
    record()
    model = whisper.load_model("small")

    """
    #ayrı bir deneme için
    # load audio and pad/trim it to fit 30 seconds
    audio = whisper.load_audio(mp3file)
    audio = whisper.pad_or_trim(audio)

    # make log-Mel spectrogram and move to the same device as the model
    mel = whisper.log_mel_spectrogram(audio).to(model.device)

    # detect the spoken language
    _, probs = model.detect_language(mel)
    print(f"Detected language: {max(probs, key=probs.get)}")

    # decode the audio
    options = whisper.DecodingOptions()
    result = whisper.decode(model, mel, options)
    """
    
    result = model.transcribe("output.mp3", language="tr")  # Dil olarak Türkçeyi ayarlıyoruz

    return result["text"]

