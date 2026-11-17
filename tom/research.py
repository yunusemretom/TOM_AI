"""Derin araştırma: plan → çoklu arama → sayfaları oku → sayfa başına not → kaynaklı rapor.

Sesli cevaptan farkı: kısa değil, kapsamlı ve yazılı. 1-2 dakika sürer; her adım `progress` ile
bildirilir, rapor parça parça `on_text` ile akar, sonunda `data/arastirmalar/` altına Markdown kaydedilir.
Rapor "Özet:" satırıyla başlar; o satır sesli söylenir.
"""

from __future__ import annotations

import datetime as dt
import json
import re
from concurrent.futures import ThreadPoolExecutor, wait
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterator

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "arastirmalar"
SKIP_SITES = ("youtube.com", "youtu.be", "instagram.com", "facebook.com", "tiktok.com", "x.com", "twitter.com")


@dataclass
class Source:
    n: int
    title: str
    url: str
    text: str = ""
    note: str = ""


@dataclass
class Report:
    question: str
    queries: list[str] = field(default_factory=list)
    sources: list[Source] = field(default_factory=list)
    text: str = ""
    path: Path | None = None

    @property
    def summary(self) -> str:
        m = re.search(r"^\s*\**Özet\**\s*:\s*\**(.+)", self.text, re.M | re.I)
        if m:
            return m.group(1).strip().strip("*")
        first = next((p for p in self.text.split("\n\n") if p.strip() and not p.lstrip().startswith("#")), "")
        return " ".join(first.split())[:400]


