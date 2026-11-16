from translatepy.translators.google import GoogleTranslate
from EdgeTTS_deneme import edge_run
from fasterWhisper_deneme import sesanalizi

def update_text(text, translation_lang):
    gtranslate = GoogleTranslate()
    translated_text = str(gtranslate.translate(text, translation_lang))
    print(translated_text)
    return translated_text
        

def main():
    list = sesanalizi()
    if list != None:
        for i in list:
            if i != "" or i != None:
                print(i)
                try:
                    text = update_text(text=i,translation_lang="english")
                    edge_run(text,language="en")
                except:
                    pass

while True:
    main()