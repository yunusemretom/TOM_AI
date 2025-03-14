import pyaudio
import wave
import numpy as np
import time

def listele_cihazlar():
    """Tüm ses cihazlarını listeler ve indekslerini gösterir."""
    p = pyaudio.PyAudio()
    cikis_cihazlari = []
    
    print("Kullanılabilir ses çıkış cihazları:")
    print("-" * 50)
    
    for i in range(p.get_device_count()):
        bilgi = p.get_device_info_by_index(i)
        if bilgi:
            print(f"Cihaz {i}: {bilgi['name']}")
            cikis_cihazlari.append(i)
    
    p.terminate()
    return cikis_cihazlari

def kaydet_hoparlor_cikisi(cihaz_indeksi, kayit_suresi=5, dosya_adi="hoparlor_kaydi.wav"):
    """Belirtilen cihaz indeksinden ses kaydeder."""
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 2
    RATE = 44100
    
    p = pyaudio.PyAudio()
    
    # Ses akışını başlat
    try:
        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        input_device_index=cihaz_indeksi,
                        frames_per_buffer=CHUNK)
        
        print(f"Cihaz {cihaz_indeksi} üzerinden {kayit_suresi} saniye boyunca kayıt yapılıyor...")
        frames = []
        
        for i in range(0, int(RATE / CHUNK * kayit_suresi)):
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
        
        print("Kayıt tamamlandı!")
        
        # Akışı durdur ve kapat
        stream.stop_stream()
        stream.close()
        
        # Kaydı WAV dosyası olarak kaydet
        wf = wave.open(dosya_adi, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        print(f"Kayıt {dosya_adi} dosyasına kaydedildi.")
        
    except Exception as e:
        print(f"Hata oluştu: {e}")
    
    finally:
        p.terminate()

# Örnek kullanım
if __name__ == "__main__":
    cihazlar = listele_cihazlar()
    
    if cihazlar:
        try:
            secim = int(input("\nKayıt yapmak istediğiniz cihazın indeksini girin: "))
            if secim in cihazlar:
                sure = int(input("Kayıt süresini saniye cinsinden girin: "))
                dosya = input("Kayıt dosyasının adını girin (varsayılan: kayit.wav): ") or "kayit.wav"
                kaydet_hoparlor_cikisi(secim, sure, dosya)
            else:
                print("Geçersiz cihaz indeksi!")
        except ValueError:
            print("Lütfen geçerli bir sayı girin!")
    else:
        print("Hiçbir çıkış cihazı bulunamadı!")