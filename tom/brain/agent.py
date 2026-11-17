"""Araçlı ajan: LLM gerekirse araç çağırır (web araması, hatırlatıcı…), sonucu görüp cevabı yazar.

Sesli kullanım için cevap metni parça parça akar (TTS beklemeden başlar). Model araç isteyince
önce kısa bir dolgu cümlesi ("Bir bakayım.") akar; kullanıcı araç çalışırken sessizlikte kalmaz.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from typing import Callable, Iterator

from tom.brain.sentence_splitter import Spoken
from tom.tools.base import Toolbox

FILLER = "Bir bakayım."
# Araca göre dolgu cümlesi (sesleri açılışta önceden üretilir)
FILLERS = {"youtube_ara": "Hemen açıyorum.", "ses_ayarla": "Tamam.", "parlaklik_ayarla": "Tamam.",
           "web_ara": "Hemen araştırıyorum.", "web_oku": "Sayfaya bakıyorum.", "haberler": "Haberlere bakıyorum.",
           "hatirlatici_kur": "Tamam.", "hatirla": "Tamam.", "unut": "Tamam.", "not_al": "Tamam.",
           "hatirlatici_sil": "Tamam.", "uygulama_ac": "Hemen açıyorum.", "site_ac": "Hemen açıyorum.",
           "hesapla": "Hemen hesaplıyorum."}
ALL_FILLERS = sorted({FILLER, *FILLERS.values()})

# Eylem gerektiren istekler: model bazen aracı çağırmadan "kurdum/kaydettim" diyor; bu kalıplarda
# kullanıcı mesajına hangi aracın gerektiği not olarak eklenir.
_HINTS = [
    (re.compile(r"hatırlat|alarm|uyandır|haber ver\b"), "hatirlatici_kur"),
    (re.compile(r"\bhatırla\b|aklında tut|unutma ki|kaydet ki"), "hatirla"),
    (re.compile(r"\bunut\b"), "unut"),
    (re.compile(r"not (al|et|düş)|notlarıma ekle"), "not_al"),
    (re.compile(r"notlar(ım)?\w* (oku|neler|ne var)|notlarımı"), "notlari_oku"),
    (re.compile(r"youtube\w*.*\b(ara|bul|aç|oynat|izle|dinle|çal|koy)\w*"), "youtube_ara"),
    (re.compile(r"\bses\w*\b.*(yüzde|%|\d)|^siz (yüzde|%)"), "ses_ayarla"),
    (re.compile(r"parlaklı\w*"), "parlaklik_ayarla"),
    (re.compile(r"\baç(ar mısın|abilir misin|ma\w*|sana|tın mı|tı mı|ılmadı|ıl)?\b|\bbaşlat\w*"),
     "site_ac ya da uygulama_ac"),
    (re.compile(r"bilgisayar\w* (durum|nasıl)|sistem durum|\bram\b|işlemci|pil(in)? (durum|yüzde)|\bgpu\b"),
     "sistem_durumu"),
    (re.compile(r"\b(kur|kuru|döviz|dolar\w*|euro\w*|yuro|avro\w*|sterlin\w*)\b|kaç (lira|tl|dolar|avro|euro)"),
     "doviz"),
    (re.compile(r"araştır|internet\w*|\bgoogle\w*|\bwebde\b|ara(r mısın|yabilir misin)\b|bul(ur musun|abilir misin)"),
     "web_ara"),
    (re.compile(r"haber|gündem|son dakika"), "haberler"),
    (re.compile(r"\bkaç eder\b|\bhesapla\b|çarpı|bölü|artı|eksi"), "hesapla"),
]


# Ollama Gemma 4'ün araç çağrısını bazen ayrıştıramıyor ve ham metin olarak veriyor:
#   web_ara{sorgu:<|"|>Galatasaray maçı<|"|>}<tool_call|>   (başında <|tool_call>call: da olabilir)
# Böyle bir metin seslendirilmez; çağrı buradan çözülür.
_RAW_CALL = re.compile(r"^\s*(?:<\|tool_call>)?\s*(?:call:)?\s*([a-z_]+)\s*(\{.*?\})\s*(?:<tool_call\|>)?", re.S)
_RAW_HEAD = re.compile(r"^(?:<\|tool_call>|<\|?[a-z_|]*)?\s*(?:call:)?\s*([a-z_]*)([{(])?")


def might_be_raw_call(head: str, names: set[str]) -> bool:
    """Akan metin ham araç çağrısının başı olabilir mi? (o zaman seslendirmeden bekletilir)"""
    m = _RAW_HEAD.match(head)
    name, brace = m.group(1), m.group(2)
    if brace:
        return name in names
    return head == m.group(0) and any(n.startswith(name) for n in names | {"call"})


def _parse_python_calls(text: str, names: set[str], params: dict[str, list[str]] | None = None) -> list[dict] | None:
    """web_ara(sorgu="…"), web_ara("…"), web_ara(sorgu: "…") biçimleri (model bazen böyle yazıyor)."""
    import ast

    src = text.replace("<tool_call|>", "").strip()
    src = re.sub(r'([(,])\s*([A-Za-z_]\w*)\s*:\s*', r"\1\2=", src)  # ad: değer → ad=değer
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None
    calls = []
    for st in tree.body:
        c = st.value if isinstance(st, ast.Expr) else None
        if not (isinstance(c, ast.Call) and isinstance(c.func, ast.Name) and c.func.id in names):
            return None
        order = (params or {}).get(c.func.id, [])
        if len(c.args) > len(order):
            return None
        try:
            args = {order[i]: ast.literal_eval(a) for i, a in enumerate(c.args)}
            args.update({k.arg: ast.literal_eval(k.value) for k in c.keywords})
        except ValueError:
            return None
        calls.append({"function": {"name": c.func.id, "arguments": args}})
    return calls or None


_LOOSE = re.compile(r"^\s*(?:<\|tool_call>)?\s*(?:call:)?\s*([a-z_]+)\s*[({](.*)[)}]\s*(?:<tool_call\|>)?\s*$", re.S)


def _parse_loose(text: str, names: set[str], params: dict[str, list[str]] | None) -> list[dict] | None:
    """Son çare: web_ara(sorgu:Dünya Kupası…) gibi tırnaksız tek parametre → ilk parametreye metnin tamamı."""
    m = _LOOSE.match(text)
    if not m or m.group(1) not in names:
        return None
    order = (params or {}).get(m.group(1), [])
    inner = m.group(2).replace('<|"|>', "").strip()
    if not inner:
        return [{"function": {"name": m.group(1), "arguments": {}}}]
    if not order:
        return None
    inner = re.sub(r"^\s*[A-Za-z_]\w*\s*[:=]\s*", "", inner).strip().strip("\"'")
    if "," in inner and len(order) > 1:
        return None  # çok parametreli ve belirsiz: tahmin etme
    return [{"function": {"name": m.group(1), "arguments": {order[0]: inner}}}]


def looks_like_raw_call(text: str, names: set[str]) -> bool:
    m = _LOOSE.match(text)
    return bool(m and m.group(1) in names)


def parse_raw_calls(text: str, names: set[str], params: dict[str, list[str]] | None = None) -> list[dict] | None:
    """Ham araç çağrısı metnini Ollama biçimine çevirir; değilse None."""
    out = _parse_strict(text, names, params)
    return out if out else _parse_loose(text, names, params)


def _parse_strict(text: str, names: set[str], params: dict[str, list[str]] | None = None) -> list[dict] | None:
    if re.match(r"^\s*[a-z_]+\(", text):
        return _parse_python_calls(text, names, params)
    calls = []
    rest = text
    while rest.strip():
        m = _RAW_CALL.match(rest)
        if not m or m.group(1) not in names:
            return None if not calls else calls
        body = m.group(2).replace('<|"|>', '"')
        body = re.sub(r'([{,])\s*([A-Za-z_]\w*)\s*:', r'\1"\2":', body)  # anahtarları tırnakla
        try:
            args = json.loads(body)
        except ValueError:
            return None
        calls.append({"function": {"name": m.group(1), "arguments": args}})
        rest = rest[m.end():]
    return calls or None


# "hatırlatmanı istemiyorum", "gerek yok": eylem istenmiyor, ipucu verme (yoksa gereksiz yeniden deneme)
_NEGATIVE = re.compile(r"istemiyorum|istemem\b|gerek yok|\bhayır\b|\byapma\b|\bkurma\b|\baçma\b|\bvazgeç|boş ver|iptal")
# Araç çağırmadan iş yaptığını iddia eden cümle: yalnız bu durumda yavaş düşünme moduna geçilir
_CLAIM = re.compile(r"\b(kurdum|kuruyorum|açtım|açıyorum|kaydettim|kaydediyorum|ekledim|ekliyorum|ayarladım|"
                    r"hatırlatacağım|not aldım|sildim|hafızama|baktım)\b", re.I)


def hinted_tools(text: str) -> list[str]:
    t = text.replace("I", "ı").replace("İ", "i").lower()
    if _NEGATIVE.search(t):
        return []
    out: list[str] = []
    for rx, n in _HINTS:
        if rx.search(t):
            out += [x.strip() for x in n.split(" ya da ") if x.strip() not in out]
    return out


def tool_hint(text: str) -> str | None:
    t = text.replace("I", "ı").replace("İ", "i").lower()
    if _NEGATIVE.search(t):
        return None
    names = [n for rx, n in _HINTS if rx.search(t)]
    if not names:
        return None
    return (f"(Sistem notu: bu istek için önce {' / '.join(dict.fromkeys(names))} aracını çağır; "
            "aracı çağırmadan yaptım deme. Cevabın kısa olsun.)")


@dataclass
class AgentTurn:
    """Bir turda olanlar: geçmişe eklenecek araç mesajları ve ölçümler."""
    trace: list[dict] = field(default_factory=list)   # assistant(tool_calls) + tool mesajları
    tools_used: list[str] = field(default_factory=list)
    tool_seconds: float = 0.0
    retried: bool = False  # model aracı atladı, düşünme moduyla yeniden soruldu


class Agent:
    def __init__(self, chat: Callable[..., Iterator[tuple[str, object]]], model: str, toolbox: Toolbox,
                 options: dict | None = None, max_rounds: int = 3, filler: str = FILLER,
                 on_tool: Callable[[str, dict, str], None] | None = None,
                 on_tool_start: Callable[[str, dict], None] | None = None):
        self.chat = chat
        self.model = model
        self.toolbox = toolbox
        self.options = options or {}
        self.max_rounds = max_rounds
        self.filler = filler
        self.on_tool = on_tool or (lambda name, args, result: None)
        self.on_tool_start = on_tool_start or (lambda name, args: None)

    def stream(self, messages: list[dict], turn: AgentTurn, expect_tool: bool | list[str] = False) -> Iterator[str]:
        """expect_tool: kullanıcı bir eylem istedi (hatırlat, aç, haberler…; liste verilirse beklenen araç adları).
        İlk tur seslendirilmeden beklenir; model aracı çağırmazsa ("kurdum" ya da "yapamam" derse) o cevap atılır ve
        kurtarılır: (1) parametresiz araç beklendiyse doğrudan çağrılır, (2) hızlı modda aracın adı söylenerek
        yeniden sorulur, (3) son çare düşünme modu (güvenilir ama 5-15 sn). Gemma 4'te think=False araç
        çağırmayı ~%30 bozuyor."""
        msgs = list(messages)
        said_filler = False
        names = set(self.toolbox.tools)
        params = {n: list(t.params) for n, t in self.toolbox.tools.items()}
        expected = [n for n in (expect_tool if isinstance(expect_tool, list) else []) if n in names]
        attempt = 0     # 0: normal, 1: araç adıyla zorla, 2: düşünerek
        retried = False
        rnd = 0
        while rnd <= self.max_rounds:
            tools = self.toolbox.schemas() if rnd < self.max_rounds else None  # son turda araç yok: cevap yazsın
            buffer_all = bool(expect_tool) and rnd == 0 and attempt < 2
            think = None if attempt == 2 and rnd == 0 else False
            if rnd == 0 and attempt == 1:
                want = " ya da ".join(expected) or "uygun"
                msgs = list(messages) + [{"role": "system", "content":
                                          f"Bu isteği yerine getirmek için şimdi {want} aracını çağır; metin yazma."}]
            calls: list[dict] = []
            text = ""
            held = ""      # araç adıyla başlayan metin: ham çağrı olabilir, seslendirmeden beklet
            holding = tools is not None
            for kind, payload in self.chat(msgs, self.model, tools=tools, options=self.options, think=think):
                if kind == "tools":
                    calls += payload  # type: ignore[arg-type]
                    continue
                text += payload  # type: ignore[operator]
                if buffer_all:
                    held += payload  # type: ignore[operator]
                    continue
                if holding:
                    held += payload  # type: ignore[operator]
                    if might_be_raw_call(held.lstrip(), names) and len(held) < 1200:
                        continue
                    holding = False
                    yield held
                    held = ""
                else:
                    yield payload  # type: ignore[misc]
            if held:
                raw = parse_raw_calls(held, names, params)
                if raw:
                    calls += raw
                    text = text[:len(text) - len(held)]
                elif (buffer_all or looks_like_raw_call(held, names)) and not calls and attempt < 2:
                    # aracı atladı ya da bozuk çağrı yazdı: söyleme, kurtar
                    turn.retried = True
                    direct = [n for n in expected if not self.toolbox.tools[n].required]
                    if direct and attempt == 0:
                        calls = [{"function": {"name": direct[0], "arguments": {}}}]
                        text = ""
                    elif attempt == 1 and not _CLAIM.search(held) and not looks_like_raw_call(held, names):
                        yield held  # zorlamada da araç yok ama yalan da yok (soru soruyor ya da reddediyor): söyle
                    else:
                        attempt += 1
                        continue
                else:
                    yield held
            if not calls:
                return
            if not said_filler and not text.strip():
                said_filler = True
                first = calls[0].get("function", {}).get("name", "")
                yield Spoken(FILLERS.get(first, self.filler))
            assistant = {"role": "assistant", "content": text, "tool_calls": calls}
            msgs.append(assistant)
            turn.trace.append(assistant)
            t0 = time.perf_counter()
            for c in calls:
                fn = c.get("function", {})
                name = fn.get("name", "")
                args = fn.get("arguments") or {}
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except ValueError:
                        args = {}
                self.on_tool_start(name, args)
                result = self.toolbox.run(name, args)
                self.on_tool(name, args, result)
                turn.tools_used.append(name)
                tool_msg = {"role": "tool", "tool_name": name, "content": result}
                msgs.append(tool_msg)
                turn.trace.append(tool_msg)
            turn.tool_seconds += time.perf_counter() - t0
            rnd += 1
            msgs = [m for m in msgs if not (m.get("role") == "system" and "aracını çağır; metin yazma" in m.get("content", ""))]
