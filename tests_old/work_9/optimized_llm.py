from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM
from typing import Dict, Optional
import functools

class OptimizedLLMHandler:
    def __init__(self, model_name="llama2:13b-chat-q4_K_M"):
        # Model optimizasyonları
        self.model = OllamaLLM(
            model=model_name,
            temperature=0.7,
            top_k=10,
            top_p=0.9,
            repeat_penalty=1.1,
            num_ctx=2048  # Bağlam penceresi
        )
        
        # Komut şablonu
        self.template = """
        Aşağıdaki cümlede bir komut var mı analiz et. Kısa ve öz cevap ver.
        Komut Listesi: {commands}
        Cümle: {question}
        
        Dönüş:
        - "Komut": {commands} içinden tespit edilen komut (yoksa "yok")
        - "Yanıt": Kısa yanıt
        """
        
        self.prompt = ChatPromptTemplate.from_template(self.template)
        self.chain = self.prompt | self.model
        
        # Önbellekleme için decorator
        self.process = functools.lru_cache(maxsize=100)(self._process)

    def _process(self, question: str, commands: Dict) -> Optional[str]:
        try:
            return self.chain.invoke({
                "question": question,
                "commands": commands
            })
        except Exception as e:
            print(f"LLM Error: {e}")
            return None

    def clear_cache(self):
        """Önbelleği temizle"""
        self.process.cache_clear()
