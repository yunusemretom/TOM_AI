import pygame
import threading
import time
from queue import Queue

def play_sound_queue(sound_queue):
    """Kuyruktaki ses dosyalarını sırayla çalan işçi fonksiyon."""
    pygame.mixer.init()  # Mixer modülünü başlat
    while True:
        file_path = sound_queue.get()  # Kuyruktan ses dosyasını al
        if file_path is None:  # Kuyruğa None eklenirse döngü sona erer
            break
        pygame.mixer.music.load(file_path)  # Ses dosyasını yükle
        pygame.mixer.music.play()  # Çalmaya başla
        while pygame.mixer.music.get_busy():  # Ses dosyası bitene kadar bekle
            time.sleep(0.1)  # CPU'yu yormamak için kısa bir bekleme
        sound_queue.task_done()  # İşlemi tamamlandı olarak işaretle

# Kuyruk başlatma ve işçi thread oluşturma
sound_queue = Queue()
threading.Thread(target=play_sound_queue, args=(sound_queue,), daemon=True).start()

def start_sound(file_path):
    """Ses dosyasını kuyruğa ekleyen fonksiyon."""
    sound_queue.put(file_path)

# Ana program
if __name__ == "__main__":
    print("Program başladı...")
    start_sound(r"C:\Users\TOM\Documents\Projeler\Tom_ai\audio_cache\cache_1.wav")
    start_sound(r"C:\Users\TOM\Documents\Projeler\Tom_ai\audio_cache\cache_2.wav")
    start_sound(r"C:\Users\TOM\Documents\Projeler\Tom_ai\audio_cache\cache_3.wav")

    for i in range(10):
        print(f"Program çalışıyor... {i}")
        time.sleep(0.5)

    # Kuyruğa None ekleyerek işçi thread'i durdur
    sound_queue.put(None)
    sound_queue.join()  # Tüm ses dosyalarının bitmesini bekle
    print("Program bitti.")
