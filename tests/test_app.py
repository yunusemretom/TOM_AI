import numpy as np

import tom.app as app
from tom.audio.vad import EndpointConfig

F = 512
CFG = EndpointConfig(min_speech_ms=96, min_silence_ms=320)


def frames(*spec):
    for p, n in spec:
        for _ in range(n):
            yield np.full(F, p, dtype=np.float32)


class FakeSTT:
    def __init__(self, texts):
        self.texts = list(texts)
        self.heard = []

    def transcribe(self, audio):
        self.heard.append(len(audio))
        return self.texts.pop(0)


class FakeTTS:
    sample_rate = 1000

    def stream(self, text):
        yield np.zeros(100, dtype=np.float32)


def make(monkeypatch, texts, replies):
    prompts = []

    def fake_chat(msgs, model, **kw):
        prompts.append(msgs)
        yield replies.pop(0)

    monkeypatch.setattr(app, "stream_chat", fake_chat)
    bot = app.Assistant(stt=FakeSTT(texts), vad=lambda fr: float(fr[0]), tts=FakeTTS(),
                        llm_model="x", vad_cfg=CFG)
    return bot, prompts


def test_two_turns_keep_history(monkeypatch):
    bot, prompts = make(monkeypatch, ["Merhaba", "Adım Tom"], ["Selam!", "Memnun oldum."])
    played = []
    logs = bot.run(frames((0.0, 5), (0.9, 20), (0.0, 15), (0.9, 20), (0.0, 15)), played.append)

    assert [l.user for l in logs] == ["Merhaba", "Adım Tom"]
    assert prompts[1][-3:] == [
        {"role": "user", "content": "Merhaba"},
        {"role": "assistant", "content": "Selam!"},
        {"role": "user", "content": "Adım Tom"},
    ]
    assert prompts[1][0]["role"] == "system"
    assert len(played) == 2


def test_empty_transcript_does_not_call_llm(monkeypatch):
    bot, prompts = make(monkeypatch, [""], [])
    logs = bot.run(frames((0.9, 20), (0.0, 15)), lambda a: None)
    assert prompts == []
    assert logs[0].timings is None


def test_mic_is_ignored_while_assistant_speaks(monkeypatch):
    bot, prompts = make(monkeypatch, ["Merhaba"], ["Selam!"])
    speaking = iter([True] * 40 + [False] * 1000)
    resumed = []
    logs = bot.run(frames((0.9, 40), (0.0, 5), (0.9, 20), (0.0, 15)), lambda a: None,
                   is_speaking=lambda: next(speaking), on_resume=lambda: resumed.append(1))
    assert len(logs) == 1  # konuşurken gelen 40 kare yok sayıldı
    # 1: asistanın sesi bitince; 2: cevap üretilirken biriken kareler atılsın diye
    assert resumed == [1, 1]
