import requests


# Haberleri yazdır
def news():
    def haberleri_getir(api_key):
        url = "https://newsapi.org/v2/top-headlines"
        params = {
            'country': 'tr',
            'category': 'technology',  # Türkiye'deki haberleri almak için
            'apiKey': api_key  # Kullanmanız gereken haber API anahtarınız
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()

            haberler = response.json().get('articles', [])
            return haberler

        except requests.exceptions.RequestException as err:
            print(f"Hata: {err}")
            return None

    # Kullanıcıya özgü bir API anahtarı almanız gerekebilir
    API_KEY = "050961900a0e44fa83ad4f073c584705"

    # Haberleri getir
    haber_listesi = haberleri_getir(API_KEY)


    if haber_listesi:
        haber_text=haber_listesi[0]['title']
        return haber_text
        
    else:
        print("Haber alınamadı.")