import numpy as np

from tom.audio.vad import EndpointConfig, Endpointer

CFG = EndpointConfig(min_speech_ms=96, min_silence_ms=320, pre_roll_ms=128, max_utterance_s=3.0)
F = CFG.frame  # 512 örnek = 32 ms


def frames(*spec):
    """spec: (olasılık, kare sayısı) çiftleri. Karenin ilk örneği olasılığı taşır."""
    for p, n in spec:
        for _ in range(n):
            yield np.full(F, p, dtype=np.float32)


def run(spec, cfg=CFG):
    ep = Endpointer(lambda fr: float(fr[0]), cfg)
    events = []
    for i, fr in enumerate(frames(*spec)):
        for ev in ep.feed(fr):
            events.append((i, ev))
    return events


def test_short_blip_is_ignored():
    assert run([(0.0, 10), (0.9, 2), (0.0, 30)]) == []  # 64 ms < 96 ms


def test_utterance_start_and_end_with_preroll():
    ev = run([(0.0, 10), (0.9, 20), (0.0, 20)])
    kinds = [(i, e.kind) for i, e in ev]
    assert kinds[0] == (12, "start")  # 3. konuşma karesinde (96 ms) başlar
    end_i, end = ev[1]
    assert end.kind == "end"
    assert end_i == 29 + 10  # 10 sessiz kare (320 ms) sonra biter
    # ses: ön tampon (4 kare) + 20 konuşma karesi + kısa kuyruk; uzun sessizlik kırpılır
    n = len(end.audio) // F
    assert 20 + 3 <= n <= 20 + 4 + 4
    assert end.audio[: F * 2].max() == 0.0  # ön tampondaki sessizlik dahil


def test_short_pause_inside_speech_does_not_end():
    ev = run([(0.9, 10), (0.1, 5), (0.9, 10), (0.0, 12)])
    assert [e.kind for _, e in ev] == ["start", "end"]


def test_hysteresis_middle_probability_keeps_speaking():
    # 0.4: başlatmaya yetmez (eşik 0.5) ama konuşmayı da bitirmez (alt eşik 0.35)
    ev = run([(0.9, 5), (0.4, 30), (0.0, 12)])
    assert [e.kind for _, e in ev] == ["start", "end"]
    assert ev[1][0] == 4 + 30 + 10


def test_max_length_forces_end():
    ev = run([(0.9, 200)])
    assert [e.kind for _, e in ev][:2] == ["start", "end"]
    assert len(ev[1][1].audio) <= int(3.0 * CFG.sample_rate) + F * 8


def test_reset_drops_partial_utterance():
    ep = Endpointer(lambda fr: float(fr[0]), CFG)
    for fr in frames((0.9, 10)):
        ep.feed(fr)
    assert ep.speaking
    ep.reset()
    assert not ep.speaking
    assert all(not ep.feed(fr) for fr in frames((0.0, 20)))
