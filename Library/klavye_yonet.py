from pynput.keyboard import Key, Controller

keyboard = Controller()

def play_pause():
    keyboard.press(Key.media_play_pause)
    keyboard.release(Key.media_play_pause)

def ses_ac():
    keyboard.press(Key.media_volume_up)
    keyboard.release(Key.media_volume_up)

def ses_kis():
    keyboard.press(Key.media_volume_down)
    keyboard.release(Key.media_volume_down)

def ses_kapat():
    keyboard.press(Key.media_volume_mute)
    keyboard.release(Key.media_volume_mute)

def uygulama_degistir():
    keyboard.press(Key.alt)
    keyboard.press(Key.tab)
    keyboard.release(Key.tab)
    keyboard.release(Key.alt)

def sonraki_sarki():
    keyboard.press(Key.media_next)
    keyboard.release(Key.media_next)

def onceki_sarki():
    keyboard.press(Key.media_previous)
    keyboard.release(Key.media_previous)

