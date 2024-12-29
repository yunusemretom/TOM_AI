from fuzzywuzzy import fuzz
import re

# Komutların bir sözlükte tanımlanması
COMMANDS = {
    "Işıkları açar mısın": "turn_on_light()",
    "Müzik çalar mısın": "play_music()",
    "Kapıları açar mısın": "open_doors()",
    # Diğer komutlar eklenebilir...
}

# Komut fonksiyonları simülasyonu
def turn_on_light():
    print("Işıklar açıldı.")

def play_music():
    print("Müzik çaldı.")

def open_doors():
    print("Kapılar açıldı.")

# Noktalama işaretlerine göre cümleyi parçalara ayıran fonksiyon
def split_sentence(sentence):
    # Cümleyi noktalama işaretlerine göre ayırıyoruz
    return re.split(r'([?.!])', sentence)  # Noktalama işaretlerini koruyarak ayırıyoruz


# Noktalama işaretlerine göre cümleyi parçalara ayıran fonksiyon
def split_sentence(sentence):
    # Cümleyi noktalama işaretlerine göre ayırıyoruz
    return re.split(r'([?.!])', sentence)  # Noktalama işaretlerini koruyarak ayırıyoruz

# Komutları çıkaran ve geriye kalan metni LLM modeline gönderen işlem
def process_input(input_text,COMMANDS):
    # Cümleyi noktalama işaretlerine göre parçalara ayır
    parts = split_sentence(input_text)
    print(parts)
    command = None
    best_match_score = 65
    best_command = ""
    
    # Her bir parça ile komutları karşılaştır
    for part in parts:
        for key in COMMANDS.keys():
            score = fuzz.ratio(part.lower(), key.lower())  # Benzerlik oranı
            
            if score > best_match_score:
                print(score)
                best_match_score = score
                best_command = key
                command_text = part
    
    # Eğer benzerlik %75'in üzerindeyse, komutu çıkart
    if best_match_score > 65:
        print(f"Komut bulundu: {command_text} (Benzerlik: {best_match_score}%)")
        # Komutu çıkar
        input_text = input_text.replace(command_text, "").strip()

        # Çıkan komutu çalıştır
        exec(COMMANDS[best_command])
    
    # Geriye kalan metni LLM modeline gönder
    print(f"Geriye kalan metin LLM modeline gönderiliyor: {input_text}")
    return(input_text)
    # Burada LLM modeline geriye kalan metni gönderebilirsiniz (örneğin, OpenAI API)
    # response = llm_model.generate(input_text)
    # print(f"LLM yanıtı: {response}")


