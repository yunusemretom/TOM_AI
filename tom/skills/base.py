"""Hızlı komut (skill) altyapısı.

Bir skill, normalize edilmiş cümle parçasına uyan düzenli ifadeler ve her eşleşme için
bir eylem tanımlar. Eşleşen komut LLM'e gitmeden anında yürütülür; cevabı sabit bir
cümleyse (`cacheable=True`) sesi açılışta bir kez üretilip saklanır.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class SkillResult:
    say: str
    cacheable: bool = False  # sabit cümle: ses önceden üretilebilir


@dataclass
class Rule:
    pattern: re.Pattern
    action: str


class Skill:
    name: str = "skill"
    description: str = ""  # sistem istemine "bunları sistem yapıyor" diye girer
    rules: list[Rule] = []

    def match(self, clause: str) -> tuple[str, re.Match] | None:
        for r in self.rules:
            m = r.pattern.search(clause)
            if m:
                return r.action, m
        return None

    def run(self, action: str, m: re.Match, clause: str) -> SkillResult:
        raise NotImplementedError

    def fixed_phrases(self) -> list[str]:
        """Açılışta sesi önceden üretilecek sabit cevaplar."""
        return []


def rule(pattern: str, action: str) -> Rule:
    return Rule(re.compile(pattern), action)
