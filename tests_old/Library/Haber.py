import requests  # HTTP istekleri yapmak için requests kütüphanesini içe aktar

# Haberleri yazdır
def news():
    def haberleri_getir(api_key):
        url = "https://newsapi.org/v2/top-headlines"  # Haber API'sinin URL'si
        params = {
            'country': 'tr',
            'category': 'technology',  # Türkiye'deki haberleri almak için
            'apiKey': api_key  # Kullanmanız gereken haber API anahtarınız
        }

        try:
            response = requests.get(url, params=params)  # API'ye GET isteği gönder
            response.raise_for_status()  # Hata durumunda istisna fırlat

            haberler = response.json().get('articles', [])  # JSON yanıtından haberleri al
            return haberler  # Haberleri döndür

        except requests.exceptions.RequestException as err:
            print(f"Hata: {err}")  # Hata mesajını yazdır
            return None  # Hata durumunda None döndür

    # Kullanıcıya özgü bir API anahtarı almanız gerekebilir
    API_KEY = "050961900a0e44fa83ad4f073c584705"  # API anahtarı

    # Haberleri getir
    haber_listesi = haberleri_getir(API_KEY)  # Haberleri al


    if haber_listesi:
        haber_text=haber_listesi[0]['title']  # İlk haberin başlığını al
        return haber_text  # Haber başlığını döndür
        
    else:
        print("Haber alınamadı.")  # Haber alınamadığında mesaj yazdır