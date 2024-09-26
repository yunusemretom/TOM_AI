import pyttsx3

engine = pyttsx3.init()
engine.setProperty('rate', 150)
voices = engine.getProperty('voices')  
engine.setProperty('voice', voices[3].id)
engine.say("Uzun bir süre bilgisayarınızdan uzaktaysanız, Windows güncelleştirmeleri tamamlamak için bilgisayarınızı otomatik olarak yeniden başlatır. ")
engine.runAndWait()