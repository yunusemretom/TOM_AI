import pygame
import time

def background(durum):

    pygame.init()
    music = pygame.mixer.Sound(r"C:\Users\TOM\Documents\projeler\Tom_ai\music\ACDC - Highway to Hell.mp3")
    channel1 = pygame.mixer.Channel(1)
    music.set_volume(0.2)

    if durum == True:
        
        channel1.play(music)
    else:
        channel1.stop()

