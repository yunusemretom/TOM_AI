from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM

# Komutları ve açıklamalarını içeren şablon
template = """
Analyze the following sentence in Turkish. Identify if it contains a command from the command list and provide the following:
- Command Number: (Return "None" if no command is found.)
- Answer: If there is no command but a question or statement exists, provide an answer for it.

Command List: {commands}
Sentence: "{question}"

Output in English, structured as follows:
- "Command Number": Detected command number or "None".
- "Answer": Appropriate response to the user's input.

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
model = OllamaLLM(model="phi3:mini")

# Zinciri oluştur
chain = prompt | model

# Kullanıcıdan gelen soruyu analiz et
result = chain.invoke({"question": "What do you think Türkiye is like? It's very hot inside, can you turn on the air conditioner?", "commands": commands_dict})

# Sonucu yazdır
print(result)