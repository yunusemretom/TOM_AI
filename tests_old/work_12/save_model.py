import json
import pickle
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
import os
import numpy as np

# Sabit dosya yolları
DATASET_PATH = "intent_dataset.json"
MODEL_PATH = "nlp_model.pkl"
VECTORIZER_PATH = "vectorizer.pkl"

# Varsayılan veri seti dosya kontrolü (sadece dosya yoksa oluşturur)
if not os.path.exists(DATASET_PATH):
    # Varsayılan boş bir dataset oluşturalım
    DEFAULT_DATASET = {
        "intent_data": [
            {"intent": "muzik_cal", "examples": ["Müzik çal", "Bir şarkı başlat"]},
            {"intent": "hava_durumu", "examples": ["Hava nasıl?", "Bugün hava durumu ne?"]}
        ]
    }
    with open(DATASET_PATH, "w", encoding='utf_8') as f:
        json.dump(DEFAULT_DATASET, f, ensure_ascii=False, indent=4)
    print(f"'{DATASET_PATH}' dosyası oluşturuldu.")


# Veri yükleme
def load_dataset():
    with open(DATASET_PATH, "r", encoding='utf8') as f:
        return json.load(f)


# Mevcut intent listesini göster
def show_available_intents(dataset):
    print("\nMevcut Intent Listesi:")
    print("----------------------")
    for i, item in enumerate(dataset['intent_data'], 1):
        print(f"{i}. {item['intent']} ({len(item['examples'])} örnek)")
    print("----------------------")


# Eğitim verisini hazırlama
def prepare_training_data(dataset):
    texts, labels = [], []
    for item in dataset['intent_data']:
        for example in item['examples']:
            texts.append(example)
            labels.append(item['intent'])
    return texts, labels


# Model eğitimi fonksiyonu
def train_model(dataset):
    texts, labels = prepare_training_data(dataset)
    vectorizer = CountVectorizer()
    X = vectorizer.fit_transform(texts)
    model = MultinomialNB()
    model.fit(X, labels)
    return vectorizer, model


# Modeli kaydetme fonksiyonu
def save_model(model, vectorizer):
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    
    with open(VECTORIZER_PATH, 'wb') as f:
        pickle.dump(vectorizer, f)
    
    print(f"Model kaydedildi: {MODEL_PATH} ve {VECTORIZER_PATH}")


# Modeli yükleme fonksiyonu
def load_model():
    if os.path.exists(MODEL_PATH) and os.path.exists(VECTORIZER_PATH):
        try:
            with open(MODEL_PATH, 'rb') as f:
                model = pickle.load(f)
            
            with open(VECTORIZER_PATH, 'rb') as f:
                vectorizer = pickle.load(f)
            
            print("Kaydedilmiş model yüklendi.")
            return vectorizer, model
        except Exception as e:
            print(f"Model yüklenirken hata oluştu: {e}")
            return None, None
    else:
        print("Kaydedilmiş model bulunamadı.")
        return None, None


# Alternatif intent önerileri göster
def show_alternative_intents(model, vector, dataset, top_n=3):
    # Tüm sınıfların olasılıklarını al
    all_probs = model.predict_proba(vector)[0]
    
    # Intent indeksleri ve olasılıkları birlikte tut ve sırala
    intent_indices = np.argsort(all_probs)[::-1]  # En yüksek olasılıktan en düşüğe
    
    # Model sınıf etiketlerini al
    class_labels = model.classes_
    
    # En olası top_n intent'i göster
    print("\nEn Olası İntent Alternatifleri:")
    print("--------------------------------")
    for i, idx in enumerate(intent_indices[:top_n], 1):
        intent_name = class_labels[idx]
        probability = all_probs[idx]
        print(f"{i}. {intent_name}: %{probability*100:.2f} olasılık")
    
    return [(class_labels[idx], all_probs[idx]) for idx in intent_indices[:top_n]]


# Kullanıcıdan öğrenme fonksiyonu
def learn_new_intent(user_input, dataset, vectorizer, model):
    # Mevcut intent'leri göster
    show_available_intents(dataset)
    
    # Eğer model eğitilmişse ve vektörleştirici hazırsa, alternatif önerileri göster
    if model is not None and vectorizer is not None:
        try:
            X_input = vectorizer.transform([user_input])
            alternatives = show_alternative_intents(model, X_input, dataset)
        except:
            print("Alternatif öneri gösterilemedi.")
    
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
    save_dataset(dataset)
    print(f"Yeni intent '{intent_name}' öğrenildi!")
    
    # Modeli yeniden eğit ve kaydet
    vectorizer, model = train_model(dataset)
    save_model(model, vectorizer)
    
    return vectorizer, model


# Veri setini kaydet
def save_dataset(dataset):
    with open(DATASET_PATH, "w", encoding="utf_8") as f:
        json.dump(dataset, f, indent=4, ensure_ascii=False)


