import pygame  # Pygame kütüphanesini içe aktar
import time  # Time kütüphanesini içe aktar

def background(durum):  # Arka plan müziği kontrolü için fonksiyon

    pygame.init()  # Pygame'i başlat
    music = pygame.mixer.Sound(r"C:\Users\TOM\Documents\projeler\Tom_ai\music\ACDC - Highway to Hell.mp3")  # Müzik dosyasını yükle
    channel1 = pygame.mixer.Channel(1)  # Ses kanalı oluştur
    music.set_volume(0.2)  # Ses seviyesini ayarla

    if durum == True:  # Eğer durum True ise
        
        channel1.play(music)  # Müziği çal
    else:  # Değilse
        channel1.stop()  # Müziği durdur

