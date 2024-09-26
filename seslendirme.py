import pygame
import os

def speak(data,kisi=1):
    if kisi == 1:

        voice = "tr-TR-AhmetNeural" #man
    elif kisi == 2:

        voice = "tr-TR-EmelNeural" #women
    #voice = "en-PH-JamesNeural"
    pitch = "-6Hz"
    
    command = f'edge-tts --rate=+10% --voice {voice} --pitch={pitch} --text "{data}" --write-media "output.mp3"'
    print(command)
    os.system(command=command)
    print("a")
    pygame.init()
    pygame.mixer.init()
    music = pygame.mixer.Sound("output.mp3")
    channel2 = pygame.mixer.Channel(0)
    music.set_volume(0.2)
    
    channel2.play(music)

    while channel2.get_busy():
        pygame.time.Clock().tick(10)