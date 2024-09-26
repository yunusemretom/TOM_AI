import time
import webbrowser
from random import randint
import multiprocessing as mp
import wave
import pyaudio
import pyttsx3
from vosk import KaldiRecognizer, Model
from Library.Hava_durum import hava, temp
from Library.arka_plan import background
from Library.Haber import news
from Library.klavye_yonet import *

#sesi yazıya çevirmek için veri seti
from seslendirme import speak



model = Model("vosk-model-small-tr-0.3")
recognizer = KaldiRecognizer(model,16000)

#mikrofon için gerekli ayaralar. Değiştirilmesi önerilmez!
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
WAVE_OUTPUT_FILENAME = "file.wav"
 
#mikrofon için gerekli ayaralar. Değiştirilmesi önerilmez!
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
WAVE_OUTPUT_FILENAME = "file.wav"
 
#burada ses verisini alıyoruz
mic = pyaudio.PyAudio()
stream = mic.open(format=FORMAT, channels=CHANNELS,
                rate=RATE, input=True,
                frames_per_buffer=CHUNK)

stream.start_stream()
FORMAT = pyaudio.paInt16

#sese dönüştüre için gerekli ayarlar
engine = pyttsx3.init()
engine.setProperty('rate', 150)
voices = engine.getProperty('voices')  
print(len(voices))
engine.setProperty('voice', voices[3].id)
engine.setProperty('voice', voices[3].id)

def konus(yazi):
    engine.say(yazi)
    engine.runAndWait()


#sesimizi kaydetmek ve göndermek için
def record():
    data = stream.read(4096)
    if recognizer.AcceptWaveform(data):
        text = recognizer.Result()
        texty = text[14:-3]
        print(text[14:-3])
        if texty != "" :
            #responsive(texty)
            return texty
        else:
            return record()


sesdeger = 1

commands = {

    "not defteri aç": open_notepad,
    "tarayıcı aç": open_browser,
    "sesi arttır": pass,
    "sesi azalt": pass,
    "sesini değiştir": pass,
    "nasılsın": pass,
    "görüşürüz": pass,
    "not al": pass,
    "son dakika haberleri":pass,
    "merhaba tom": pass,
    "saat kaç": pass
    "değiştir şarkıyı": pass,
    "arama yap", pass
    "parlaklığı arttır": pass,
    "parlaklığı azalt": pass,
    "arka planı kapat": pass

}

background_music = ["arka planını kapat","arka planı kapat", "arka plan muziğini kapat","planı kapat", "arka kapat","arka planı kapat","sessiz ol", "sessiz mod"]
def kelime_kontrol(cumle, kelime_listesi):
    for kelime in kelime_listesi:
        if kelime in cumle:
            return True
    return False

kayit = True
def sound_record(filename="output.wav"):
    
    global kayit
    OUTPUT_FILENAME = filename
    frames = []
    print("f")
    konus("kayıt başladı")
    while kayit:
        data = stream.read(8192)
        frames.append(data)
        print("i")
    with wave.open(OUTPUT_FILENAME, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(mic.get_sample_size(FORMAT))
        wf.setframerate(16000)
        wf.writeframes(b''.join(frames))

    konus("kayıt bitti")    
    print("d")
    kayit=True



