"""TTS'e gitmeden önce metne yapılan küçük düzeltmeler.

XTTS cümle sonundaki noktayı görünce hemen durmuyor; 1 sn'ye varan fazladan ses (nefes,
anlamsız hece) üretiyor. Ölçüm (test1 modeli, 10 cümle): son kelimeden sonra kalan ses
noktalıyken ort. 0,55 s / en çok 1,33 s, nokta kaldırılınca 0,23 s / 0,33 s.
Soru ve ünlem işareti tonlamayı belirlediği için korunur.
"""

from __future__ import annotations

import re

# Sondaki nokta(lar)/üç nokta, ardından gelebilecek kapanış tırnağı/parantezi korunarak;
# öncesinde rakam varsa ("3.") dokunulmaz.
_TRAILING_PERIOD = re.compile(r"(?<=[^\d\s.…])[.…]+(?=[\"'”’)»]*\s*$)")

# Metin hazırlama değişince önceden üretilmiş sesler (hazır cümle önbelleği) geçersiz olur
TEXT_PREP_VERSION = 2


def tts_text(text: str) -> str:
    return _TRAILING_PERIOD.sub("", text.strip()).strip()
