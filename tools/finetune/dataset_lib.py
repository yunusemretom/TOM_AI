"""Podcast → XTTS veri seti: modelden bağımsız, test edilebilir yardımcılar.

Whisper kelime zaman damgaları cümlelere, cümleler 3–11 sn'lik kliplere toplanır.
Klip sınırları cümle sonlarına denk gelir (cümle ortasından kesilmez); uzun sessizlik
(konuşmacı değişimi olabilir) klibi böler.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass, field

import numpy as np

from tom.skills.text import sayi_yaz, tr_lower

_SENT_END = re.compile(r"[.!?…]['\"”’)»]*$")
_SOFT_END = re.compile(r"[,;:]['\"”’)»]*$")


# Whisper ekleri ayrı kelime verir ("İstanbul" + "'un", "Arif" + "-i"); tek başına noktalama da olabilir
_SUFFIX = re.compile(r"^(['’]|-\w|[.,!?;:…]+$)")


def join_words(texts) -> str:
    """Kelimeleri boşlukla birleştirir; kesme işaretli ek ve tireli izafet önceki kelimeye yapışır."""
    out = ""
    for t in texts:
        t = t.strip()
        if not t:
            continue
        out += t if (out and _SUFFIX.match(t)) else (" " + t if out else t)
    return out


@dataclass
class Word:
    text: str
    start: float
    end: float
    prob: float = 1.0


@dataclass
class Clip:
    words: list[Word] = field(default_factory=list)

    @property
    def start(self) -> float:
        return self.words[0].start

    @property
    def end(self) -> float:
        return self.words[-1].end

    @property
    def duration(self) -> float:
        return self.end - self.start

    @property
    def text(self) -> str:
        return join_words(w.text for w in self.words)

    @property
    def min_prob(self) -> float:
        return min(w.prob for w in self.words)


def _sentences(words: list[Word], max_gap_s: float) -> list[tuple[list[Word], bool]]:
    """(kelimeler, öncesinde_uzun_ara) listesi."""
    out, cur, brk = [], [], False
    for i, w in enumerate(words):
        if cur and w.start - cur[-1].end > max_gap_s:
            out.append((cur, brk))
            cur, brk = [], True
        elif not cur and out and w.start - out[-1][0][-1].end > max_gap_s:
            brk = True
        cur.append(w)
        if _SENT_END.search(w.text.strip()):
            out.append((cur, brk))
            cur, brk = [], False
    if cur:
        out.append((cur, brk))
    return out


def _split_long(sent: list[Word], max_s: float) -> list[list[Word]] | None:
    """max_s'yi aşan cümleyi virgül/noktalı virgülden böler; olmuyorsa None (atılır)."""
    if sent[-1].end - sent[0].start <= max_s:
        return [sent]
    pieces, cur = [], []
    for w in sent:
        cur.append(w)
        if _SOFT_END.search(w.text.strip()):
            pieces.append(cur)
            cur = []
    if cur:
        pieces.append(cur)
    if any(p[-1].end - p[0].start > max_s for p in pieces):
        return None
    # komşu parçaları sınırı aşmadan birleştir
    merged = [pieces[0]]
    for p in pieces[1:]:
        if p[-1].end - merged[-1][0].start <= max_s:
            merged[-1] = merged[-1] + p
        else:
            merged.append(p)
    return merged


def sentence_units(words: list[Word], max_s: float = 11.0, max_gap_s: float = 1.2):
    """Kelimeleri klip yapı taşlarına (cümle ya da cümle parçası) ayırır.

    Dönen liste: (kelimeler, öncesinde_kopma). Kelimeleri boş birim, atılan bir cümlenin
    yerini tutar (iki yanı birleştirilmez).
    """
    units: list[tuple[list[Word], bool]] = []
    for sent, brk in _sentences(words, max_gap_s):
        parts = _split_long(sent, max_s)
        if parts is None:
            units.append(([], True))
            continue
        for k, p in enumerate(parts):
            units.append((p, brk if k == 0 else False))
    return units


