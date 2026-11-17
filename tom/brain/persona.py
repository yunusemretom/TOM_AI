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


def selam(hitap: str, now: dt.datetime | None = None, reminders: list[dict] | None = None,
          restarted: bool = False) -> str:
    """Açılış selamı: saate göre, varsa bugünün hatırlatıcılarıyla."""
    from tom.skills.text import sayi_yaz

    now = now or dt.datetime.now()
    if restarted:
        return "Kısa bir aksaklık oldu, yeniden başladım. Kaldığımız yerden devam edebiliriz."
    h = now.hour
    part = "Günaydın" if 5 <= h < 11 else "İyi günler" if h < 17 else "İyi akşamlar" if h < 22 else "İyi geceler"
    s = f"{part}{' ' + hitap if hitap else ''}, hazırım."
    today = [r for r in (reminders or []) if r["zaman"].startswith(now.strftime("%Y-%m-%d"))]
    if today:
        hh, mm = map(int, today[0]["zaman"][11:16].split(":"))
        saat = sayi_yaz(hh) + (f" {sayi_yaz(mm)}" if mm else "")
        s += (f" Bugün {sayi_yaz(len(today))} hatırlatıcın var, ilki saat {saat}: {today[0]['mesaj']}."
              if len(today) > 1 else f" Bugün saat {saat} için bir hatırlatıcın var: {today[0]['mesaj']}.")
    return s


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

    def system_prompt(self, now: dt.datetime | None = None, capabilities: list[str] | None = None,
                      tools: bool = False, facts: list[str] | None = None) -> str:
        now = now or dt.datetime.now()
        lines = [
            f"Senin adın {self.asistan_adi}. Kullanıcıyla Türkçe, sesli konuşan kişisel asistanısın; "
            "cevapların yüksek sesle okunacak.",
        ]
        if self.kisilik:
            lines.append(self.kisilik)
        if self.hitap:
            lines.append(f"Kullanıcıya \"{self.hitap}\" diye hitap edebilirsin, ama her cümlede değil.")
        known = self.hakkinda + list(facts or [])
        if known:
            lines.append("Kullanıcı hakkında bildiklerin: " + " ".join(
                s if s.rstrip().endswith((".", "!", "?")) else s + "." for s in known))
        lines.append(
            f"Bugün {now.day} {AYLAR[now.month - 1]} {now.year}, {GUNLER[now.weekday()]}, saat {now:%H:%M} "
            f"({now:%Y-%m-%d})." + (f" Kullanıcı {self.sehir} şehrinde." if self.sehir else "")
        )
        if tools:
            lines.append(
                "Araçların var: internette arama ve sayfa okuma, haberler, hesap, döviz, hava tahmini, hatırlatıcı, "
                "not, kalıcı hafıza, uygulama ve site açma, sistem durumu. Güncel bilgi, haber, sonuç, fiyat ya da "
                "emin olmadığın bir şey sorulursa tahmin etme, web_ara kullan; 'araştırayım mı' diye izin isteme, "
                "doğrudan ara. Kullanıcı senin önerine 'olur' ya da 'evet' derse o işi hemen aracıyla yap. "
                "Araç sonucunu kendi cümlelerinle, "
                "kısaca ve önemli olanı söyleyerek aktar; gerekirse kaynağın adını an, adres okuma. Bir aracı "
                "çağırmadan bir işi yaptığını asla söyleme. Cevapların sesli okunduğu için kısa olsun: en fazla iki "
                "üç cümle; haberleri en önemli iki üç başlıkla özetle. Cevabın sonuna 'başka bir şey ister misin' "
                "gibi sorular ekleme; espriyi ara sıra yap."
            )
            if capabilities:
                lines.append("Şu komutları ayrı bir sistem anında yapıyor: " + ", ".join(capabilities) + ".")
        elif capabilities:
            lines.append(
                "Şu işleri senin yerine ayrı bir sistem anında yapıyor ve sonucu kullanıcıya söylüyor: "
                + ", ".join(capabilities) + ". Böyle bir istek sana ulaştıysa sistem onu anlayamamış "
                "demektir: asla yaptım, kurdum, açtım deme; kullanıcıdan isteği daha açık söylemesini iste. "
                "Bunlar dışında internete, haberlere ya da cihazlara erişimin yok; güncel bilgi uydurma, "
                "erişimin olmadığını kısaca söyle."
            )
        lines += self.konusma_kurallari
        return "\n".join(lines)

    def chat_prompt(self, now: dt.datetime | None = None, facts: list[str] | None = None) -> str:
        """Yazılı sohbet (Open WebUI) için: sesli moddaki kısalık kuralları yok, Markdown serbest."""
        now = now or dt.datetime.now()
        lines = [f"Senin adın {self.asistan_adi}. Kullanıcının yerel bilgisayarında çalışan kişisel araştırma ve "
                 "yardım asistanısın; kullanıcıyla Türkçe yazışıyorsun (kullanıcı başka dilde yazarsa o dilde cevap ver)."]
        if self.kisilik:
            lines.append(self.kisilik)
        if self.hitap:
            lines.append(f"Kullanıcının adı {self.hitap}.")
        known = self.hakkinda + list(facts or [])
        if known:
            lines.append("Kullanıcı hakkında bildiklerin: " + " ".join(
                s if s.rstrip().endswith((".", "!", "?")) else s + "." for s in known))
        lines.append(f"Bugün {now.day} {AYLAR[now.month - 1]} {now.year}, {GUNLER[now.weekday()]}, saat {now:%H:%M} "
                     f"({now:%Y-%m-%d})." + (f" Kullanıcı {self.sehir} şehrinde." if self.sehir else ""))
        lines.append(
            "Araçların var: internette arama ve sayfa okuma, haberler, hesap, döviz, hava tahmini, hatırlatıcı, not, "
            "kalıcı hafıza, YouTube/site/uygulama açma, sistem durumu. Güncel bilgi, haber, fiyat, sonuç ya da emin "
            "olmadığın bir şey sorulursa tahmin etme, web_ara kullan; izin isteme, doğrudan ara. Araç sonuçlarına "
            "dayanırken kaynağı belirt (site adı ya da bağlantı). Bir aracı çağırmadan bir işi yaptığını asla söyleme.")
        lines.append(
            "Yazılı sohbettesin: cevapların ihtiyaca göre ayrıntılı olabilir; Markdown (başlık, madde, tablo, kod "
            "bloğu) kullan. Gereksiz uzatma, cevabın sonuna 'başka bir şey ister misin' gibi kalıp cümleler ekleme.")
        return "\n".join(lines)
