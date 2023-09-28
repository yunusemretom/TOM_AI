import pyaudio
import wave
import multiprocessing as mp
import threading as th

# Ses kaydı için gerekli ayarlar
FORMAT = pyaudio.paInt16  # Ses formatı
CHANNELS = 1              # Tek kanal
RATE = 44100              # Örnekleme hızı (örneğin 44.1 kHz)
CHUNK = 1024              # Ses bloğunun boyutu

RECORD_SECONDS = 10        # Kaydedilecek süre
OUTPUT_FILENAME = "output.wav"

mic = pyaudio.PyAudio()


FORMAT = pyaudio.paInt16

# Pyaudio nesnesini başlat
audio = pyaudio.PyAudio()
for i in range(audio.get_device_count()):
  dev = audio.get_device_info_by_index(i)
  print((i,dev['name'],dev['maxInputChannels']))
# Ses kaydı yapma fonksiyonu
kayit = True
def record_audio():
    global kayit
    stream = mic.open(format=pyaudio.paInt16,channels=1,rate=16000,output=False,input_device_index = 7,input=True,frames_per_buffer=8192)
    stream.start_stream()
    print("Kayıt başladı...")

    frames = []

    while kayit:
        data = stream.read(8192)
        frames.append(data)
        print(kayit)

    print("Kayıt tamamlandı.")
    with wave.open(OUTPUT_FILENAME, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(16000)
        wf.writeframes(b''.join(frames))
    

    return frames



# Ses kaydını kaydetme



frames = mp.Process(target=record_audio)
frames.start()
input("e")
kayit=False
#frames = th.Thread(target=record_audio)
#frames2 = th.Thread(target=cevap)
#frames.start()
#frames2.start()




# Ses kaydını dosyaya yazma


# Pyaudio nesnesini kapat
audio.terminate()
