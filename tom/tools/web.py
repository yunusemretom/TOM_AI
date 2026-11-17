"""İnternet araçları: arama (+ en iyi sayfaları okuyup özetlenebilir metin), sayfa okuma, haberler.

Anahtar gerektirmez: arama `ddgs` (DuckDuckGo/Yahoo… metasearch), sayfa metni `trafilatura`.
Sesli kullanım için hız önemli: arama sonucu en iyi 3 sayfayı paralel okur ki model ikinci bir
"sayfayı oku" turuna ihtiyaç duymadan cevap verebilsin.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, wait
from urllib.parse import urlparse

PAGE_CHARS = 900     # sayfa başına modele giden metin
FETCH_TIMEOUT = 3.0  # sn: yavaş site cevabı bekletmesin (yoksa arama özeti kullanılır)


def _search(query: str, n: int, news: bool = False) -> list[dict]:
    from ddgs import DDGS

    last: Exception | None = None
    for backend in ("auto", "yahoo"):  # bazı motorlar zaman zaman boş döner
        try:
            d = DDGS(timeout=8)
            r = (d.news if news else d.text)(query, region="tr-tr", max_results=n, backend=backend)
            if r:
                return r
        except Exception as e:  # noqa: BLE001 — sonraki motoru dene
            last = e
    if last:
        raise RuntimeError(f"arama yapılamadı ({last})")
    return []


def fetch(url: str, timeout: float = 4.0) -> str:
    import urllib.request

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) tom-asistan",
                                               "Accept-Language": "tr,en;q=0.8"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read(2_000_000)
        enc = r.headers.get_content_charset() or "utf-8"
    return raw.decode(enc, errors="replace")


def page_text(url: str, limit: int = PAGE_CHARS) -> str:
    import trafilatura

    html = fetch(url)
    txt = trafilatura.extract(html or "", favor_precision=True, include_comments=False) or ""
    txt = " ".join(txt.split())
    return txt[:limit] + ("…" if len(txt) > limit else "")


def site(url: str) -> str:
    return urlparse(url).netloc.removeprefix("www.")


def web_ara(sorgu: str) -> str:
    results = _search(sorgu, 6)
    if not results:
        return "Sonuç bulunamadı."
    top = results[:3]
    texts: dict[int, str] = {}
    ex = ThreadPoolExecutor(3)
    futs = {ex.submit(page_text, r["href"]): i for i, r in enumerate(top)}
    done, _ = wait(futs, timeout=FETCH_TIMEOUT)
    ex.shutdown(wait=False, cancel_futures=True)  # yavaş site cevabı bekletmesin
    for f in done:
        try:
            texts[futs[f]] = f.result()
        except Exception:  # noqa: BLE001 — okunamayan sayfa atlanır, özet kalır
            pass
    lines = [f"Arama: {sorgu}"]
    for i, r in enumerate(results):
        body = texts.get(i) or r.get("body", "")
        lines.append(f"[{i + 1}] {r.get('title', '')} ({site(r['href'])}): {body}")
    return "\n".join(lines)


def web_oku(adres: str) -> str:
    if not adres.startswith(("http://", "https://")):
        adres = "https://" + adres
    t = page_text(adres, limit=2800)
    return t or "Sayfadan metin çıkarılamadı."


def haberler(konu: str = "") -> str:
    r = _search(konu or "Türkiye gündem son dakika", 8, news=True)
    if not r:
        return "Haber bulunamadı."
    return "\n".join(f"- {x.get('title', '')} ({x.get('source', '')}, {str(x.get('date', ''))[:10]}): "
                     f"{str(x.get('body', ''))[:160]}" for x in r)
