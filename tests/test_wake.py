import numpy as np
import pytest

import tom.app as app
from tom.wake import WakeGate, is_sleep_command, strip_wake
from test_app import CFG, FakeSTT, FakeTTS, frames


@pytest.mark.parametrize("text,rest", [
    ("Hey Tom, saat kaç?", "Saat kaç?"), ("hey tom hava nasıl", "Hava nasıl"), ("Tom, YouTube'u aç.", "YouTube'u aç."),
    ("Hey Tam bana bir fıkra anlat", "Bana bir fıkra anlat"), ("Hey Tom.", ""), ("Hei Tom! Merhaba", "Merhaba"),
])
def test_wake_word_variants(text, rest):
    assert strip_wake(text) == (True, rest)


@pytest.mark.parametrize("text", ["Bugün hava güzel.", "Tomurcuklar açtı.", "Atom bombası", "Tamam o zaman"])
def test_no_wake_word(text):
    assert strip_wake(text)[0] is False


def test_sleep_commands():
    for t in ["Uyu", "Artık uyuyabilirsin", "Uyku moduna geç", "Beni dinleme"]:
        assert is_sleep_command(t), t
    assert not is_sleep_command("Uyumadan önce hatırlat")


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def test_gate_window_media_and_sleep():
    c = Clock()
    g = WakeGate(window_s=40, idle_sleep_s=600, clock=c)
    assert not g.check("Saat kaç?").listen                       # pencere kapalı
    d = g.check("Hey Tom saat kaç?")
    assert d.listen and d.text == "Saat kaç?"
    c.t = 30
    assert g.check("Peki yarın?").listen                          # pencere içinde
    c.t = 35
    assert not g.check("Peki yarın?", media_playing=True).listen  # video çalarken pencere yok
    c.t = 100
    assert not g.check("Hâlâ orada mısın?").listen               # pencere kapandı
    g.sleep()
    assert not g.check("Saat kaç?").listen
    d = g.check("Hey TOM")
    assert d.listen and d.woke and d.text == ""
    c.t = 1000
    assert g.should_auto_sleep()


def make_bot(monkeypatch, texts):
    monkeypatch.setattr(app, "stream_chat", lambda msgs, model, **kw: iter(["Tamam."]))
    bot = app.Assistant(stt=FakeSTT(texts), vad=lambda fr: float(fr[0]), tts=FakeTTS(), llm_model="x", vad_cfg=CFG)
    c = Clock()
    bot.wake = WakeGate(window_s=40, idle_sleep_s=600, clock=c)
    events = []
    bot.on_sleep = lambda: events.append("sleep")
    bot.on_wake = lambda: events.append("wake")
    return bot, c, events


def utter(n):
    return [(0.9, 20), (0.0, 15)] * n


def test_assistant_ignores_without_wake_and_sleeps_on_command(monkeypatch):
    bot, c, events = make_bot(monkeypatch, ["Videodaki adam konuşuyor.", "Hey Tom merhaba", "Uyu",
                                            "Saat kaç?", "Hey Tom"])
    logs = bot.run(frames(*utter(5)), lambda a: None)
    assert "yok sayıldı" in logs[0].line()                       # uyandırma kelimesi yok
    assert logs[1].user == "Merhaba" and logs[1].timings is not None
    assert logs[2].skills == ["uyku"] and bot.wake.asleep is False or events == ["sleep", "wake"]
    assert "uykuda" in logs[3].ignored
    assert logs[4].user == "(Hey TOM)" and events == ["sleep", "wake"]


def test_media_playing_requires_wake_word_every_time(monkeypatch):
    bot, c, events = make_bot(monkeypatch, ["Hey Tom merhaba", "Bu videoda anlatılan", "Hey Tom videoyu durdur"])
    bot.media_playing = lambda: True
    logs = bot.run(frames(*utter(3)), lambda a: None)
    assert logs[0].user == "Merhaba"
    assert "video/müzik" in logs[1].ignored
    assert logs[2].user == "Videoyu durdur"


def test_stop_command_ignores_own_words():
    from tom.wake import stop_command

    assert stop_command("Sus!") == "stop"
    assert stop_command("Tamam tamam yeter") == "stop"
    assert stop_command("Sessiz ol lütfen") == "stop"
    assert stop_command("Uyku moduna geç") == "sleep"
    # TOM'un kendi cümlesindeki "dur" mikrofona girdi: yok say
    assert stop_command("bir dakika dur bakalım", speaking_text="Bir dakika dur bakalım, hesaplıyorum.") is None
    assert stop_command("Durum gayet iyi görünüyor") is None


def test_interrupt_while_speaking(monkeypatch):
    bot, c, events = make_bot(monkeypatch, ["Hey Tom merhaba", "Sus"])
    stopped = []
    speaking = iter([False] * 35 + [True] * 35 + [False] * 100)
    logs = bot.run(frames((0.9, 20), (0.0, 15), (0.9, 20), (0.0, 15)), lambda a: None,
                   is_speaking=lambda: next(speaking), interrupt=lambda: stopped.append(1))
    assert logs[0].user == "Merhaba" and stopped == [1]
