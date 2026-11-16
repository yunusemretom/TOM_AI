import numpy as np
import pytest

from tools.finetune.dataset_lib import (Word, clip_bounds, clipping_ratio, group_into_clips,
                                        normalize_text_tr, rms_dbfs, split_train_eval, word_error_rate)


def words(spec):
    """spec: [(metin, başlangıç, bitiş), ...]"""
    return [Word(t, s, e, 0.9) for t, s, e in spec]


def test_groups_sentences_into_clips_within_limits():
    w = words([
        ("Merhaba", 0.0, 0.5), ("arkadaşlar.", 0.6, 1.4),            # 1,4 s
        ("Bugün", 1.8, 2.2), ("çok", 2.3, 2.5), ("güzel", 2.6, 3.0), ("bir", 3.1, 3.3),
        ("konumuz", 3.4, 4.0), ("var.", 4.1, 4.5),                       # 2,7 s
        ("Hadi", 4.9, 5.2), ("başlayalım.", 5.3, 6.2),                   # 1,3 s
    ])
    clips = group_into_clips(w, min_s=3.0, max_s=11.0)
    assert [c.text for c in clips] == [
        "Merhaba arkadaşlar. Bugün çok güzel bir konumuz var. Hadi başlayalım."
    ]
    assert clips[0].start == 0.0 and clips[0].end == pytest.approx(6.2)


def test_clip_is_closed_before_exceeding_max():
    w = words([("Birinci", 0, 1), ("cümle.", 1.1, 4.0),
               ("İkinci", 4.2, 5), ("cümle.", 5.1, 8.0),
               ("Üçüncü", 8.2, 9), ("cümle.", 9.1, 12.0)])
    clips = group_into_clips(w, min_s=3.0, max_s=8.5)
    assert [c.text for c in clips] == ["Birinci cümle. İkinci cümle.", "Üçüncü cümle."]
    assert all(c.end - c.start <= 8.5 for c in clips)


def test_long_pause_breaks_clip():
    # 2 sn'lik sessizlik: konuşmacı değişmiş ya da konu kopmuş olabilir, birleştirme
    w = words([("Evet", 0, 1.5), ("aynen.", 1.6, 3.5), ("Peki", 5.5, 6.5), ("sonra?", 6.6, 9.0)])
    clips = group_into_clips(w, min_s=3.0, max_s=11.0, max_gap_s=1.2)
    assert [c.text for c in clips] == ["Evet aynen.", "Peki sonra?"]


def test_too_long_sentence_is_split_at_comma_or_dropped():
    w = words([("Bu", 0, 1), ("çok", 1, 2), ("uzun,", 2, 5), ("gerçekten", 5, 8), ("uzun", 8, 11),
               ("bir", 11, 13), ("cümle.", 13, 15)])
    clips = group_into_clips(w, min_s=3.0, max_s=11.0)
    assert [c.text for c in clips] == ["Bu çok uzun,", "gerçekten uzun bir cümle."]
    w2 = words([("Hiç", 0, 6), ("virgülsüz", 6, 14), ("cümle.", 14, 15)])
    assert group_into_clips(w2, min_s=3.0, max_s=11.0) == []


def test_short_isolated_sentence_is_dropped():
    w = words([("Hmm.", 0, 0.6), ("Tamam.", 3.0, 3.5)])
    assert group_into_clips(w, min_s=3.0, max_s=11.0, max_gap_s=1.2) == []


def test_clip_bounds_pad_without_eating_neighbours():
    s, e = clip_bounds(10.0, 14.0, prev_end=9.95, next_start=14.5, total=100.0)
    assert s == pytest.approx(9.975)  # komşuya kadar, ortası
    assert 14.0 < e <= 14.25
    s, e = clip_bounds(0.05, 3.0, prev_end=None, next_start=None, total=3.1)
    assert s == 0.0 and e == pytest.approx(3.1)


@pytest.mark.parametrize("text,expected", [
    ("Saat 14 oldu.", "Saat on dört oldu."),
    ("%50 indirim var", "yüzde elli indirim var"),
    ("Pi sayısı 3,14 civarı.", "Pi sayısı üç virgül on dört civarı."),
    ("2026 yılında", "iki bin yirmi altı yılında"),
    ("  Merhaba   dünya  ", "Merhaba dünya"),
])
def test_normalize_text(text, expected):
    assert normalize_text_tr(text) == expected


@pytest.mark.parametrize("text", ["15. yüzyılda", "Saat 14:30'da", "1.000.000 kişi", "♪ müzik ♪", ""])
def test_unspeakable_text_is_rejected(text):
    assert normalize_text_tr(text) is None


def test_audio_quality_measures():
    t = np.linspace(0, 1, 22050, dtype=np.float32)
    sine = 0.5 * np.sin(2 * np.pi * 220 * t)
    assert rms_dbfs(sine) == pytest.approx(-9.03, abs=0.1)
    assert clipping_ratio(sine) == 0.0
    assert clipping_ratio(np.clip(sine * 4, -1, 1)) > 0.3


def test_wer():
    assert word_error_rate("Merhaba, nasılsın?", "merhaba nasılsın") == 0.0
    assert word_error_rate("bir iki üç dört", "bir iki beş dört") == 0.25


def test_split_train_eval_is_deterministic_and_bounded():
    items = [f"c{i}" for i in range(100)]
    tr, ev = split_train_eval(items, eval_ratio=0.1, seed=1)
    assert len(ev) == 10 and len(tr) == 90 and not set(tr) & set(ev)
    assert split_train_eval(items, 0.1, seed=1) == (tr, ev)
    tr, ev = split_train_eval(items[:5], eval_ratio=0.1, seed=1)
    assert len(ev) == 1


def test_other_speaker_sentence_breaks_clip():
    from tools.finetune.dataset_lib import merge_units, sentence_units

    w = words([("Sunucu", 0, 1), ("konuşuyor.", 1.1, 3.2), ("Konuk", 3.6, 4.5), ("araya", 4.6, 5.2),
               ("giriyor.", 5.3, 6.5), ("Sunucu", 6.9, 8), ("devam", 8.1, 9), ("ediyor.", 9.1, 10.5)])
    units = sentence_units(w)
    assert len(units) == 3
    units[1] = ([], True)  # konuşmacı süzgeci: başkasına ait
    clips = merge_units(units, min_s=3.0, max_s=11.0)
    assert [c.text for c in clips] == ["Sunucu konuşuyor.", "Sunucu devam ediyor."]
