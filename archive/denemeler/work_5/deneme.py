import librosa
import librosa.display
import numpy as np
import soundfile as sf

y, sr = librosa.load("output_effect.wav", sr=None)
S_full, phase = librosa.magphase(librosa.stft(y))

# Gürültü seviyesini azalt
S_filtered = librosa.decompose.nn_filter(S_full, aggregate=np.median)
y_clean = librosa.istft(S_filtered * phase)
sf.write("output_filtered.wav", y_clean, sr)
