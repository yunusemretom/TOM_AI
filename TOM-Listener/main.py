import sys
import io
import argparse
import speech_recognition as sr
from faster_whisper import WhisperModel
from datetime import datetime, timedelta
from queue import Queue
from time import sleep
from tempfile import NamedTemporaryFile
from typing import List, Optional

from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QFont, QPalette, QColor
from PySide6.QtWidgets import (QApplication, QLabel, QVBoxLayout, 
                               QWidget, QMainWindow, QSizePolicy,
                               QPushButton, QHBoxLayout)

# Argüman parser'ı oluştur ve varsayılan değerleri ayarla
parser = argparse.ArgumentParser()
parser.add_argument("--model", default="distil-large-v3", choices=["tiny", "base", "small", "medium", "large"])
parser.add_argument("--device", default="auto", choices=["auto", "cuda", "cpu"]) 
parser.add_argument("--energy_threshold", default=1000, type=int)
parser.add_argument("--record_timeout", default=2, type=float)
parser.add_argument("--phrase_timeout", default=3, type=float)
parser.add_argument("--language", default="tr", choices=["tr", "en", "auto"])
parser.add_argument("--font_size", default=18, type=int)
parser.add_argument("--text_color", default="white")
parser.add_argument("--max_lines", default=3, type=int)
args = parser.parse_args()

class TranscriptionSignals(QObject):
    update_text = Signal(str)

class AudioTranscriber:
    def __init__(self, signals):
        self.signals = signals
        self.phrase_time = None
        self.last_sample = bytes()
        self.data_queue = Queue()
        self.transcription = ['']
        
        # Recognizer ayarları
        self.recorder = sr.Recognizer()
        self.recorder.energy_threshold = args.energy_threshold
        self.recorder.dynamic_energy_threshold = False
        
        # Mikrofon kaynağı
        self.source = sr.Microphone(sample_rate=16000, device_index=2)
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

    def process_audio(self) -> None:
        try:
            now = datetime.utcnow()
            if self.data_queue.empty():
                return
                
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
            segments, _ = self.audio_model.transcribe(self.temp_file, language=args.language)
            text = " ".join([segment.text for segment in segments])

            # Sonucu işle
            if "Altyazı M.K." not in text:
                if phrase_complete:
                    self.transcription.append(text)
                else:
                    self.transcription[-1] = text
                
                # Son birkaç mesajı göster (args.max_lines kadar)
                display_text = "\n".join(self.transcription[-args.max_lines:])
                self.signals.update_text.emit(display_text)

        except Exception as e:
            print(f"Error: {e}")
        except KeyboardInterrupt:
            exit()

class TransparentWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Pencere ayarları
        self.setWindowTitle("Canlı Transkripsiyon")
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint | 
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        
        # Ana widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_widget.setAttribute(Qt.WA_TranslucentBackground)
        
        # Ana layout
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Üst çubuk için layout
        self.top_bar = QHBoxLayout()
        self.main_layout.addLayout(self.top_bar)
        
        # Boşluk ekle (sol tarafı doldurmak için)
        self.top_bar.addStretch(1)
        
        # Kapatma düğmesi
        self.close_button = QPushButton("×")
        self.close_button.setFixedSize(20, 20)
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #FF5555;
                font-weight: bold;
                font-size: 16px;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 85, 85, 0.3);
                border-radius: 10px;
            }
        """)
        self.close_button.clicked.connect(self.close_panel)
        self.top_bar.addWidget(self.close_button)
        
        # Metin etiketi
        self.text_label = QLabel("Konuşmayı algılıyor...")
        self.text_label.setWordWrap(True)
        self.text_label.setStyleSheet(f"color: {args.text_color}; background-color: transparent;")
        self.text_label.setFont(QFont("Arial", args.font_size))
        self.text_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.text_label.setAlignment(Qt.AlignBottom | Qt.AlignLeft)
        self.main_layout.addWidget(self.text_label)
        
        # Pencere boyutu
        self.resize(800, 200)
        
        # Pencereyi ekranın alt kısmına yerleştir
        desktop = QApplication.primaryScreen().geometry()
        self.move(desktop.width() // 2 - self.width() // 2, 
                  desktop.height() - self.height() - 100)
    
    def update_text(self, text):
        self.text_label.setText(text)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Kapatma düğmesi üzerinde tıklama değilse
            if not self.close_button.geometry().contains(event.position().toPoint()):
                self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
        
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and hasattr(self, 'drag_position'):
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    def close_panel(self):
        exit()
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Sinyal nesnesi
    signals = TranscriptionSignals()
    
    # Pencere oluştur
    window = TransparentWindow()
    window.show()
    
    # Ses transkripsiyonunu başlat
    transcriber = AudioTranscriber(signals)
    
    # Sinyal bağlantısı
    signals.update_text.connect(window.update_text)
    
    # Düzenli aralıklarla ses işleme
    timer = QTimer()
    timer.timeout.connect(transcriber.process_audio)
    timer.start(100)  # Her 100ms'de bir çalıştır
    
    sys.exit(app.exec())