from tom.listener.whisper_stt import is_hallucination, tr_lower


def test_turkish_lowercase():
    assert tr_lower("IŞIK İzmir") == "ışık izmir"


def test_known_hallucinations_are_dropped():
    assert is_hallucination("Altyazı M.K.")
    assert is_hallucination("  ")
    assert is_hallucination("...")
    assert is_hallucination("İzlediğiniz için teşekkürler!")


def test_real_sentences_are_kept():
    assert not is_hallucination("Işıkları açar mısın?")
    assert not is_hallucination("Yarın sabah sekizde beni uyandır, altyazılı film izleyeceğiz.")
