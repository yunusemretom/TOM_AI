import pyaudio  # PyAudio kütüphanesini içe aktar
import numpy as np  # NumPy kütüphanesini içe aktar
import wave  # Wave kütüphanesini içe aktar
from pydub import AudioSegment  # Pydub'dan AudioSegment'i içe aktar
import os  # İşletim sistemi işlemleri için os modülünü içe aktar
import whisper  # Whisper kütüphanesini içe aktar
import time  # Zaman işlemleri için time modülünü içe aktar
from rich import print  # Rich kütüphanesinden print fonksiyonunu içe aktar

# Mikrofonun sürekli dinlemesi ve sesin başladığını algılayıp kayda başlaması için fonksiyon
def listen_and_record():
    chunk = 4096  # Sesin kaç örneklemde parçalara ayrılacağını belirler.
    sample_format = pyaudio.paInt16  # 16 bit derinlikte ses formatı
    channels = 1  # Tek kanal (mono) kayıt
    fs = 16000  # 16kHz örnekleme frekansı
    output_wav_file = "output.wav"  # Geçici olarak kaydedilecek WAV dosyası
    output_mp3_file = "output.mp3"  # Dönüştürülecek MP3 dosyası
    threshold = 500  # Ses seviyesi eşiği, bu değerin üstünde kayıt başlar
    silent_chunks = 10  # Kaç chunk boyunca ses algılanmazsa kaydı sonlandırır

    # PyAudio başlat
    p = pyaudio.PyAudio()  # PyAudio nesnesi oluştur
    stream = p.open(format=sample_format, channels=channels, rate=fs, input=True, frames_per_buffer=chunk)  # Ses akışını başlat
    print("[blue]Mikrofon dinleniyor...[/blue]")  # Kullanıcıya bilgi ver

    frames = []  # Kaydedilen ses verilerini tutacak
    silent_count = 0  # Sessizlik sayacı
    recording = False  # Kayıt başladığında True olur

    while True:
        data = stream.read(chunk)  # Ses verisini oku
        audio_data = np.frombuffer(data, dtype=np.int16)  # Ses verisini NumPy dizisine dönüştür
        audio_volume = np.linalg.norm(audio_data)  # Ses seviyesini hesapla

        # Ses seviyesi threshold'u aşarsa kayıt başlar
        if audio_volume > threshold:
            print("[green]Ses algılandı, kayıt başlıyor...[/green]")  # Kullanıcıya bilgi ver
            recording = True  # Kayıt durumunu başlat
            silent_count = 0  # Sessizlik sayacını sıfırla

        # Ses seviyesi threshold altındaysa sessizlik sayacı artar
        if recording:
            frames.append(data)  # Ses verisini kaydet

            if audio_volume < threshold:
                silent_count += 1  # Sessizlik sayacını artır
                # Eğer belirlenen süre kadar sessizlik olursa kayıt biter
                if silent_count > silent_chunks:
                    print("[red]Sessizlik algılandı, kayıt tamamlandı.[/red]")  # Kullanıcıya bilgi ver
                    break  # Döngüden çık

    # PyAudio durdurma ve kapatma işlemleri
    stream.stop_stream()  # Ses akışını durdur
    stream.close()  # Ses akışını kapat
    p.terminate()  # PyAudio nesnesini sonlandır

    # WAV dosyasını oluştur ve ses verilerini yaz
    wf = wave.open(output_wav_file, 'wb')  # WAV dosyasını aç
    wf.setnchannels(channels)  # Kanal sayısını ayarla
    wf.setsampwidth(p.get_sample_size(sample_format))  # Örnek genişliğini ayarla
    wf.setframerate(fs)  # Örnekleme frekansını ayarla
    wf.writeframes(b''.join(frames))  # Ses verilerini yaz
    wf.close()  # WAV dosyasını kapat

    # WAV dosyasını MP3 formatına çevir ve kaydet
    audio = AudioSegment.from_wav(output_wav_file)  # WAV dosyasını yükle
    audio.export(output_mp3_file, format="mp3")  # MP3 olarak dışa aktar
    print(f"[blue]Kayıt MP3 formatına dönüştürüldü: {output_mp3_file}[/blue]")  # Kullanıcıya bilgi ver

    # İsteğe bağlı: Geçici WAV dosyasını sil
    os.remove(output_wav_file)  # WAV dosyasını sil

    return output_mp3_file  # Kaydedilen MP3 dosyasını döndür

if __name__ == "__main__":
    print(listen_and_record())  # Fonksiyonu çağır ve sonucu yazdır
