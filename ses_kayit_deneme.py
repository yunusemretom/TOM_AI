import pyaudio
import numpy as np
import soundfile as sf
import time

# Ses kaydı ve işleme için parametreler
CHUNK = 1024  # Her veri bloğu boyutu
FORMAT = pyaudio.paInt16  # Veri formatı
CHANNELS = 1  # Mono kanal
RATE = 44100  # Örnekleme oranı
THRESHOLD = 1000  # Eşik değerini artırdık
MIN_RECORD_SECONDS = 1  # Minimum kayıt süresi

# Pyaudio ile ses akışı başlatma
p = pyaudio.PyAudio()

stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

print("Ses algılanıyor...")


frames = []  # Kaydedilecek ses verileri
recording = False  # Ses kaydediliyor mu?
silent_chunks = 0
MAX_SILENT_CHUNKS = 50  # Yaklaşık 1 saniye sessizlik

try:
    while True:
        # Ses verilerini oku
        data = stream.read(CHUNK)
        audio_data = np.frombuffer(data, dtype=np.int16)

        # Desibel seviyesini hesapla (kök ortalama kare yöntemi - RMS)
        rms = np.sqrt(np.mean(np.square(audio_data)))
        
        if rms > THRESHOLD:
            silent_chunks = 0
            if not recording:
                print("Ses kaydediliyor...")
                recording = True
                frames = []
            frames.append(data)  # Veriyi kaydet
        elif recording:
            silent_chunks += 1
            frames.append(data)

            if silent_chunks >= MAX_SILENT_CHUNKS:
                if len(frames) > (RATE / CHUNK * MIN_RECORD_SECONDS):
                    print("Sessizlik algılandı, kaydedilen dosya kaydediliyor...")
                    # Ses kaydını dosyaya kaydet
                    filename = f"ses_kaydi_{int(time.time())}.wav"
                    sf.write(filename, np.frombuffer(b''.join(frames), dtype=np.int16), RATE)
                    print(f"Ses kaydı dosyası: {filename}")
                else:
                    print("Kayıt çok kısa, göz ardı ediliyor.")
                recording = False
                frames = []
                silent_chunks = 0

except KeyboardInterrupt:
    print("Kayıt durduruldu.")
finally:
    stream.stop_stream()
    stream.close()
    p.terminate()
