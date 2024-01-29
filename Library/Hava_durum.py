import requests

from translate import Translator


api_key = '395ccd54e9148627148b12a98ba10133'
base_url ="https://api.openweathermap.org/data/2.5/weather?"

city ="Malatya"

request_url = f'{base_url}q={city}&appid={api_key}'

response = requests.get(request_url)


def cevir(text, tolang = 'tr'):
    translator= Translator(to_lang=tolang)
    translation = translator.translate(text)
    return translation

def hava():
    global weather
    if response.status_code == 200:
        data = response.json()
        weather = data['weather'][0]['description']
        return cevir(weather)

    else:
        print("hata")


def temp():
    global temp

    
    if response.status_code == 200:
        data = response.json()
        temp = round(data['main']['temp'] + -272.15)
        return temp

    else:
        print("hata")
