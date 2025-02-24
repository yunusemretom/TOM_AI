import pickle
import numpy as np

class NLPModel:
    def __init__(self, model_path='nlp_model.pkl', vectorizer_path='vectorizer.pkl'):
        # Model dosya yolları
        self.model_path = model_path
        self.vectorizer_path = vectorizer_path
        self.model = None
        self.vectorizer = None
        
        # Modeli ve vektörleştiriciyi yükle
        self._load_model()
    
    def _load_model(self):
        """Kaydedilmiş modeli ve vektörleştiriciyi yükler."""
        try:
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            
            with open(self.vectorizer_path, 'rb') as f:
                self.vectorizer = pickle.load(f)
            
            return True
        except Exception as e:
            print(f"Model yüklenirken hata oluştu: {e}")
            return False
    
    def predict(self, text):
        """Verilen metni sınıflandırır.
        
        Args:
            text (str): Sınıflandırılacak metin
            
        Returns:
            dict: Intent adı, güven değeri ve alternatifler içeren sözlük
        """
        if self.model is None or self.vectorizer is None:
            return {"success": False, "error": "Model yüklenemedi"}
        
        try:
            # Metni vektöre dönüştür
            X_input = self.vectorizer.transform([text])
            
            # Tahmin yap
            predicted_intent = self.model.predict(X_input)[0]
            
            # Tüm olasılıkları al
            all_probs = self.model.predict_proba(X_input)[0]
            confidence = all_probs.max()
            
            # Intent indekslerini sırala
            intent_indices = np.argsort(all_probs)[::-1]
            
            # Sınıf etiketlerini al
            class_labels = self.model.classes_
            
            # Alternatifler listesi oluştur (en iyi 3)
            alternatives = []
            for idx in intent_indices[:3]:
                intent_name = class_labels[idx]
                probability = all_probs[idx]
                alternatives.append({
                    "intent": intent_name,
                    "confidence": float(probability)
                })
            
            return {
                "success": True,
                "intent": predicted_intent,
                "confidence": float(confidence),
                "alternatives": alternatives
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}


# Kullanım örneği
if __name__ == "__main__":
    # Modeli yükle
    nlp = NLPModel()
    
    # Test et
    test_message = "şarkı"
    result = nlp.predict(test_message)
    
    if result["success"]:
        print(f"Metin: '{test_message}'")
        print(f"Tahmin edilen intent: {result['intent']}")
        print(f"Güven değeri: {result['confidence']:.4f}")
        
        print("\nAlternatifler:")
        for alt in result["alternatives"]:
            print(f"- {alt['intent']}: {alt['confidence']:.4f}")
    else:
        print(f"Hata: {result['error']}")