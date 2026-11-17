"""Komut eşleştirme için Türkçe metin yardımcıları."""

from __future__ import annotations

import re

_ONES = ["sıfır", "bir", "iki", "üç", "dört", "beş", "altı", "yedi", "sekiz", "dokuz"]
_TENS = ["", "on", "yirmi", "otuz", "kırk", "elli", "altmış", "yetmiş", "seksen", "doksan"]
_WORD_VAL = {w: i for i, w in enumerate(_ONES)} | {w: i * 10 for i, w in enumerate(_TENS) if w}
_WORD_VAL.update({"yarım": 0.5, "buçuk": 0.5})


def tr_lower(s: str) -> str:
    return s.replace("I", "ı").replace("İ", "i").lower()


def normalize(s: str) -> str:
    """Küçük harf (Türkçe), noktalama → boşluk (rakam arasındaki : ve . korunur)."""
    s = tr_lower(s)
    s = re.sub(r"(?<=\d)[:.,](?=\d)", "\x00", s)
    s = re.sub(r"[^\w\s\x00%]", " ", s).replace("\x00", ".")
    return re.sub(r"\s+", " ", s).strip()


def sayi_yaz(n: int) -> str:
    """0–9999 arası sayıyı boşluklu Türkçe yazıya çevirir (XTTS rakamları kötü okuyabiliyor)."""
    if n < 0:
        return "eksi " + sayi_yaz(-n)
    if n < 10:
        return _ONES[n]
    parts = []
    if n >= 1000:
        k, n = divmod(n, 1000)
        parts.append("bin" if k == 1 else f"{sayi_yaz(k)} bin")
    if n >= 100:
        h, n = divmod(n, 100)
        parts.append("yüz" if h == 1 else f"{_ONES[h]} yüz")
    if n >= 10:
        t, n = divmod(n, 10)
        parts.append(_TENS[t])
    if n:
        parts.append(_ONES[n])
    return " ".join(parts)


_UNIT_S = {"saniye": 1, "sn": 1, "dakika": 60, "dk": 60, "saat": 3600}
_NUM = r"(?:\d+(?:[.,]\d+)?|(?:(?:" + "|".join(_TENS[1:]) + r")\s*)?(?:" + "|".join(_ONES[1:]) + r")|" \
       + "|".join(_TENS[1:]) + r"|yarım)"
DURATION_RE = re.compile(
    rf"(?<!\w)(?P<num>{_NUM})(?P<half>\s+buçuk)?\s*(?P<unit>saniye|sn|dakika|dk|saat)\w*"
)


# Yüzde: "%40", "yüzde 40", "yüzde yetmiş beş", "yüzde yüz"
PCT_RE = re.compile(r"(?:%\s*|\byüzde\s+)(?P<pct>\d+|yüz|(?:(?:" + "|".join(_TENS[1:]) + r")\s*)?(?:"
                    + "|".join(_ONES[1:]) + r")|" + "|".join(_TENS[1:]) + r")\b")


def parse_percent(text: str) -> int | None:
    m = PCT_RE.search(text)
    if not m:
        return None
    v = 100 if m.group("pct") == "yüz" else word_number(m.group("pct"))
    return int(v) if v is not None else None


def word_number(s: str) -> float | None:
    s = s.strip().replace(",", ".")
    try:
        return float(s)
    except ValueError:
        pass
    total = 0.0
    for w in s.split():
        if w not in _WORD_VAL:
            return None
        total += _WORD_VAL[w]
    return total


def parse_duration(text: str) -> int | None:
    """'5 dakika', 'iki buçuk saat', 'yarım saat', '1 dakika 30 saniye' → saniye."""
    total, found = 0.0, False
    for m in DURATION_RE.finditer(text):
        v = word_number(m.group("num").replace(" ", " "))
        if v is None:
            continue
        if m.group("half"):
            v += 0.5
        total += v * _UNIT_S[m.group("unit")]
        found = True
    return int(round(total)) if found and total > 0 else None


def sure_yaz(seconds: int) -> str:
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    parts = [f"{sayi_yaz(h)} saat" if h else "", f"{sayi_yaz(m)} dakika" if m else "",
             f"{sayi_yaz(s)} saniye" if s else ""]
    return " ".join(p for p in parts if p) or "sıfır saniye"
