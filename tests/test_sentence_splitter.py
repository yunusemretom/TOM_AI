from tom.brain.sentence_splitter import SentenceSplitter


def feed_all(pieces, **kw):
    s = SentenceSplitter(**kw)
    out = []
    for p in pieces:
        out.extend(s.feed(p))
    out.extend(s.flush())
    return out


def test_splits_on_sentence_end_across_token_boundaries():
    pieces = ["Merha", "ba! Bugün ", "hava güzel", ". Yarın da", " öyle olacak."]
    assert feed_all(pieces, first_min_chars=999) == [
        "Merhaba!",
        "Bugün hava güzel.",
        "Yarın da öyle olacak.",
    ]


def test_sentence_is_emitted_as_soon_as_next_word_starts():
    s = SentenceSplitter(first_min_chars=999)
    assert s.feed("Tamam.") == []  # sonrası belli değil, bekle
    assert s.feed(" Işıkları") == ["Tamam."]


def test_does_not_split_decimals_or_ordinals():
    text = "Sıcaklık 3.5 derece. 15. yüzyılda kuruldu."
    assert feed_all([text], first_min_chars=999) == [
        "Sıcaklık 3.5 derece.",
        "15. yüzyılda kuruldu.",
    ]


def test_first_chunk_can_break_on_comma_for_fast_start():
    text = "Tabii, hemen bakıyorum, birkaç saniye sürebilir. Sonra söylerim."
    out = feed_all([text], first_min_chars=10)
    assert out[0] == "Tabii, hemen bakıyorum,"
    assert out[1:] == ["birkaç saniye sürebilir.", "Sonra söylerim."]


def test_long_sentence_is_broken_at_comma_under_max_chars():
    long = "Bu, " + "çok uzun bir cümle parçası, " * 12 + "bitti."
    out = feed_all([long], first_min_chars=999, max_chars=120)
    assert all(len(x) <= 120 for x in out)
    assert " ".join(out).replace("  ", " ") == long.strip()


def test_strips_markdown_and_emoji():
    out = feed_all(["**Merhaba** 😊\n", "# Başlık\n- madde bir.\n"], first_min_chars=999)
    assert out == ["Merhaba", "Başlık", "madde bir."]


def test_flush_returns_unterminated_tail():
    assert feed_all(["Sonu noktasız"]) == ["Sonu noktasız"]
    assert feed_all(["   "]) == []


def test_generic_closers_are_dropped():
    pieces = ["Sen bu işi halledersin. ", "Nasıl yardımcı olabilirim? ", "Başka bir sorun var mı?"]
    assert feed_all(pieces, first_min_chars=999) == ["Sen bu işi halledersin."]


def test_closer_filter_keeps_real_sentences():
    from tom.brain.sentence_splitter import is_filler_closer

    assert is_filler_closer("Peki, sana nasıl yardımcı olabilirim?")
    assert is_filler_closer("Senin için yapabileceğim başka bir şey var mı?")
    assert not is_filler_closer("Sana sınavda nasıl yardımcı olabilirim, konuları mı tekrar edelim?")
    assert not is_filler_closer("Bu konuda nasıl yardımcı olabileceğimi düşündüm.")
    assert feed_all(["Nasıl yardımcı olabilirim?"], drop_closers=False) == ["Nasıl yardımcı olabilirim?"]
