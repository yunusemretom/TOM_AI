from vosk import Model, KaldiRecognizer
import pyaudio

model = Model(r"C:\Users\TOM\Documents\projeler\projeler\TOM_AI\vosk-model-small-tr-0.3")
recognizer = KaldiRecognizer(model,16000)

mic=pyaudio.PyAudio()
stream = mic.open(format=pyaudio.paInt16,channels=1,rate=16000,input=True,frames_per_buffer=8192)

while True:
    data = stream.read(4092)
    
    if len(data) == 0:
        continue
    if recognizer.AcceptWaveform(data):
        text = recognizer.Result()
        print(text)