import requests  # HTTP istekleri için requests kütüphanesini içe aktar

from translate import Translator  # Çeviri için Translator sınıfını içe aktar


api_key = '395ccd54e9148627148b12a98ba10133'  # OpenWeatherMap API anahtarı
base_url ="https://api.openweathermap.org/data/2.5/weather?"  # OpenWeatherMap API temel URL'si

city ="Malatya"  # Hava durumu sorgulanacak şehir

request_url = f'{base_url}q={city}&appid={api_key}'  # API isteği için URL oluştur

response = requests.get(request_url)  # API'ye GET isteği gönder


def cevir(text, tolang = 'tr'):  # Metni çevirmek için fonksiyon
    translator= Translator(to_lang=tolang)  # Çevirmen nesnesi oluştur
    translation = translator.translate(text)  # Metni çevir
    return translation  # Çeviriyi döndür

def hava():  # Hava durumunu almak için fonksiyon
    global weather  # weather değişkenini global olarak tanımla
    if response.status_code == 200:  # Eğer API yanıtı başarılıysa
        data = response.json()  # JSON verisini al
        weather = data['weather'][0]['description']  # Hava durumu açıklamasını al
        return cevir(weather)  # Çevirilmiş hava durumunu döndür

    else:  # API yanıtı başarısızsa
        print("hata")  # Hata mesajı yazdır


def temp():  # Sıcaklığı almak için fonksiyon
    global temp  # temp değişkenini global olarak tanımla

    
    if response.status_code == 200:  # Eğer API yanıtı başarılıysa
        data = response.json()  # JSON verisini al
        temp = round(data['main']['temp'] + -272.15)  # Kelvin'i Celsius'a çevir ve yuvarla
        return temp  # Sıcaklığı döndür

    else:  # API yanıtı başarısızsa
        print("hata")  # Hata mesajı yazdır
