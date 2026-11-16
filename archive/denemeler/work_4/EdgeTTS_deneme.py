import asyncio
import random
import edge_tts
from edge_tts import VoicesManager
import os
from pydub import AudioSegment
from pydub.playback import play



async def amain(language="tr") -> None:
    """Main function"""
    voices = await VoicesManager.create()
    voice = voices.find(Gender="Male", Language=language)
    # Also supports Locales
    # voice = voices.find(Gender="Female", Locale="es-AR")

    communicate = edge_tts.Communicate(TEXT, random.choice(voice)["Name"])
    await communicate.save(OUTPUT_FILE)


def edge_run(text="ya ama şöyle düşünün o çalışıyor",output="output.mp3",language="tr"):
    global TEXT,OUTPUT_FILE
    TEXT = text
    OUTPUT_FILE = output
    asyncio.run(amain(language=language))
    
    # Output dosyasını çalmak için pydub kullan
    audio = AudioSegment.from_file(OUTPUT_FILE)
    play(audio)

if __name__ == "__main__":
    while True:

        
        edge_run(text=input())