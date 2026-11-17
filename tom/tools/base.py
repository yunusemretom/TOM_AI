"""Araç tanımı ve kutusu: Ollama'nın beklediği JSON şeması + güvenli çalıştırma."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

MAX_RESULT = 3000  # karakter: bağlam (num_ctx) taşmasın


@dataclass
class Tool:
    name: str
    description: str
    params: dict[str, dict] = field(default_factory=dict)  # ad → {"type": ..., "description": ...}
    required: list[str] = field(default_factory=list)
    fn: Callable[..., str] = lambda **kw: ""

    def schema(self) -> dict:
        return {"type": "function", "function": {
            "name": self.name, "description": self.description,
            "parameters": {"type": "object", "properties": self.params, "required": self.required}}}


class Toolbox:
    def __init__(self, tools: list[Tool]):
        self.tools = {t.name: t for t in tools}

    def schemas(self) -> list[dict]:
        return [t.schema() for t in self.tools.values()]

    def run(self, name: str, args: dict) -> str:
        t = self.tools.get(name)
        if t is None:
            return f"Hata: '{name}' diye bir araç yok."
        known = {k: v for k, v in (args or {}).items() if k in t.params}
        missing = [r for r in t.required if r not in known]
        if missing:
            return f"Hata: eksik parametre: {', '.join(missing)}."
        try:
            out = str(t.fn(**known))
        except Exception as e:  # araç hatası modele iletilir; model kullanıcıya söyler
            return f"Hata: {type(e).__name__}: {e}"
        return out if len(out) <= MAX_RESULT else out[:MAX_RESULT] + " …(kısaltıldı)"
