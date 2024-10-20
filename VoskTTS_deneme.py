from vosk import Model, KaldiRecognizer  # Vosk kütüphanesinden gerekli modülleri içe aktar
import pyaudio  # PyAudio kütüphanesini içe aktar

model = Model(r"vosk-model-small-tr-0.3")  # Türkçe konuşma tanıma modelini yükle
recognizer = KaldiRecognizer(model,16000)  # Konuşma tanıyıcıyı oluştur

mic=pyaudio.PyAudio()  # PyAudio nesnesini oluştur
stream = mic.open(format=pyaudio.paInt16,channels=1,rate=16000,input=True,frames_per_buffer=8192)  # Ses akışını başlat

while True:  # Sonsuz döngü başlat
    data = stream.read(4092)  # Ses verisini oku
    
    if len(data) == 0:  # Eğer veri yoksa
        continue  # Döngünün başına dön
    if recognizer.AcceptWaveform(data):  # Eğer ses verisi kabul edilirse
        text = recognizer.Result()  # Tanınan metni al
        print(text)  # Tanınan metni yazdır