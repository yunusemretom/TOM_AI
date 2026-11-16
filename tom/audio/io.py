"""Mikrofon girişi ve hoparlör çıkışı (sounddevice / PortAudio).

`MicStream`: 16 kHz mono, VAD'ın beklediği 512 örneklik kareler halinde kuyruğa yazar.
`Player`: parça parça gelen TTS sesini kesintisiz çalar; `stop()` ile anında susar
(kullanıcı araya girdiğinde), `busy` ile hâlâ çalıp çalmadığı sorulur.
"""

from __future__ import annotations

import queue
import threading
from collections import deque

import numpy as np


class MicStream:
    def __init__(self, sample_rate: int = 16000, frame: int = 512, device=None):
        import sounddevice as sd

        self.frames: queue.Queue[np.ndarray] = queue.Queue()
        self.overflows = 0

        def cb(indata, n, t, status):
            if status.input_overflow:
                self.overflows += 1
            self.frames.put(indata[:, 0].copy())

        self.stream = sd.InputStream(
            samplerate=sample_rate, channels=1, dtype="float32", blocksize=frame,
            callback=cb, device=device,
        )

    def __enter__(self):
        self.stream.start()
        return self

    def __exit__(self, *a):
        self.stream.stop()
        self.stream.close()

    def drain(self) -> None:
        """Bekleyen kareleri at (ör. asistan konuşurken birikenler)."""
        while True:
            try:
                self.frames.get_nowait()
            except queue.Empty:
                return


class Player:
    def __init__(self, sample_rate: int = 24000, device=None):
        import sounddevice as sd

        self._buf: deque[np.ndarray] = deque()
        self._off = 0
        self._lock = threading.Lock()
        self.sample_rate = sample_rate
        self.stream = sd.OutputStream(
            samplerate=sample_rate, channels=1, dtype="float32", callback=self._cb,
            device=device, blocksize=1024,
        )
        self.stream.start()

    def _cb(self, out, n, t, status):
        out.fill(0)
        i = 0
        with self._lock:
            while i < n and self._buf:
                a = self._buf[0]
                take = min(n - i, len(a) - self._off)
                out[i : i + take, 0] = a[self._off : self._off + take]
                i += take
                self._off += take
                if self._off >= len(a):
                    self._buf.popleft()
                    self._off = 0

    def play(self, chunk: np.ndarray) -> None:
        with self._lock:
            self._buf.append(np.asarray(chunk, dtype=np.float32).reshape(-1))

    @property
    def busy(self) -> bool:
        with self._lock:
            return bool(self._buf)

    def stop(self) -> None:
        with self._lock:
            self._buf.clear()
            self._off = 0

    def close(self) -> None:
        self.stream.stop()
        self.stream.close()
