from tom.voice.settings import ROOT, VoiceSettings


def test_settings_load_paths_and_overrides(tmp_path):
    f = tmp_path / "ses.yaml"
    f.write_text("model: models/xtts_ince_test1\nreferans: models/voices/a.wav\nhiz: 0.9\nsicaklik: 0.6\n")
    s = VoiceSettings.load(f)
    assert s.model == str(ROOT / "models/xtts_ince_test1") and s.referans == [str(ROOT / "models/voices/a.wav")]
    assert s.overrides() == {"speed": 0.9, "temperature": 0.6}
    assert len(s.style_key()) == 8 and VoiceSettings().style_key() == ""


def test_engine_applies_overrides_after_config():
    from types import SimpleNamespace

    from tom.voice.xtts_engine import XttsEngine

    e = XttsEngine("/yok", gen_overrides={"speed": 1.1, "temperature": 0.5})
    e.config = SimpleNamespace(temperature=0.75, length_penalty=1.0, repetition_penalty=5.0, top_k=50, top_p=0.85)
    kw = e._gen_kwargs({"temperature": 0.3})
    assert kw["speed"] == 1.1 and kw["temperature"] == 0.3 and kw["top_p"] == 0.85
