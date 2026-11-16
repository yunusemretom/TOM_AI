from pynput.keyboard import Key, Controller  # Klavye kontrolü için gerekli modülleri içe aktar

keyboard = Controller()  # Klavye kontrolcüsü oluştur

def play_pause():
    keyboard.press(Key.media_play_pause)  # Medya oynat/duraklat tuşuna bas
    keyboard.release(Key.media_play_pause)  # Medya oynat/duraklat tuşunu bırak

def ses_ac():
    keyboard.press(Key.media_volume_up)  # Ses artırma tuşuna bas
    keyboard.release(Key.media_volume_up)  # Ses artırma tuşunu bırak

def ses_kis():
    keyboard.press(Key.media_volume_down)  # Ses azaltma tuşuna bas
    keyboard.release(Key.media_volume_down)  # Ses azaltma tuşunu bırak

def ses_kapat():
    keyboard.press(Key.media_volume_mute)  # Ses kapatma tuşuna bas
    keyboard.release(Key.media_volume_mute)  # Ses kapatma tuşunu bırak

def uygulama_degistir():
    keyboard.press(Key.alt)  # Alt tuşuna bas
    keyboard.press(Key.tab)  # Tab tuşuna bas
    keyboard.release(Key.tab)  # Tab tuşunu bırak
    keyboard.release(Key.alt)  # Alt tuşunu bırak

def sonraki_sarki():
    keyboard.press(Key.media_next)  # Sonraki şarkı tuşuna bas
    keyboard.release(Key.media_next)  # Sonraki şarkı tuşunu bırak

def onceki_sarki():
    keyboard.press(Key.media_previous)  # Önceki şarkı tuşuna bas
    keyboard.release(Key.media_previous)  # Önceki şarkı tuşunu bırak
