from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM

# Komutları ve açıklamalarını içeren şablon
template = """
Aşağıdaki cümlede bir komut var mı analiz et. Eğer komut veya komuta yakın bir cümle varsa komut numarasını döndür.
Komut cümleleri genelikle soru cümleleri oluyor. buradaki komutları algıla ve komut numarasını döndür.
Eğer komut yoksa "None" döndür ve cevap kısmını soruda komut olmayan kısmının cevabını döndür. 
Eğer özel bir soru yoksa cevap kısmını da boş bırak.

Komut Listesi: {commands}
Cümle: {question}

Dönüş:
- "Komut Numarası": Tespit edilen komut numarası (eğer yoksa "None").
- "Cevap": Kullanıcının sorusuna uygun bir cevap.
"""



# Komutların tanımlandığı sözlük
commands_dict = {
    "ışıkları aç": 1,
    "ışıkları kapat": 2,
    "klimayı aç": 3,
    "klimayı kapat": 4,
    "tv aç": 5,
    "tv kapat": 6,
}

# Şablonu oluştur
prompt = ChatPromptTemplate.from_template(template)

# Modeli tanımla
model = OllamaLLM(model="aya")

# Zinciri oluştur
chain = prompt | model

# Kullanıcıdan gelen soruyu analiz et
result = chain.invoke({"question": "Sence türkiye nasl bir yer? içerisi çok sıcak oldu klimayı açar mısın?", "commands": commands_dict})

# Sonucu yazdır
print(result)