from translatepy.translators.google import GoogleTranslate

def update_text(self, text, translation_lang):
        
        gtranslate = GoogleTranslate()
        num = -2
        if len(text) < 2:
            num = -len(text)
        for i in range(num, 0, 1):
            text_to_display += text[i] + '\n'
            try:
                translated_text = str(gtranslate.translate(text[i], translation_lang))
            except:
                translated_text = ""
            text_to_display += translated_text + '\n'

