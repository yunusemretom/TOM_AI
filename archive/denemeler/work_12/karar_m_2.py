import json
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
import os

# Veri seti dosyası
DATASET_PATH = "intent_dataset.json"

# Varsayılan veri seti
DEFAULT_DATASET = {
    "intent_data": [
        {"intent": "muzik_cal", 
         "examples": ["Müzik çal", 
                      "Bir şarkı başlat", 
                      "Şarkı çalsana",
                      "müzik",
                      "Bir şarkı aç",
                      "Müzik aç",
                      "Şarkı başlat",
                      "Hadi müzik çalsın"]},

        {"intent": "hava_durumu", 
         "examples": ["Hava nasıl?", 
                      "Bugün hava durumu ne?", 
                      "Dışarısı sıcak mı?",
                      "Hava durumu nedir?",
                      "Yağmur yağacak mı?",
                      "Hava durumu raporu",
                      "Bugün dışarı çıkabilir miyim?",
                      "Hava nasıl olacak?",
                      "Yağmur var mı?"]},

        {"intent": "muzik_değiştir", 
         "examples": ["Müziği değiştir", 
                      "Başka bir şarkı çal", 
                      "Farklı bir parça aç",
                      "Yeni bir şarkı çal",
                      "Şarkıyı değiştir",
                      "Başka bir müzik aç",
                      "Farklı bir müzik çal",
                      "Yeni bir şarkıya geç"]},

        {"intent": "sesi_aç", 
         "examples": ["Sesi aç", 
                      "Sesi yükselt", 
                      "Daha yüksek sesle çal",
                      "Sesi artır",
                      "Sesi biraz daha aç",
                      "Müziği daha yüksek yap",
                      "Sesini aç",
                      "Ses biraz daha yükselsin"]},

        {"intent": "sesi_kıs", 
         "examples": ["Sesi kıs", 
                      "Sesi azalt", 
                      "Daha düşük sesle çal",
                      "Sesi biraz kıs",
                      "Müziği kıs",
                      "Sesi azalt lütfen",
                      "Sesin biraz düşsün",
                      "Sesi düşük yap"]},

        {"intent": "sesi_kapat", 
         "examples": ["Sesi kapat", 
                      "Müziği durdur", 
                      "Ses yok",
                      "Müziği kapat",
                      "Sesi tamamen kapat",
                      "Ses açma",
                      "Müziği kapat lütfen",
                      "Sesini kapat"]},

        {"intent": "sohbet_kararı", 
         "examples": ["Sohbet kararı ver", 
                      "Karar al", 
                      "Ne yapmalıyım?",
                      "Bana bir karar ver",
                      "Hangi seçeneği seçmeliyim?",
                      "Karar vermeme yardım et",
                      "Beni yönlendir",
                      "Şu an ne yapmalıyım?"]},

        {"intent": "alarm_kur", 
         "examples": ["Alarm kur", 
                      "Bir alarm kurar mısın?",
                      "Beni 8'de uyandır",
                      "Sabah 7'de alarm kur",
                      "Alarmı 10 dakika sonra kur",
                      "Beni saat 6'da uyandır"]},

        {"intent": "hatırlatıcı_ekle", 
         "examples": ["Bir hatırlatıcı ekle", 
                      "Hatırlatıcı kur",
                      "Saat 2'ye hatırlatıcı koy",
                      "Yarın 10'da hatırlatıcı kur",
                      "Bir şey hatırlat bana",
                      "Hatırlatıcı oluştur"]},

        {"intent": "saat_sor", 
         "examples": ["Saat kaç?", 
                      "Saat ne?", 
                      "Şu an saat kaç?",
                      "Hangi saatteyiz?",
                      "Saatin kaç olduğunu söyler misin?",
                      "Şu an ne kadar zaman geçti?"]},

        {"intent": "gün_dönemi", 
         "examples": ["Bugün günlerden ne?", 
                      "Hangi gündeyiz?",
                      "Bugün hangi gün?",
                      "Bugün Pazar mı?",
                      "Yarın hangi gün?",
                      "Hangi hafta günü?"]},

        {"intent": "yol_tarifi", 
         "examples": ["Nasıl gidilir?", 
                      "Burası nasıl gidilir?",
                      "Bana şu adrese nasıl giderim?",
                      "Bu yoldan nasıl geçebilirim?",
                      "Nereye gitmeliyim?",
                      "Bu yoldan gidip şuraya ulaşabilir miyim?"]},

        {"intent": "video_izle", 
         "examples": ["Bir video izle", 
                      "Video aç",
                      "YouTube'da bir video izle",
                      "Bana bir video göster",
                      "Videoyu başlat",
                      "Bir video başlat"]},

        {"intent": "fiyat_sor", 
         "examples": ["Bu ürün ne kadar?", 
                      "Fiyatı ne kadar?",
                      "Bunun fiyatı nedir?",
                      "Bir şeyin fiyatını öğrenmek istiyorum",
                      "Bunun fiyatı nedir?",
                      "Bu ne kadar?"]},

        {"intent": "yemek_tarifi", 
         "examples": ["Yemek tarifi ver", 
                      "Bana yemek tarifi öner",
                      "Bugün ne pişirsem?",
                      "Yemek yapmak için tarif ver",
                      "Hangi yemeği yapmalıyım?",
                      "Bir yemek tarifi ver"]},

        {"intent": "kitap_sor", 
         "examples": ["Kitap öner", 
                      "Bana bir kitap öner",
                      "Ne kitap okumalıyım?",
                      "En çok okunan kitapları biliyor musun?",
                      "Bir kitap tavsiyesi ver",
                      "Hangi kitapları okumalıyım?"]},

        {"intent": "film_sor", 
         "examples": ["Film öner", 
                      "Bana bir film öner",
                      "Ne film izlesem?",
                      "En iyi filmleri biliyor musun?",
                      "Bu akşam ne izleyeyim?",
                      "Bana film önerir misin?"]},

        {"intent": "komik_video", 
         "examples": ["Komik bir video bul", 
                      "Bana bir komik video göster",
                      "Gülme videoları izle",
                      "Bir komik video aç",
                      "Bana güldüren bir video göster",
                      "Komik bir şey izlet"]},

        {"intent": "yazilim_sor", 
         "examples": ["Bu yazılım nedir?",
                      "Yazılım hakkında bilgi ver",
                      "Bir yazılım tavsiyesi var mı?",
                      "En iyi yazılımlar nelerdir?",
                      "Yazılımla ilgili konuşalım",
                      "Yazılım tavsiyen var mı?"]},

        {"intent": "kitap_oku", 
         "examples": ["Bir kitap oku", 
                      "Kitap okumaya başla",
                      "Bir kitapla ilgili özet yap",
                      "Kitap hakkında konuşalım",
                      "Bir hikaye oku",
                      "Kitap üzerine sohbet et"]}

    ]
}


