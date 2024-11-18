import argparse
import io
import speech_recognition as sr
from faster_whisper import WhisperModel
from datetime import datetime, timedelta
from queue import Queue
from time import sleep
from tempfile import NamedTemporaryFile

parser = argparse.ArgumentParser()
parser.add_argument("--model", default="large", help="Model to use",
                    choices=["tiny", "base", "small", "medium", "large"])
parser.add_argument("--device", default="auto", help="Device to use for inference",
                    choices=["auto", "cuda", "cpu"])
parser.add_argument("--energy_threshold", default=1000,
                    help="Energy level for mic to detect.", type=int)
parser.add_argument("--record_timeout", default=2,
                    help="How real time the recording is in seconds.", type=float)
parser.add_argument("--phrase_timeout", default=3,
                    help="How much empty space between recordings before we "
                            "consider it a new line in the transcription.", type=float)
parser.add_argument("--language", default="tr", help="Language to use for transcription",
                    choices=["tr", "en","auto"])
args = parser.parse_args()

# Initialize necessary components
phrase_time = None
last_sample = bytes()
data_queue = Queue()
recorder = sr.Recognizer()
recorder.energy_threshold = args.energy_threshold
recorder.dynamic_energy_threshold = False

source = sr.Microphone(sample_rate=16000)

model = args.model
device = args.device
audio_model = WhisperModel(model, device=device)

record_timeout = args.record_timeout
phrase_timeout = args.phrase_timeout

temp_file = NamedTemporaryFile().name
transcription = ['']

with source:
    recorder.adjust_for_ambient_noise(source)

def record_callback(_, audio: sr.AudioData) -> None:
    data = audio.get_raw_data()
    data_queue.put(data)

recorder.listen_in_background(source, record_callback, phrase_time_limit=record_timeout)

print("Model loaded. Ready to transcribe.")

def sesanalizi():
    global phrase_time, last_sample, data_queue, recorder, source, model, device, audio_model, temp_file, transcription
    transcription = ['']
    try:
        now = datetime.utcnow()
        if not data_queue.empty():
            phrase_complete = False
            if phrase_time and now - phrase_time > timedelta(seconds=phrase_timeout):
                last_sample = bytes()
                phrase_complete = True
            phrase_time = now

            while not data_queue.empty():
                data = data_queue.get()
                last_sample += data

            audio_data = sr.AudioData(last_sample, source.SAMPLE_RATE, source.SAMPLE_WIDTH)
            wav_data = io.BytesIO(audio_data.get_wav_data())
            
            with open(temp_file, 'w+b') as f:
                f.write(wav_data.read())
            
            segments, _ = audio_model.transcribe(temp_file,language="tr")
            text = " ".join([segment.text for segment in segments])

            if phrase_complete:
                if text=="Altyazı M.K.":
                    pass
                else:
                    transcription.append(text)
            else:
                transcription[-1] = text
            return transcription
            
            for line in transcription:
                print(line)
            transcription = ['']

            print('', end='', flush=True)

            sleep(0.25)
    except Exception as e:
        print(f"Error: {e}")
    except KeyboardInterrupt:
        exit()



if __name__ == "__main__":
    while True: 
        
        a = sesanalizi()
        if a != None:
            print(a) 