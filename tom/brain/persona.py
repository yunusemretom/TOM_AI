"""Kişilik ayarı (config/kisilik.yaml) ve ondan üretilen sistem istemi."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
PERSONA_FILE = ROOT / "config" / "kisilik.yaml"
EXAMPLE_FILE = ROOT / "config" / "kisilik.example.yaml"

GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos",
         "Eylül", "Ekim", "Kasım", "Aralık"]


@dataclass
class Persona:
    asistan_adi: str = "TOM"
    hitap: str = ""
    hakkinda: list[str] = field(default_factory=list)
    sehir: str = ""
    kisilik: str = ""
    konusma_kurallari: list[str] = field(default_factory=list)

    @classmethod
    def load(cls, path: Path | None = None) -> "Persona":
        p = path or (PERSONA_FILE if PERSONA_FILE.exists() else EXAMPLE_FILE)
        d = yaml.safe_load(Path(p).read_text(encoding="utf-8")) or {}
        k = d.get("kullanici") or {}
        return cls(
            asistan_adi=d.get("asistan_adi") or "TOM",
            hitap=(k.get("hitap") or "").strip(),
            hakkinda=[str(x) for x in (k.get("hakkinda") or [])],
            sehir=((d.get("konum") or {}).get("sehir") or "").strip(),
            kisilik=(d.get("kisilik") or "").strip(),
            konusma_kurallari=[str(x) for x in (d.get("konusma_kurallari") or [])],
        )

    def system_prompt(self, now: dt.datetime | None = None, capabilities: list[str] | None = None) -> str:
        now = now or dt.datetime.now()
        lines = [
            f"Senin adın {self.asistan_adi}. Kullanıcıyla Türkçe, sesli konuşan kişisel asistanısın; "
            "cevapların yüksek sesle okunacak.",
        ]
        if self.kisilik:
            lines.append(self.kisilik)
        if self.hitap:
            lines.append(f"Kullanıcıya \"{self.hitap}\" diye hitap edebilirsin, ama her cümlede değil.")
        if self.hakkinda:
            lines.append("Kullanıcı hakkında bildiklerin: " + " ".join(
                s if s.rstrip().endswith((".", "!", "?")) else s + "." for s in self.hakkinda))
        lines.append(
            f"Bugün {now.day} {AYLAR[now.month - 1]} {now.year}, {GUNLER[now.weekday()]}."
            + (f" Kullanıcı {self.sehir} şehrinde." if self.sehir else "")
        )
        if capabilities:
            lines.append(
                "Şu işleri senin yerine ayrı bir sistem anında yapıyor ve sonucu kullanıcıya söylüyor: "
                + ", ".join(capabilities) + ". Bunlar dışında internete, haberlere ya da cihazlara "
                "erişimin yok; güncel bilgi uydurma, erişimin olmadığını kısaca söyle."
            )
        lines += self.konusma_kurallari
        return "\n".join(lines)
