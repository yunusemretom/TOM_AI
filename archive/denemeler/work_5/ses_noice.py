from scipy.io import wavfile
import noisereduce as nr
# load data
rate, data = wavfile.read(r"audio_cache\cache_75dc59032ec622f4c19523369e5fdb71.wav")
# perform noise reduction
reduced_noise = nr.reduce_noise(y=data, sr=rate)
wavfile.write("mywav_reduced_noise.wav", rate, reduced_noise)

# Örnek olarak HiFi-GAN kullanarak ses sentezleme
import torchaudio

model = torchaudio.pipelines.TACOTRON2_WAVEGLOW_22050Hz()
waveform, sample_rate = torchaudio.load("mywav_reduced_noise.wav")
improved_waveform = model.infer(waveform)
torchaudio.save("output_improved.wav", improved_waveform, sample_rate)

