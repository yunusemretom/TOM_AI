import pygame
import time

def background(durum):

    pygame.init()
    music = pygame.mixer.Sound(r"C:\Users\TOM\Documents\projeler\projeler\TOM_AI\music\ACDC - Highway to Hell.mp3")
    music.set_volume(0.2)

    if durum == True:
        
        music.play()
    else:
        pygame.mixer.pause()