import psutil  # Sistem ve süreç bilgilerini almak için kullanılır
import time  # Zaman işlemleri için kullanılır
import os  # İşletim sistemi işlemleri için kullanılır

# Uygulama adı ve süreç adını belirle
application_name = "chrome.exe"  # İzlemek istediğin uygulamanın adı
tracking_time = 0  # İzleme süresi (saniye)

# Uygulamanın açık olup olmadığını kontrol eden fonksiyon
def is_application_running(app_name):
    for proc in psutil.process_iter(['pid', 'name']):  # Tüm süreçleri döngüye al
        if app_name.lower() in proc.info['name'].lower():  # Uygulama adını kontrol et
            return True  # Uygulama çalışıyorsa True döndür
    return False  # Uygulama çalışmıyorsa False döndür

# Uygulamayı izleme ve kullanım süresini hesaplama
def track_application(app_name):
    global tracking_time  # Global değişkeni kullan
    print(f"{app_name} izleniyor...")  # İzleme başladığını bildir
    
    while True:  # Sonsuz döngü başlat
        if is_application_running(app_name):  # Uygulama çalışıyorsa
            print(f"{app_name} çalışıyor. Zaman takip ediliyor...")  # Takip başladığını bildir
            start_time = time.time()  # Başlangıç zamanını kaydet
            while is_application_running(app_name):  # Uygulama çalıştığı sürece
                time.sleep(1)  # Her saniyede bir kontrol et
            end_time = time.time()  # Bitiş zamanını kaydet
            usage_time = end_time - start_time  # Kullanım süresini hesapla
            tracking_time += usage_time  # Toplam süreye ekle
            print(f"{app_name} toplam kullanım süresi: {tracking_time:.2f} saniye")  # Süreyi yazdır
        else:
            print(f"{app_name} çalışmıyor.")  # Uygulamanın çalışmadığını bildir
            time.sleep(5)  # 5 saniyede bir kontrol et

# Uygulamayı izleme fonksiyonunu çağır
track_application(application_name)  # Fonksiyonu çağır ve izlemeyi başlat