class DeepResearch:
    def __init__(self, chat: Callable[[list[dict]], Iterator[str]], search: Callable[[str, int], list[dict]],
                 read_page: Callable[[str], str], max_pages: int = 8, n_queries: int = 4,
                 now: Callable[[], dt.datetime] = dt.datetime.now):
        """chat(mesajlar) → metin parçaları; search(sorgu, n) → [{title, href, body}]; read_page(url) → metin."""
        self.chat, self.search, self.read_page = chat, search, read_page
        self.max_pages, self.n_queries, self.now = max_pages, n_queries, now

    def _ask(self, prompt: str, system: str = "") -> str:
        msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
        return "".join(self.chat(msgs)).strip()

    # ---- 1. plan ----
    def plan(self, question: str) -> list[str]:
        today = self.now().strftime("%d.%m.%Y")
        out = self._ask(
            f"Bugün {today}. Aşağıdaki araştırma sorusunu internette araştırmak için birbirinden farklı açıları "
            f"kapsayan {self.n_queries} arama sorgusu yaz (gerekirse biri İngilizce olsun). Yalnız JSON dizi döndür, "
            f'açıklama yazma. Örnek: ["sorgu 1", "sorgu 2"]\n\nSoru: {question}')
        m = re.search(r"\[.*\]", out, re.S)
        queries: list[str] = []
        if m:
            try:
                queries = [str(q).strip() for q in json.loads(m.group(0)) if str(q).strip()]
            except ValueError:
                pass
        if not queries:  # model JSON vermediyse satır satır dene
            queries = [re.sub(r'^[\s\-\d.)"]+|"\s*,?$', "", l).strip() for l in out.splitlines()]
            queries = [q for q in queries if len(q) > 3]
        queries = list(dict.fromkeys([question] + queries))  # soru kendisi de aranır
        return queries[: self.n_queries + 1]

    # ---- 2. ara + oku ----
    def gather(self, queries: list[str], progress: Callable[[str], None]) -> list[Source]:
        progress(f"🔎 {len(queries)} sorgu aranıyor…")
        results: list[dict] = []
        with ThreadPoolExecutor(4) as ex:
            for r in ex.map(lambda q: self._safe_search(q), queries):
                results += r
        seen, picked = set(), []
        for r in results:  # sorguların sonuçlarını sırayla karıştır, tekrarları ve video sitelerini at
            url = r.get("href", "")
            key = re.sub(r"[?#].*$", "", url).rstrip("/")
            if not url or key in seen or any(s in url for s in SKIP_SITES):
                continue
            seen.add(key)
            picked.append(r)
        picked = picked[: self.max_pages + 4]  # okunamayanlar olur: biraz fazla dene
        progress(f"📄 {len(picked)} sayfa okunuyor…")
        texts: dict[int, str] = {}
        ex = ThreadPoolExecutor(6)
        futs = {ex.submit(self.read_page, r["href"]): i for i, r in enumerate(picked)}
        done, _ = wait(futs, timeout=12)
        ex.shutdown(wait=False, cancel_futures=True)
        for f in done:
            try:
                t = f.result()
                if len(t) > 300:
                    texts[futs[f]] = t
            except Exception:  # noqa: BLE001 — okunamayan sayfa atlanır
                pass
        sources = []
        for i, r in enumerate(picked):
            if i in texts and len(sources) < self.max_pages:
                sources.append(Source(len(sources) + 1, r.get("title", ""), r["href"], texts[i]))
        progress(f"📄 {len(sources)} sayfa okundu.")
        return sources

    def _safe_search(self, q: str) -> list[dict]:
        try:
            return self.search(q, 6)
        except Exception:  # noqa: BLE001
            return []

    # ---- 3. sayfa başına not ----
    def take_notes(self, question: str, sources: list[Source], progress: Callable[[str], None]) -> list[Source]:
        kept = []
        for i, s in enumerate(sources, 1):
            progress(f"📝 Not alınıyor {i}/{len(sources)}: {s.title[:50]}")
            s.note = self._ask(
                f"Soru: {question}\nKaynak: {s.title} ({_site(s.url)})\nMetin:\n{s.text[:2500]}\n\n"
                "Bu kaynaktan soruyla ilgili önemli bilgileri 3-6 kısa maddede, somut (sayı, tarih, isim) olarak "
                "Türkçe özetle. Kaynakta olmayanı yazma. Kaynak soruyla ilgisizse yalnız İLGİSİZ yaz.")
            if s.note and "İLGİSİZ" not in s.note.upper()[:20]:
                kept.append(s)
        for n, s in enumerate(kept, 1):
            s.n = n
        return kept

    # ---- 4. rapor ----
    def write(self, question: str, sources: list[Source], on_text: Callable[[str], None]) -> str:
        notes = "\n\n".join(f"[{s.n}] {s.title} ({_site(s.url)})\n{s.note}" for s in sources)
        prompt = (
            f"Araştırma sorusu: {question}\n\nKaynak notları:\n{notes}\n\n"
            "Bu notlara dayanarak Türkçe, düzenli bir araştırma raporu yaz:\n"
            "- İlk satır 'Özet: ' ile başlasın ve soruyu 2 cümlede cevaplasın.\n"
            "- Sonra ## başlıklar altında ana bulgular (madde işaretleri kullanabilirsin), varsa farklı görüşler "
            "ve çelişkiler, en sonda ## Sonuç.\n"
            "- Her bilginin sonuna kaynağını [1], [2] gibi yaz. Notlarda olmayan bilgi ekleme, tahmin yürütüyorsan "
            "belirt. Kaynak listesini yazma (ayrıca eklenecek).")
        out = []
        msgs = [{"role": "user", "content": prompt}]
        for piece in self.chat(msgs):
            out.append(piece)
            on_text(piece)
        return "".join(out).strip()

    # ---- hepsi ----
    def run(self, question: str, progress: Callable[[str], None] = print,
            on_text: Callable[[str], None] = lambda t: None, save: bool = True) -> Report:
        rep = Report(question)
        progress("🧭 Araştırma planlanıyor…")
        rep.queries = self.plan(question)
        progress("Sorgular: " + " · ".join(rep.queries))
        sources = self.gather(rep.queries, progress)
        if not sources:
            rep.text = "Özet: İnternetten okunabilir kaynak bulamadım; bağlantıyı ya da soruyu kontrol et."
            on_text(rep.text)
            return rep
        rep.sources = self.take_notes(question, sources, progress) or sources
        if all(not s.note for s in rep.sources):
            for s in rep.sources:
                s.note = s.text[:600]
        progress(f"✍️ Rapor yazılıyor ({len(rep.sources)} kaynak)…")
        rep.text = self.write(question, rep.sources, on_text)
        if save:
            rep.path = self.save(rep)
        return rep

    def save(self, rep: Report) -> Path:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        slug = re.sub(r"[^\w]+", "_", rep.question.lower())[:50].strip("_")
        path = OUT_DIR / f"{self.now():%Y-%m-%d_%H%M}_{slug}.md"
        refs = "\n".join(f"{s.n}. [{s.title}]({s.url})" for s in rep.sources)
        path.write_text(f"# {rep.question}\n\n_{self.now():%d.%m.%Y %H:%M} · TOM derin araştırma · "
                        f"sorgular: {', '.join(rep.queries)}_\n\n{rep.text}\n\n## Kaynaklar\n\n{refs}\n",
                        encoding="utf-8")
        return path


def _site(url: str) -> str:
    from urllib.parse import urlparse

    return urlparse(url).netloc.removeprefix("www.")


def default_research(model: str, options: dict | None = None) -> DeepResearch:
    """TOM'un Ollama modeli + ddgs araması + trafilatura ile."""
    from tom.brain.ollama_client import stream_chat
    from tom.tools import web

    # Asistanla AYNI seçenekler: num_ctx/num_gpu değişirse Ollama modeli yeniden yükler (yavaş) ve GPU'da daha çok
    # yer tutar (Whisper OOM). 8 kaynağın notları + 2500 karakterlik sayfa metni 4096 bağlama sığar.
    opts = dict(options or {})
    return DeepResearch(chat=lambda msgs: stream_chat(msgs, model, options=opts),
                        search=lambda q, n: web._search(q, n), read_page=lambda u: web.page_text(u, limit=4000))
