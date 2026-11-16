"""Kullanıcı cümlesini komut parçalarına ve LLM'e gidecek sohbet parçasına ayırır.

"Işıkları aç ve bana bir fıkra anlat" → ışık komutu anında yürütülür, "bana bir fıkra
anlat" LLM'e gider. Hiçbir parça komut değilse cümlenin tamamı olduğu gibi LLM'e gider.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from tom.skills.base import Skill, SkillResult
from tom.skills.text import normalize

log = logging.getLogger(__name__)

_SPLIT = re.compile(r"\s*(?:[,;]|\.(?!\d)|\bve\b|\bsonra da\b|\bardından\b|\bayrıca\b)\s*")
# Komut algılamayı bozan, anlam taşımayan sözcükler
_FILLER = re.compile(r"\b(tom|lütfen|hey|acaba|bir zahmet|rica etsem)\b")


@dataclass
class Routed:
    results: list[tuple[str, SkillResult]]  # (skill adı, sonuç)
    rest: str  # LLM'e gidecek metin ("" ise LLM'e gerek yok)


class Router:
    def __init__(self, skills: list[Skill]):
        self.skills = skills

    def capabilities(self) -> list[str]:
        return [s.description for s in self.skills if s.description]

    def fixed_phrases(self) -> list[str]:
        out: list[str] = []
        for s in self.skills:
            out += [p for p in s.fixed_phrases() if p not in out]
        return out

    def match(self, clause: str):
        c = _FILLER.sub(" ", normalize(clause)).strip()
        if not c:
            return None
        for s in self.skills:
            hit = s.match(c)
            if hit:
                return s, hit[0], hit[1], c
        return None

    def route(self, text: str) -> Routed:
        clauses = [c for c in _SPLIT.split(text) if c and c.strip()]
        results, rest = [], []
        for clause in clauses:
            hit = self.match(clause)
            if not hit:
                rest.append(clause.strip())
                continue
            skill, action, m, norm = hit
            try:
                res = skill.run(action, m, norm)
            except Exception as e:  # bir komutun hatası sohbeti düşürmesin
                log.exception("skill %s hata", skill.name)
                res = SkillResult(f"Bunu yaparken bir sorun çıktı: {type(e).__name__}.")
            results.append((skill.name, res))
        if not results:
            return Routed([], text.strip())
        return Routed(results, " ".join(rest))
