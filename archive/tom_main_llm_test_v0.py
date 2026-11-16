from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM
import os
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)


llm_model = OllamaLLM(model="gemma3:4b")

template = """
Analyze if there is one or more commands in the sentence. Return the command number(s) if any commands are detected. 
If it's a question or regular statement without a command, generate an appropriate response to the question or statement.
If there is no command, return "None" and provide a relevant response to the user's input.
If multiple commands are present, return all command numbers as a list.

Komut Listesi: {commands}
Cümle: {question}

Dönüş:
- "Komut Numarası": List of detected command numbers (e.g., [1, 2]) or "None" if not present.
- "Yanıt": A response to the user's statement or question (Answers should be in Turkish).
"""


prompt = ChatPromptTemplate.from_template(template)

# Komutları önceden tanımla
commands_dict = {
    "ışıkları aç": 1,
    "ışıkları kapat": 2, 
    "klimayı aç": 3,
    "klimayı kapat": 4,
    "tv aç": 5,
    "tv kapat": 6,
}


def yanit(question):
    chain = prompt | llm_model
    return chain.invoke({"question": question, "commands": commands_dict})


while True:
    try:
        metin = input("Bir cümle girin: ")
        if metin and len(metin) > 0:  # metin listesi boş değilse
            son_metin=metin # listenin son elemanını al
            print("Gelen veri:", son_metin)
            responsive = yanit(son_metin)
            print("gelen yanit:", responsive)
            
            cevap_kismi = responsive.split("Cevap", 1)[1] if "Cevap" in responsive else None
            if cevap_kismi:
                print(cevap_kismi)
            print()

    except Exception as e:
        print(e)
