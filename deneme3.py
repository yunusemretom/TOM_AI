import psutil
import time
import os

# Uygulama adı ve süreç adını belirle
application_name = "chrome.exe"  # İzlemek istediğin uygulamanın adı
tracking_time = 0  # İzleme süresi (saniye)

# Uygulamanın açık olup olmadığını kontrol eden fonksiyon
def is_application_running(app_name):
    for proc in psutil.process_iter(['pid', 'name']):
        if app_name.lower() in proc.info['name'].lower():
            return True
    return False

# Uygulamayı izleme ve kullanım süresini hesaplama
def track_application(app_name):
    global tracking_time
    print(f"{app_name} izleniyor...")
    
    while True:
        if is_application_running(app_name):
            print(f"{app_name} çalışıyor. Zaman takip ediliyor...")
            start_time = time.time()
            while is_application_running(app_name):
                time.sleep(1)  # Her saniyede bir kontrol et
            end_time = time.time()
            usage_time = end_time - start_time
            tracking_time += usage_time
            print(f"{app_name} toplam kullanım süresi: {tracking_time:.2f} saniye")
        else:
            print(f"{app_name} çalışmıyor.")
            time.sleep(5)  # 5 saniyede bir kontrol et

# Uygulamayı izleme fonksiyonunu çağır
track_application(application_name)
