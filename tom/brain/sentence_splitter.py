"""LLM'den akan metni seslendirilebilir cümlelere böler.

LLM token token yazar; TTS'e ise anlamlı, kapanmış parçalar vermek gerekir. Bölücü:
- `. ! ? …` sonrası bir sonraki kelime başlayınca cümleyi verir (ondalık "3.5" ve
  sıra sayısı "15. yüzyıl" bölünmez: noktadan sonra küçük harf/rakam gelirse bölmez).
- İlk parçayı hızlı çıkarmak için yeterince uzunsa virgülde de böler (`first_min_chars`).
- `max_chars`'ı aşan cümleyi virgülden, yoksa boşluktan böler (XTTS uzun girdide bozulur).
- Markdown işaretlerini ve emojileri atar; satır sonu cümle sonu sayılır.
"""

from __future__ import annotations

import re

_ENDERS = ".!?…"
_MD = re.compile(r"(\*\*|__|\*|`+|^#+\s*|^\s*[-*•]\s+|^\s*\d+\)\s+)", re.MULTILINE)
_EMOJI = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F2FF\U0000FE0F\U0000200D]"
)
_WS = re.compile(r"[ \t]+")

# Küçük modellerin istemi dinlemeyip her cevaba eklediği kalıp kapanışlar ("Nasıl yardımcı olabilirim?")
_CLOSER = re.compile(
    r"^(peki |o zaman |şimdi )?(sana |size )?(başka |bugün |başka bir konuda )?"
    r"(nasıl|ne konuda|hangi konuda) (sana |size )?(yardımcı|destek) ol(abilirim|ayım|abilir miyim)$"
    r"|^(senin için |sana )?yapabileceğim (başka )?bir şey var mı$"
    r"|^(sana )?yardımcı olabileceğim başka bir (şey|konu) var mı$"
    r"|^başka (bir )?(sorun|sorunuz|sorusu|isteğin|bir şey|soru) var mı$"
    r"|^(peki |yunus )?başka (bir )?\w+( \w+){0,4} (ister misin|istersin|ihtiyacın var mı|yapmamı ister misin|"
    r"yardımcı olabilir miyim|var mı)$"
    r"|^bu konulardan (herhangi )?(biri|birisi) hakkında .*(ister misin|var mı)$"
)


_SPEAKER = re.compile(r"^\s*(?:TOM|Tom|Asistan)\s*:\s*")  # model bazen konuşmacı etiketi yazıyor


def _clean(text: str) -> str:
    text = _SPEAKER.sub("", text)
    text = _EMOJI.sub("", text)
    text = _MD.sub("", text)
    return _WS.sub(" ", text).strip()


# "Yağmur bekleniyor, başka bir şey ister misin?" → yalnız kuyruk atılır, bilgi kalır
_CLOSER_TAIL = re.compile(
    r"[,;]\s*(peki |yunus |ya da )?başka (bir )?\w+( \w+){0,4} (ister misin|istersin|ihtiyacın var mı|"
    r"yapmamı ister misin|yardımcı olabilir miyim|var mı)\s*\?\s*$", re.I)


def strip_closer_tail(sentence: str) -> str:
    return _CLOSER_TAIL.sub(".", sentence)


def is_filler_closer(sentence: str) -> bool:
    s = sentence.replace("I", "ı").replace("İ", "i").lower()
    s = re.sub(r"[^\w\s]", " ", s)
    return bool(_CLOSER.match(" ".join(s.split())))


class Spoken(str):
    """Hemen söylenecek tam cümle (ör. araç çalışırken "Bir bakayım."): en az uzunluk beklenmez."""


class SentenceSplitter:
    def __init__(self, first_min_chars: int = 20, max_chars: int = 200, drop_closers: bool = True):
        self.first_min_chars = first_min_chars
        self.max_chars = max_chars
        self.drop_closers = drop_closers
        self.buf = ""
        self.emitted = 0

    def feed(self, piece: str) -> list[str]:
        if isinstance(piece, Spoken):  # bekletmeden, tek başına cümle olarak ver
            out = self.flush() if self.buf.strip() else []
            self.buf = ""
            out.extend(self._emit(str(piece)))
            return out
        self.buf += piece
        out: list[str] = []
        while True:
            cut = self._find_cut()
            if cut is None:
                break
            chunk, self.buf = self.buf[:cut], self.buf[cut:]
            out.extend(self._emit(chunk))
        return out

    def flush(self) -> list[str]:
        chunk, self.buf = self.buf, ""
        return self._emit(chunk)

    # ------------------------------------------------------------------
    def _emit(self, chunk: str) -> list[str]:
        out = []
        for line in chunk.split("\n"):
            for part in self._limit(_clean(line)):
                if part and any(ch.isalnum() for ch in part):
                    if self.drop_closers:
                        if is_filler_closer(part):
                            continue
                        part = strip_closer_tail(part)
                    out.append(part)
        self.emitted += len(out)
        return out

    def _limit(self, text: str) -> list[str]:
        parts = []
        while len(text) > self.max_chars:
            window = text[: self.max_chars]
            i = window.rfind(", ")
            i = i + 1 if i > 0 else window.rfind(" ")
            if i <= 0:
                i = self.max_chars
            parts.append(text[:i].strip())
            text = text[i:].strip()
        parts.append(text)
        return parts

    def _find_cut(self) -> int | None:
        b = self.buf
        for i, ch in enumerate(b):
            if ch == "\n":
                return i + 1
            if ch in _ENDERS:
                j = i + 1
                while j < len(b) and b[j] in _ENDERS + "\"')»":
                    j += 1
                if j >= len(b):
                    return None  # ardından ne geleceği belli değil
                if not b[j].isspace():
                    continue  # "3.5", "a.b" gibi
                k = j
                while k < len(b) and b[k] in " \t":
                    k += 1
                if k >= len(b):
                    return None
                nxt = b[k]
                if nxt.islower() or (nxt.isdigit() and b[i - 1 : i].isdigit()):
                    continue  # "15. yüzyıl", "3. 5" gibi
                if b[i - 1 : i].isdigit() and nxt.islower():
                    continue
                return j
            if (
                ch == ","
                and self.emitted == 0
                and i + 1 >= self.first_min_chars
                and i + 1 < len(b)
                and b[i + 1].isspace()
            ):
                return i + 1
        if len(b) > self.max_chars * 2:
            return self.max_chars  # hiç noktalama yoksa sınırsız birikmesin
        return None