# Dosya kontrolü
if not os.path.exists(DATASET_PATH):
    with open(DATASET_PATH, "w", encoding='utf_8') as f:
        json.dump(DEFAULT_DATASET, f, ensure_ascii=False, indent=4)


# Veri yükleme
with open(DATASET_PATH, "r", encoding='utf8') as f:
    dataset = json.load(f)


# Eğitim verisini hazırlama
def prepare_training_data(dataset):
    texts, labels = [], []
    for item in dataset['intent_data']:
        for example in item['examples']:
            texts.append(example)
            labels.append(item['intent'])
    return texts, labels


# Model eğitimi fonksiyonu
def train_model():
    texts, labels = prepare_training_data(dataset)
    vectorizer = CountVectorizer()
    X = vectorizer.fit_transform(texts)
    model = MultinomialNB()
    model.fit(X, labels)
    return vectorizer, model

# Alternatif intent önerileri göster
# İlk model eğitimi
vectorizer, model = train_model(epoch=3)


# Kullanıcıdan öğrenme fonksiyonu
def learn_new_intent(user_input):
    intent_name = input(f"Bu komut ne yapmalı? (Intent adı girin): ")
    
    # Var olan bir intent mi kontrol et
    for item in dataset['intent_data']:
        if item['intent'] == intent_name:
            item['examples'].append(user_input)
            break
    else:
        # Yeni bir intent oluştur
        dataset['intent_data'].append({"intent": intent_name, "examples": [user_input]})

    # Güncellenmiş veri setini kaydet
    with open(DATASET_PATH, "w", encoding="utf_8") as f:
        json.dump(dataset, f, indent=4, ensure_ascii=False)

    print(f"Yeni intent '{intent_name}' öğrenildi!")
    
    # Modeli yeniden eğit
    global vectorizer, model
    vectorizer, model = train_model()
    print("Model yeniden eğitildi!")


# Mesaj işleme
def handle_message(message):
    global vectorizer, model
    
    X_input = vectorizer.transform([message])
    predicted_intent = model.predict(X_input)[0]
    confidence = model.predict_proba(X_input).max()
    
    print(f"Anlaşılan intent: {predicted_intent}, Güven: {confidence:.4f}")
    
    if confidence < 0.1:
        print("Bu mesajı anlayamadım!")
        learn_new_intent(message)
    else:
        # Kullanıcıdan karar doğrulama
        correct = input("Bu karar doğru mu? (Evet/Hayır): ")
        if correct.lower() != "evet":
            correct_intent = input("Doğru intent nedir?: ")
            
            # Var olan bir intent mi kontrol et
            intent_exists = False
            for item in dataset['intent_data']:
                if item['intent'] == correct_intent:
                    item['examples'].append(message)
                    intent_exists = True
                    break
            
            # Eğer yoksa yeni intent oluştur
            if not intent_exists:
                dataset['intent_data'].append({"intent": correct_intent, "examples": [message]})

            # Güncellenmiş veri setini kaydet
            with open(DATASET_PATH, "w", encoding="utf_8") as f:
                json.dump(dataset, f, indent=4, ensure_ascii=False)

            print(f"Intent '{correct_intent}' için yeni örnek öğrenildi!")
            
            # Modeli yeniden eğit
            vectorizer, model = train_model()
            print("Model yeniden eğitildi!")


# Test çalıştırması
print("Asistan başlatıldı! Çıkmak için 'q' yazın.")
while True:
    user_message = input("Kullanıcı: ")
    if user_message.lower() == 'q':
        break
    handle_message(user_message)

print("Asistan kapatıldı!")

# Bu kodu çalıştırıp test edebilirsin. Başta anlamadığı komutları öğrenip kendini geliştirecek! 🚀