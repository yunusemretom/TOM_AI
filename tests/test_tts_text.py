import pytest

from tom.voice.text_prep import tts_text


@pytest.mark.parametrize("text,expected", [
    ("Saat on dokuz, kırk dokuz.", "Saat on dokuz, kırk dokuz"),
    ("Tamam.  ", "Tamam"),
    ("Bekle...", "Bekle"),
    ("Bekle…", "Bekle"),
    ("Nasılsın?", "Nasılsın?"),          # soru/ünlem tonlamayı belirler, kalır
    ("Harika!", "Harika!"),
    ("Birinci. İkinci.", "Birinci. İkinci"),  # yalnız sondaki nokta
    ("\"Ben de seninle yaparım.\"", "\"Ben de seninle yaparım\""),
    ("3.", "3."),                       # tek başına sayı: anlamı değişmesin
])
def test_trailing_period_removed(text, expected):
    assert tts_text(text) == expected
