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


def test_repetition_loop_is_detected():
    from tom.listener.whisper_stt import is_repetitive

    loop = "Bir gün bir gün de " + "bir günlük " * 60
    assert is_repetitive(loop)
    assert not is_repetitive("Bir şey yapmanı istemiyorum. Yanlışlıkla söyledim. Daha demin İngilizce "
                             "konuştum ama İngilizceyi Türkçe'ye çevirdiği için böyle bir konuşma dili geldi.")
    assert not is_repetitive("Evet evet evet.")
