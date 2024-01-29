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
model = Model("TOM_AI/vosk-model-small-tr-0.3")
recognizer = KaldiRecognizer(model,16000)

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


nasilsincumeleleri = ["nasılsın","naber","ne haber","napıyorsun","nasıl gidiyor","naber","napıyon","nasıl","nabıyon","merhaba"]
iltifat = ["mükemmelsin","çok iyisin","mükemmel","efsane","saol","teşekkürler","çok","iyi","çok iyi"]
donus = ["iyiyim sen","çok iyiyim","Teşekkür ederim beni düşün"]
kimsin = ["sen nesin","nesin","kimsin","ne iş yaparısın"]
donustesekkur = ["Çok teşekkürler","beni utandırıyorsun","utandım","teşekkürler","yardımcı olabildiysem ne mutlu bana"]

clock = ["saat","kaç","saat kaç","kaç saat","zaman"]
gun = ["bugün ayın kaçı","ayın","kaçı","bugün günlerden ne","günler","günlerden","bu gün ayın"]
maps = ["nerede","nerededir","nerda","nerde","neresi"]

search = ["nedir","kimdir","nasıl","arama yap"]
tempature = ["derece","hava","hava kaç","sıcaklık kaç","sıcaklık","hava durumu"]

note = ["not al","not alır mısın","not"]
noteread = ["notlarımı oku","notları oku","notlar"]

haber = ["haberler","haberleri","haber","gündem","gazete","oku","haberleri oku"]

playlist = ["müzik listemi çal","müzik listem","müzik","playlist","listem","müzik listeleri","müzik aç"]
playsong = ["başlat","devam et","şarkıyı başlat","şarkıyı devam et","müziği aç","şarkı aç"]
stopsong = ["şarkıyı kapat","şarkıyı durdur","durdur"]
nextsong=["şarkıyı değiştir","sonraki","sonraki şarkı", "sonraki müzik","müzik değiştir","müziği değiştir","değiştir"]
oncekisarki=["önceki","önceki şarkı","önceki müzik"]

kapatma = ["sistemi kapat","uyu","kendini kapat","görüşürüz", "bay bay"]
tomopen = ["hey tom","hey","alo","tom","açıl","açıl susam açıl","açın","uyan bakalım"]
tomopendonus = ["her zaman efendim","açıldım efendim","aktifim"]

animsatici = ["anımsatıcı oluştur","anımsatıcı kur","anımsatıcı başlat","anımsatıcı oluş"]
animsaticioku = ["anımsatıcılarım","anımsatıcımı oku","anımsatıcılar","anımsatıcılarımı oku","anımsatıcı oku","anımsatıcım"]

baglantikur=["uçağa bağlan","bağlan","uçak","otonom","uçak bağlan","uçak modu"]


penceredegistir=["pencere değiştir","uygulama değiştir","pencereyi değiştir"]

lightopen =["ışıkları aç","ışıklar","işıklar"]
lightoff = ["ışıkları kapat","işıkları kapat"]

sesartırma = ["ses aç","sesi arttır","sesini arttır","ses arttır","sesi aç","sesini aç"]
sesazaltma = ["ses kıs", "sesi azalt","sesini azalt","ses azalt","sesi azalt","sesi kıs","sesini kıs"]

seskaydet=["ses kaydet","sesi kaydet","yeni proje","ses kaydı","kayıt yap"]
seskaydetdur=["ses kaydını durdur","kaydı durdur", "kayıt dur","bitir"]

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


def responsive(text):
    global kayit
    try:
        
        if kelime_kontrol(text,baglantikur):
            konus("bağlantı kuruluyor")

        if kelime_kontrol(text,background_music):
            konus("kapatıldı")
            background(False)
        
        if kelime_kontrol(text,tomopen):
             konus(tomopendonus[randint(0,len(tomopendonus)-1)])

        if kelime_kontrol(text,tempature):
            konus(f"Hava{temp()} derece ve {hava()}")

        if kelime_kontrol(text,nasilsincumeleleri):
            konus(donus[randint(0,len(donus)-1)])

        if kelime_kontrol(text,kimsin):
            konus("Ben adım TOM. Ben sesli bir asistanım. Birçok projeye yardım etmek amacaıyla oluşturuldum.")

        if kelime_kontrol(text,clock):
            saat = str(time.localtime().tm_hour)+" "+str(time.localtime().tm_min)
            konus(saat)

        if kelime_kontrol(text,playlist):
            konus("açılıyor")
            webbrowser.open("https://www.youtube.com/watch?v=YbWkR6mFI6s&list=RDrnhBElHzHb0&index=1",new=2)

        if kelime_kontrol(text,penceredegistir):
            print("pencere değişti")
            uygulama_degistir()

        elif kelime_kontrol(text,nextsong):
            sonraki_sarki()

        if kelime_kontrol(text,oncekisarki):
            onceki_sarki()

        if kelime_kontrol(text,stopsong):
            play_pause()

        if kelime_kontrol(text,playsong):
            play_pause()

        if kelime_kontrol(text,search):
            website = text.replace("arama yap", "")
            konus(website+" araması yapılıyor")
            time.sleep(1)
            
            if website != None:
                print(website)
                webbrowser.open("https://www.google.com/search?q="+website,new=2)
            else:
                konus("aranacak kelime yok")

        if kelime_kontrol(text,lightopen):
            konus("ışıklar açılıyor")  
        
        if kelime_kontrol(text,lightoff):
            konus("ışıklar kapatılıyor")
        
        if kelime_kontrol(text,sesartırma):
            for i in range(5):
                ses_ac()
                time.sleep(0.1)

        if kelime_kontrol(text,sesazaltma) :
            for i in range(5):
                ses_kıs()
                time.sleep(0.1)

        if kelime_kontrol(text,seskaydet):
            konus("proje ismi nedir")
            proje_ismi = ""
            while proje_ismi == None or proje_ismi == "" or proje_ismi == " ":
                proje_ismi=record()
                if proje_ismi=="çık":
                       break
            proje_ismi=proje_ismi+".wav"
            konus(proje_ismi)
            p1=mp.Process(target=sound_record)
            p1.start()
            
        
        if kelime_kontrol(text,seskaydetdur):
            konus("kayıt bitti")
            kayit=False

        if 'sesi kapat' in text :
            ses_kapat()
            time.sleep(0.1)

        else:
            pass

    except Exception as e:
        print(e)
        konus("sistemsel bir arıza oluştu tekrar deneyin")
    
    if kelime_kontrol(text,kapatma):
            konus("görüşmek üzere")
            exit()


background(durum = True)
time.sleep(2)
konus("Hoş geldiniz efendim. Güzel bir gün.")
konus(f"Hava{temp()} derece ve {hava()}")
konus("Güncel haberlerden")
konus(news())
while True:
    question = record()
    if question !=None:
        responsive(question)
    

