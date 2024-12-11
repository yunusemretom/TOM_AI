import argparse
import io
import speech_recognition as sr
from faster_whisper import WhisperModel
from datetime import datetime, timedelta
from queue import Queue
from time import sleep
from tempfile import NamedTemporaryFile
from typing import List, Optional

# Argüman parser'ı oluştur ve varsayılan değerleri ayarla
parser = argparse.ArgumentParser()
parser.add_argument("--model", default="large", choices=["tiny", "base", "small", "medium", "large"])
parser.add_argument("--device", default="auto", choices=["auto", "cuda", "cpu"]) 
parser.add_argument("--energy_threshold", default=1000, type=int)
parser.add_argument("--record_timeout", default=2, type=float)
parser.add_argument("--phrase_timeout", default=3, type=float)
parser.add_argument("--language", default="tr", choices=["tr", "en", "auto"])
args = parser.parse_args()

class AudioTranscriber:
    def __init__(self):
        self.phrase_time = None
        self.last_sample = bytes()
        self.data_queue = Queue()
        self.transcription = ['']
        
        # Recognizer ayarları
        self.recorder = sr.Recognizer()
        self.recorder.energy_threshold = args.energy_threshold
        self.recorder.dynamic_energy_threshold = False
        
        # Mikrofon kaynağı
        self.source = sr.Microphone(sample_rate=16000)
        with self.source:
            self.recorder.adjust_for_ambient_noise(self.source)
            
        # Model ayarları    
        self.audio_model = WhisperModel(args.model, device=args.device)
        self.temp_file = NamedTemporaryFile().name
        
        # Callback fonksiyonunu başlat
        self.recorder.listen_in_background(
            self.source, 
            self._record_callback,
            phrase_time_limit=args.record_timeout
        )
        
        print("Model loaded. Ready to transcribe.")

    def _record_callback(self, _, audio: sr.AudioData) -> None:
        self.data_queue.put(audio.get_raw_data())

    def process_audio(self) -> Optional[List[str]]:
        try:
            now = datetime.utcnow()
            if self.data_queue.empty():
                return None
                
            # Phrase tamamlanma kontrolü    
            phrase_complete = False
            if self.phrase_time and now - self.phrase_time > timedelta(seconds=args.phrase_timeout):
                self.last_sample = bytes()
                phrase_complete = True
            self.phrase_time = now

            # Ses verilerini topla
            while not self.data_queue.empty():
                self.last_sample += self.data_queue.get()

            # Ses verisini işle
            audio_data = sr.AudioData(self.last_sample, self.source.SAMPLE_RATE, self.source.SAMPLE_WIDTH)
            wav_data = io.BytesIO(audio_data.get_wav_data())
            
            with open(self.temp_file, 'w+b') as f:
                f.write(wav_data.read())
            
            # Transcribe et
            segments, _ = self.audio_model.transcribe(self.temp_file, language="tr")
            text = " ".join([segment.text for segment in segments])

            # Sonucu işle
            if text != "Altyazı M.K.":
                if phrase_complete:
                    self.transcription.append(text)
                else:
                    self.transcription[-1] = text
                    
            return self.transcription

        except Exception as e:
            print(f"Error: {e}")
            return None
        except KeyboardInterrupt:
            exit()

if __name__ == "__main__":
    transcriber = AudioTranscriber()
    while True:
        result = transcriber.process_audio()
        if result:
            print(result)
        sleep(0.1)