# Mesaj işleme
def handle_message(message, vectorizer, model, dataset, confidence_threshold=0.5):
    X_input = vectorizer.transform([message])
    predicted_intent = model.predict(X_input)[0]
    confidence = model.predict_proba(X_input).max()
    
    print(f"Anlaşılan intent: {predicted_intent}, Güven: {confidence:.4f}")
    
    # Düşük güven durumunda alternatif önerileri göster ve yeni intent öğren
    if confidence < confidence_threshold:
        print(f"Güven değeri düşük! (Eşik: {confidence_threshold:.2f})")
        alternatives = show_alternative_intents(model, X_input, dataset)
        
        # Alternatif seçimi ya da yeni intent ekleme
        choice = input("\nSeçenekler:\n1-3: Alternatif bir intent seç\n0: Yeni bir intent ekle\nSeçiminiz: ")
        
        if choice.isdigit():
            choice = int(choice)
            if 1 <= choice <= len(alternatives):
                selected_intent = alternatives[choice-1][0]
                print(f"Seçilen intent: {selected_intent}")
                
                # Seçilen intent'e örnek ekle
                for item in dataset['intent_data']:
                    if item['intent'] == selected_intent:
                        item['examples'].append(message)
                        break
                
                # Veri setini kaydet ve modeli yeniden eğit
                save_dataset(dataset)
                print(f"Intent '{selected_intent}' için yeni örnek eklendi.")
                vectorizer, model = train_model(dataset)
                save_model(model, vectorizer)
                return vectorizer, model
        
        # Yeni intent öğren
        return learn_new_intent(message, dataset, vectorizer, model)
    
    else:
        # Yeterince yüksek güven durumunda bile kullanıcıya doğrulama sor
        correct = input("Bu karar doğru mu? (Evet/Hayır): ")
        if correct.lower() != "evet":
            # Mevcut intent'leri göster
            show_available_intents(dataset)
            
            # Alternatif önerileri göster
            alternatives = show_alternative_intents(model, X_input, dataset)
            
            # Intent seçimi (numara veya isim ile)
            correct_intent = input("Doğru intent nedir? (İsim veya numara girebilirsiniz): ")
            
            # Eğer numara girilmişse, intent adına dönüştür
            if correct_intent.isdigit():
                index = int(correct_intent) - 1
                if 0 <= index < len(dataset['intent_data']):
                    correct_intent = dataset['intent_data'][index]['intent']
                    print(f"Seçilen intent: {correct_intent}")
                else:
                    print("Geçersiz numara! Yeni bir intent oluşturulacak.")
            
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
            save_dataset(dataset)
            print(f"Intent '{correct_intent}' için yeni örnek öğrenildi!")
            
            # Modeli yeniden eğit ve kaydet
            vectorizer, model = train_model(dataset)
            save_model(model, vectorizer)
            
    return vectorizer, model


# Eğitim için ayrı bir fonksiyon
def train_and_save_model():
    # Dataset'i yükle
    dataset = load_dataset()
    print(f"Dataset yüklendi. {len(dataset['intent_data'])} farklı intent, "
          f"toplam {sum(len(item['examples']) for item in dataset['intent_data'])} örnek bulunuyor.")
    
    # Modeli eğit ve kaydet
    vectorizer, model = train_model(dataset)
    save_model(model, vectorizer)
    print("Model eğitildi ve kaydedildi!")
    
    return vectorizer, model


# Kullanım için ayrı bir fonksiyon
def use_model():
    # Modeli yüklemeyi dene
    vectorizer, model = load_model()
    
    # Eğer model yoksa, eğit ve kaydet
    if vectorizer is None or model is None:
        print("Kaydedilmiş model bulunamadı. Yeni model eğitiliyor...")
        vectorizer, model = train_and_save_model()
    
    # Dataset'i yükle
    dataset = load_dataset()
    
    # Güven eşiğini belirle
    confidence_threshold = float(input("Güven eşiğini belirleyin (0.0-1.0 arası, önerilen: 0.5): ") or "0.5")
    
    # Kullanıcı arayüzü
    print("\nAsistan başlatıldı! Çıkmak için 'q' yazın.")
    while True:
        user_message = input("\nKullanıcı: ")
        if user_message.lower() == 'q':
            break
        vectorizer, model = handle_message(user_message, vectorizer, model, dataset, confidence_threshold)

    print("\nAsistan kapatıldı!")


# Ana fonksiyon
def main():
    while True:
        print("\n1. Modeli Eğit ve Kaydet")
        print("2. Kaydedilmiş Modeli Kullan")
        print("q. Çıkış")
        
        choice = input("\nSeçiminiz: ")
        
        if choice == "1":
            train_and_save_model()
        elif choice == "2":
            use_model()
        elif choice.lower() == "q":
            break
        else:
            print("Geçersiz seçim!")

    print("Program sonlandırıldı.")


if __name__ == "__main__":
    main()