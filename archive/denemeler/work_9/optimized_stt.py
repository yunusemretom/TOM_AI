import numpy as np
import speech_recognition as sr
from faster_whisper import WhisperModel
from datetime import datetime, timedelta
from queue import Queue
import io
from typing import List, Optional
import torch

class OptimizedAudioTranscriber:
    def __init__(self, model_size="medium"):
        self.phrase_time = None
        self.last_sample = bytes()
        self.data_queue = Queue()
        self.transcription = ['']
        
        # Daha verimli recognizer ayarları
        self.recorder = sr.Recognizer()
        self.recorder.energy_threshold = 1000
        self.recorder.dynamic_energy_threshold = False
        
        # Mikrofon kaynağını bir kez başlat
        self.source = sr.Microphone(sample_rate=16000)
        
        # Model optimizasyonları
        compute_type = "float16" if torch.cuda.is_available() else "int8"
        self.audio_model = WhisperModel(
            model_size,
            device="cuda" if torch.cuda.is_available() else "cpu",
            compute_type=compute_type,
            num_workers=2  # CPU thread sayısı
        )
        
        # Bellek içi işlem için buffer
        self.audio_buffer = io.BytesIO()
        
        # Başlangıç kalibrasyonu
        with self.source:
            self.recorder.adjust_for_ambient_noise(self.source)
        
        # Arka plan dinlemeyi başlat
        self.recorder.listen_in_background(
            self.source, 
            self._record_callback,
            phrase_time_limit=2
        )

    def _record_callback(self, _, audio: sr.AudioData) -> None:
        # Ses verilerini doğrudan kuyruğa ekle
        self.data_queue.put(audio.get_raw_data())

    def process_audio(self, phrase_timeout=3.0) -> Optional[List[str]]:
        try:
            now = datetime.utcnow()
            if self.data_queue.empty():
                return None
            
            # Cümle tamamlanma kontrolü
            phrase_complete = False
            if self.phrase_time and now - self.phrase_time > timedelta(seconds=phrase_timeout):
                self.last_sample = bytes()
                phrase_complete = True
            self.phrase_time = now

            # Ses verilerini topla
            while not self.data_queue.empty():
                self.last_sample += self.data_queue.get()

            if len(self.last_sample) == 0:
                return None

            # Ses verisini bellek içinde işle
            audio_data = sr.AudioData(self.last_sample, self.source.SAMPLE_RATE, self.source.SAMPLE_WIDTH)
            wav_data = io.BytesIO(audio_data.get_wav_data())
            
            # Transcribe işlemi - optimize edilmiş parametrelerle
            segments, _ = self.audio_model.transcribe(
                wav_data.read(),
                language="tr",
                beam_size=1,  # Hızlı işlem için
                vad_filter=True,  # Sessiz bölümleri filtrele
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            text = " ".join(segment.text for segment in segments)

            # Sonucu işle ve döndür
            if text.strip():
                if phrase_complete:
                    self.transcription.append(text)
                else:
                    self.transcription[-1] = text
                return self.transcription

            return None

        except Exception as e:
            print(f"Error in audio processing: {e}")
            return None
