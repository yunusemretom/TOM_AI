# Gerekli kütüphaneleri yükleyin:
# pip install sentence-transformers numpy

from sentence_transformers import SentenceTransformer, util
import numpy as np

# 1. Modeli yükleyin (Bu model hafif ve yerelde çalışmaya uygun):
model = SentenceTransformer('all-MiniLM-L6-v2')

# 2. Her görev için örnek (prototype) ifadeler tanımlayın:
commands = {
    "lights_on": [
        "ışıkları aç",
        "ışığı aç",
        "ışıkları yak",
        "ışık aç komutunu ver"
    ],
    "lights_off": [
        "ışıkları kapat",
        "ışığı söndür",
        "ışıkları kapat komutunu ver"
    ],
    "play_music": [
        "müzik çal",
        "şarkı çal",
        "müzik başlat",
        "playlist aç"
    ],
    # İhtiyaç duyduğun diğer görevleri buraya ekleyebilirsin.
}

# 3. Her bir görev için prototype ifadelerin vektörlerini önceden hesaplayın:
command_embeddings = {}
for action, phrases in commands.items():
    embeddings = model.encode(phrases, convert_to_tensor=True)
    command_embeddings[action] = embeddings

# 4. Gelen STT verisini alıp, en yüksek benzerlik skoruna sahip görevi belirleyen fonksiyon:
def decide_action(input_text, threshold=0.6):
    input_embedding = model.encode(input_text, convert_to_tensor=True)
    best_action = None
    best_score = 0.0

    for action, embeddings in command_embeddings.items():
        # Her bir prototype ile gelen metin arasındaki benzerliği ölç:
        scores = util.cos_sim(input_embedding, embeddings)
        print(scores)
        max_score = np.max(scores.cpu().numpy())
        if max_score > best_score:
            best_score = max_score
            best_action = action

    if best_score >= threshold:
        return best_action, best_score
    else:
        return None, best_score


def karar_yapisi(text):
    # Örnek STT girdisi (senaryoya göre değiştirebilirsin):
    if (text):
        action, score = decide_action(text)
        
        if action:
            print(f"Seçilen aksiyon: {action} (Benzerlik skoru: {score:.2f})")
        else:
            print("Uygun bir aksiyon bulunamadı.")


# 5. Ana fonksiyon ile örnek çalıştırma:
if __name__ == "__main__":
    while True:

        karar_yapisi(input("girdi gir: "))
