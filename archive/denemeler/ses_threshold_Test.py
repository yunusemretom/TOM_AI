import pyaudio
import numpy as np

def test_threshold():
    chunk = 4096
    sample_format = pyaudio.paInt16
    channels = 1
    fs = 16000

    p = pyaudio.PyAudio()
    stream = p.open(format=sample_format, channels=channels, rate=fs, input=True, frames_per_buffer=chunk)

    print("Mikrofon dinleniyor...")

    while True:
        data = stream.read(chunk)
        audio_data = np.frombuffer(data, dtype=np.int16)
        audio_volume = np.linalg.norm(audio_data)
        print(f"Ses seviyesi: {audio_volume}")  # Ses seviyesini gösterir

    stream.stop_stream()
    stream.close()
    p.terminate()

test_threshold()
