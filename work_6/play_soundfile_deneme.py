import pygame
import threading
import time
from queue import Queue

# Ses dosyası kuyruğu
sound_queue = Queue()
is_playing = False

def play_sound_queue():
    """Kuyruktan ses dosyalarını sırayla çalan fonksiyon."""
    global is_playing
    pygame.mixer.init()  # Mixer modülünü başlat
    
    while True:
        if not sound_queue.empty():
            is_playing = True
            file_path = sound_queue.get()
            pygame.mixer.music.load(file_path)  # Ses dosyasını yükle
            pygame.mixer.music.play()  # Çalmaya başla
            
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)  # Müzik çalarken CPU'yu yormamak için bekleme
                
            is_playing = False
        time.sleep(0.1)  # Kuyruk boşken CPU'yu yormamak için bekleme

# Ses çalma thread'ini başlat
player_thread = threading.Thread(target=play_sound_queue, daemon=True)
player_thread.start()

def start_sound(file_path):
    """Ses dosyasını kuyruğa ekler."""
    sound_queue.put(file_path)

# Ana program
if __name__ == "__main__":
    print("Program başladı...")
    
    # Test için birkaç ses dosyası kuyruğa ekle
    test_file = r"C:\Users\TOM\Documents\Projeler\Tom_ai\audio_cache\cache_85562c4d0e74bfc72950312f689f94aa.wav"
    for _ in range(3):
        start_sound(test_file)
        
    for i in range(10):
        print(f"Program çalışıyor... {i}")
        time.sleep(0.5)
        
    print("Program bitti.")
