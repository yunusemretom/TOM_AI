# Denklem üzerinden ilerleyerek olası dizileri bulalım!
import math

# Koşulları tanımlayalım
a1 = 4
a11 = 1024
sequence_count = 0

# Denklemden yola çıkarak çözüm bulalım
def find_sequences(a1, a11):
    sequences = []

    def backtrack(seq):
        if len(seq) == 11:
            if seq[-1] == a11:
                sequences.append(seq[:])
            return
        
        # Denklemden yeni terimi hesapla
        a_prev = seq[-1]
        sqrt_product = math.sqrt(a_prev * a_prev * (25/4))
        
        # Olası iki çözüm
        a_next1 = (5/2) * sqrt_product - a_prev
        a_next2 = (5/2) * sqrt_product + a_prev

        # Pozitif reel sayıları alalım
        for a_next in [a_next1, a_next2]:
            if a_next > 0:
                seq.append(a_next)
                backtrack(seq)
                seq.pop()

    # İlk terimle başla
    backtrack([a1])
    
    return sequences

# Çözümleri bulalım
sequences = find_sequences(a1, a11)
sequence_count = len(sequences)

# Çözüm sayısının son iki basamağını alalım
last_two_digits = sequence_count % 100
last_two_digits

print(sequences)