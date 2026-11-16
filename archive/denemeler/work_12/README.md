# NLP Model Assistant 🤖

Bu proje, kullanıcıdan gelen mesajları anlamak ve yanıtlamak için bir NLP (Doğal Dil İşleme) modeli kullanmaktadır. Aşağıda, projede bulunan dosyaların açıklamaları yer almaktadır.

## Dosyalar 📁

### 1. `karar_m_2.1.py`
- Bu script, bir intent veri setini yükler, Naive Bayes modelini eğitir ve kullanıcı mesajlarını işler. 
- Kullanıcıdan gelen girdilere göre yeni intent'ler öğrenme ve alternatif intent önerileri sunma işlevselliğine sahiptir.

### 2. `karar_m_2.py`
- `karar_m_2.1.py` ile benzer işlevselliğe sahiptir, ancak kullanıcı geri bildirimlerini daha iyi işleyerek intent tahminlerini güncelleyebilir.
- Daha geniş bir intent ve örnek seti içerir.

### 3. `save_model.py`
- Bu script, eğitilmiş modeli ve vektörleştiriciyi kaydetmek ve yüklemek için kullanılır.
- Modelin disk üzerinde saklanmasını ve gelecekteki tahminler için yüklenmesini sağlar.

### 4. `test.py`
- `NLPModel` sınıfını tanımlar ve modelin yüklenmesi ile tahmin işlevselliğini kapsüller.
- Kullanıcıdan gelen metinleri sınıflandırmak için temiz bir arayüz sunar.

## Kullanım 🚀
- Projeyi çalıştırmak için `karar_m_2.py` veya `karar_m_2.1.py` dosyalarından birini kullanabilirsiniz.
- Model, kullanıcıdan gelen mesajları anlamak için eğitilmiş olup, yeni intent'ler öğrenebilir.

## Geliştirme 💻
- Proje, Python ve scikit-learn kütüphanesini kullanarak geliştirilmiştir.
- Yeni intent'ler eklemek veya mevcut intent'leri güncellemek için kullanıcıdan geri bildirim alır.

## İletişim 📫
- Herhangi bir sorun veya öneri için iletişime geçebilirsiniz.
