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


class FakePhrases:
    def __init__(self, known):
        self.known = known

    def get(self, text):
        return np.ones(7, dtype=np.float32) if text in self.known else None


def test_command_is_answered_without_llm_and_uses_cached_audio(monkeypatch):
    from tom.skills.builtin import DeviceSkill
    from tom.skills.router import Router

    bot, prompts = make(monkeypatch, ["Işıkları aç"], [])
    bot.router = Router([DeviceSkill()])
    bot.phrases = FakePhrases({"Işıklar için henüz bir bağlantım yok."})
    played = []
    logs = bot.run(frames((0.9, 20), (0.0, 15)), played.append)
    assert prompts == []  # LLM'e gidilmedi
    assert logs[0].skills == ["cihaz"] and logs[0].timings is None
    assert len(played) == 1 and len(played[0]) == 7  # hazır ses çalındı
    assert bot.history[-1] == {"role": "assistant", "content": "Işıklar için henüz bir bağlantım yok."}


def test_mixed_sentence_runs_command_then_llm_with_note(monkeypatch):
    from tom.skills.builtin import DeviceSkill
    from tom.skills.router import Router

    bot, prompts = make(monkeypatch, [], ["İşte bir fıkra."])
    bot.router = Router([DeviceSkill()])
    log = bot.respond_text("Işıkları aç ve bana bir fıkra anlat", lambda a: None)
    assert log.skills == ["cihaz"] and log.timings is not None
    last = prompts[0][-1]["content"]
    assert last.startswith("bana bir fıkra anlat") and "zaten yapıldı" in last
    assert "ışık, klima" in prompts[0][0]["content"]  # sistem istemi yetenekleri biliyor


def test_inbox_message_is_spoken_when_idle(monkeypatch):
    bot, _ = make(monkeypatch, [], [])
    bot.notify("Zaman doldu!")
    spoken = []
    monkeypatch.setattr(bot, "speak", lambda text, play: spoken.append(text))
    bot.run(frames((0.0, 5)), lambda a: None)
    assert spoken == ["Zaman doldu!"]


def test_agent_answer_keeps_only_last_tool_trace(monkeypatch):
    from tom.brain.agent import Agent
    from tom.tools.base import Tool, Toolbox

    calls = []

    def chat(msgs, model, tools=None, options=None, think=False):
        calls.append(msgs)
        n = len(calls)
        if n in (1, 3):  # her soruda önce araç ister
            yield "tools", [{"function": {"name": "web_ara", "arguments": {"sorgu": f"s{n}"}}}]
        else:
            yield "text", f"Cevap {n}."

    bot, _ = make(monkeypatch, ["Birinci?", "İkinci?"], [])
    bot.agent = Agent(chat, "m", Toolbox([Tool("web_ara", "x", {"sorgu": {"type": "string"}}, ["sorgu"],
                                               lambda sorgu: "sonuç " + sorgu)]))
    played = []
    logs = bot.run(frames((0.9, 20), (0.0, 15), (0.9, 20), (0.0, 15)), played.append)
    assert [l.user for l in logs] == ["Birinci?", "İkinci?"]
    assert logs[0].tools == ["web_ara"] and "araç: web_ara" in logs[0].line()
    tools_in_history = [m for m in bot.history if m.get("role") == "tool"]
    assert [m["content"] for m in tools_in_history] == ["sonuç s3"]  # yalnız son turun izi
    assert bot.history[-1] == {"role": "assistant", "content": "Bir bakayım. Cevap 4."} or \
        bot.history[-1]["content"].endswith("Cevap 4.")
    # ikinci sorunun ilk çağrısı, birinci turun araç izini görüyor (devam sorusu için)
    assert any(m.get("role") == "tool" and m["content"] == "sonuç s1" for m in calls[2])


def test_system_prompt_mentions_tools_time_and_facts():
    import datetime as dt
    from tom.brain.persona import Persona

    p = Persona(hitap="Yunus", hakkinda=["Öğrenci."])
    sp = p.system_prompt(now=dt.datetime(2026, 11, 17, 9, 5), tools=True, facts=["Kahveyi sütsüz içer."])
    assert "saat 09:05" in sp and "2026-11-17" in sp and "web_ara" in sp
    assert "Kahveyi sütsüz içer." in sp and "erişimin yok" not in sp