def group_into_clips(words: list[Word], min_s: float = 3.0, max_s: float = 11.0,
                     max_gap_s: float = 1.2) -> list[Clip]:
    return merge_units(sentence_units(words, max_s, max_gap_s), min_s, max_s)


def merge_units(units, min_s: float = 3.0, max_s: float = 11.0) -> list[Clip]:
    """Ardışık birimleri max_s'yi aşmadan kliplere toplar; boş birim ya da kopma klibi böler.

    Konuşmacı süzgeci, başka birine ait cümleyi boş birimle değiştirerek klibin
    o noktada bölünmesini sağlar.
    """
    clips, cur = [], []

    def flush():
        if cur and cur[-1].end - cur[0].start >= min_s:
            clips.append(Clip(list(cur)))
        cur.clear()

    for unit, brk in units:
        if not unit:
            flush()
            continue
        if cur and (brk or unit[-1].end - cur[0].start > max_s):
            flush()
        cur.extend(unit)
    flush()
    return clips


def clip_bounds(start: float, end: float, prev_end: float | None, next_start: float | None,
                total: float, pad_start: float = 0.15, pad_end: float = 0.25) -> tuple[float, float]:
    """Kelime sınırlarına pay ekler; komşu kelimelerle aradaki boşluğun ortasını geçmez."""
    s = start - pad_start
    if prev_end is not None:
        s = max(s, (prev_end + start) / 2)
    e = end + pad_end
    if next_start is not None:
        e = min(e, (end + next_start) / 2)
    return max(0.0, s), min(total, e)


_ALLOWED = re.compile(r"^[\wçğıöşüâîûÇĞİÖŞÜÂÎÛ\s.,!?;:'\"’“”()\-…%]+$")


def normalize_text_tr(text: str) -> str | None:
    """Sayıları yazıya çevirir. Doğru okunuşu belirsiz ifadelerde None (klip atılır)."""
    t = re.sub(r"\s+", " ", text or "").strip()
    if not t or not _ALLOWED.match(t):
        return None
    # sıra sayısı, saat, binlik ayırıcı, ekli sayı: okunuşu belirsiz
    if re.search(r"\d\.(\s|\d|$)|\d:\d|\d['’]", t):
        return None
    t = re.sub(r"%\s*(\d+)", lambda m: f"yüzde {m.group(1)}", t)
    t = re.sub(r"(\d+),(\d+)", lambda m: f"{m.group(1)} virgül {m.group(2)}", t)

    def num(m):
        n = int(m.group(0))
        if n > 9999:
            raise ValueError
        return sayi_yaz(n)

    try:
        t = re.sub(r"\d+", num, t)
    except ValueError:
        return None
    if "%" in t or re.search(r"\d", t):
        return None
    return re.sub(r"\s+", " ", t).strip()


def rms_dbfs(audio: np.ndarray) -> float:
    rms = float(np.sqrt(np.mean(np.square(audio, dtype=np.float64))))
    return 20 * np.log10(max(rms, 1e-9))


def clipping_ratio(audio: np.ndarray, level: float = 0.99) -> float:
    return float(np.mean(np.abs(audio) >= level))


def _norm_words(s: str) -> list[str]:
    return re.sub(r"[^\w\s]", " ", tr_lower(s)).split()


def word_error_rate(ref: str, hyp: str) -> float:
    r, h = _norm_words(ref), _norm_words(hyp)
    if not r:
        return 0.0 if not h else 1.0
    d = list(range(len(h) + 1))
    for i, rw in enumerate(r, 1):
        prev, d[0] = d[0], i
        for j, hw in enumerate(h, 1):
            prev, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, prev + (rw != hw))
    return d[-1] / len(r)


def split_train_eval(items: list, eval_ratio: float = 0.1, seed: int = 0, max_eval: int = 100):
    idx = list(range(len(items)))
    random.Random(seed).shuffle(idx)
    n_eval = min(max_eval, max(1, round(len(items) * eval_ratio))) if len(items) > 1 else 0
    ev = set(idx[:n_eval])
    return [x for i, x in enumerate(items) if i not in ev], [x for i, x in enumerate(items) if i in ev]
