import time

import numpy as np
import pytest

from tom.brain.sentence_splitter import SentenceSplitter
from tom.pipeline.respond import respond


class FakeTTS:
    sample_rate = 1000

    def __init__(self, gen_delay=0.0):
        self.gen_delay = gen_delay
        self.calls = []

    def stream(self, text):
        self.calls.append(text)
        time.sleep(self.gen_delay)
        yield np.zeros(500, dtype=np.float32)  # 0,5 sn ses
        yield np.zeros(500, dtype=np.float32)


def slow_llm(pieces, delay):
    for p in pieces:
        time.sleep(delay)
        yield p


def test_first_sentence_is_spoken_before_llm_finishes():
    pieces = ["Merhaba", "!", " Bugün", " hava", " çok", " güzel", ".", " Yarın", " yağmur", " var", "."]
    tts = FakeTTS()
    out = []
    tm = respond(slow_llm(pieces, 0.02), tts, out.append, SentenceSplitter(first_min_chars=999))

    assert tts.calls == ["Merhaba!", "Bugün hava çok güzel.", "Yarın yağmur var."]
    assert tm.first_audio < tm.llm_done  # ilk ses, LLM bitmeden çıktı
    assert tm.text == "".join(pieces)
    assert tm.audio_seconds == pytest.approx(3.0)
    assert len(out) == 6


def test_stall_is_counted_when_tts_is_slower_than_playback():
    tts = FakeTTS(gen_delay=0.8)  # her cümle 0,8 sn gecikiyor, ses 1 sn
    tm = respond(iter(["Bir. İki. "]), tts, splitter=SentenceSplitter(first_min_chars=999))
    assert tts.calls == ["Bir.", "İki."]
    assert tm.stall_seconds == pytest.approx(0.0, abs=0.1)  # 0,8 < 1,0: yetişiyor

    tts = FakeTTS(gen_delay=1.3)
    tm = respond(iter(["Bir. İki. "]), tts, splitter=SentenceSplitter(first_min_chars=999))
    assert tm.stall_seconds == pytest.approx(0.3, abs=0.1)


def test_llm_error_is_raised_in_caller():
    def broken():
        yield "Merhaba. "
        raise ConnectionError("ollama kapalı")

    with pytest.raises(ConnectionError):
        respond(broken(), FakeTTS())
