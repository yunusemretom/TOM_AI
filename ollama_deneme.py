import ollama  # Ollama kütüphanesini içe aktar

class agent():  # Agent sınıfını tanımla
  def __init__(self, role, model="llama3.1"):  # Yapıcı metodu tanımla
    self.role = role  # Role özelliğini ayarla
    self.model = model  # Model özelliğini ayarla
  def generate(self, prompt):  # Metin üretme metodunu tanımla
    return ollama.generate(prompt=prompt, system=self.role, 
      model=self.model, stream=False)["response"]  # Ollama ile metin üret ve yanıtı döndür

Naz = agent(role="Senin adın Naz, süper akıllısın ve yardım etmeyi çok seviyorsun. cilve yapmaya bayılıyorsun. cinsiyetin kız. sorulara kısa cevap veriyorsun.")  # Naz adında bir agent nesnesi oluştur

print(Naz.generate("bir sorun mu var"))  # Naz'a soru sor ve yanıtı yazdır