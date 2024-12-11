import pygame
import threading
import time

def play_sound(file_path):
    """Ses dosyasını arka planda çalan fonksiyon."""
    pygame.mixer.init()  # Mixer modülünü başlat
    pygame.mixer.music.load(file_path)  # Ses dosyasını yükle
    pygame.mixer.music.play()  # Çalmaya başla
    while pygame.mixer.music.get_busy():
        time.sleep(1)  # Müzik çalarken CPU'yu yormamak için bekleme

# Ses dosyasını çalmak için ayrı bir thread başlat
def start_sound(file_path):
    threading.Thread(target=play_sound, args=(file_path,), daemon=True).start()

# Ana program
if __name__ == "__main__":
    print("Program başladı...")
    #start_sound = threading.Thread(target=play_sound_in_background, args=(r"C:\Users\TOM\Documents\Projeler\Tom_ai\audio_cache\cache_5e80b8e710ebcec3d1c828d9d29a9e14.wav",), daemon=True)
    #start_sound.start()
    play_sound(r"C:\Users\TOM\Documents\Projeler\Tom_ai\audio_cache\cache_5e80b8e710ebcec3d1c828d9d29a9e14.wav")
    for i in range(10):
        print(f"Program çalışıyor... {i}")
        time.sleep(0.5)  # Ana program akışı
    #start_sound.join() 
    print("Program bitti.")
