"""import ollama

# Ollama istemcisini başlat
ollama_client = ollama.Client()

# Ollama'nın karar vermesini istediğimiz sınıf
class Agent:
    def __init__(self, role, model="llama3.1"):
        self.role = role
        self.model = model

    def generate(self, prompt):
        # Ollama ile metin üret ve sonucu döndür
        return ollama_client.generate(prompt=prompt, system=self.role, model=self.model, stream=False)["response"]

# Yeni AI ajanı oluştur
Ada = Agent(role=(
    "Merhaba, benim adım Ada. "
    "Ben senin zeki ve kullanıcı dostu AI asistanınım. "
    "Sana projelerinde rehberlik edebilir, teknik çözümler sunabilir ve yaratıcı fikirler sağlayabilirim. "
    "Sorularını çözmek ve işlerindeki yükü azaltmak için buradayım. "
    "Sade, anlaşılır ve hızlı bir şekilde sana yardımcı olmaya odaklanıyorum."
    "Bana söylediğin cümleye göre sana hangi fonskiyonu çalıştırman gerektiğini önerebilirim: Saat kaç fonskiyonu, ses düzenleme fonksiyonu "
))


ollama_response = Ada.generate("saatin kaç olduğunu öğrenmek istiyorum")
print(ollama_response)
"""

import ollama




response = ollama.chat(
    model='llama3.1',
    messages=[{'role': 'user', 'content': 'merhaba nasılsın'}],

		# provide a weather checking tool to the model
    tools=[{
      'type': 'function',
      'function': {
        'name': 'get_current_weather',
        'description': 'Get the current weather for a city',
        'parameters': {
          'type': 'object',
          'properties': {
            'city': {
              'type': 'string',
              'description': 'The name of the city',
            },
          },
          'required': ['city'],
        },
      },
    },
  ],

)

print("eehe",response['message'])