"""Bilgi araçları: hesap makinesi, döviz, hava tahmini (anahtarsız servisler)."""

from __future__ import annotations

import ast
import json
import math
import operator as op
import urllib.parse
import urllib.request

_OPS = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv, ast.FloorDiv: op.floordiv,
        ast.Mod: op.mod, ast.Pow: op.pow, ast.USub: op.neg, ast.UAdd: op.pos}
_FUNCS = {k: getattr(math, k) for k in ("sqrt", "sin", "cos", "tan", "log", "log10", "exp", "floor", "ceil")}
_FUNCS.update(abs=abs, round=round)
_CONST = {"pi": math.pi, "e": math.e}


def _eval(node):
    if isinstance(node, ast.Expression):
        return _eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        if isinstance(node.op, ast.Pow) and abs(_eval(node.right)) > 100:
            raise ValueError("üs çok büyük")
        return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.operand))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _FUNCS:
        return _FUNCS[node.func.id](*[_eval(a) for a in node.args])
    if isinstance(node, ast.Name) and node.id in _CONST:
        return _CONST[node.id]
    raise ValueError("desteklenmeyen ifade")


def hesapla(ifade: str) -> str:
    """Güvenli hesap: yalnız sayılar, + - * / // % **, parantez ve birkaç matematik fonksiyonu."""
    e = ifade.replace("×", "*").replace("÷", "/").replace("^", "**").replace(",", ".")
    v = _eval(ast.parse(e, mode="eval"))
    if isinstance(v, float):
        v = round(v, 6)
        if v.is_integer():
            v = int(v)
    return f"{ifade} = {v}"


def _get_json(url: str, timeout: float = 8) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "tom-asistan"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


_AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım",
          "Aralık"]
_PARA = {"TRY": ("lira", "kuruş"), "USD": ("dolar", "sent"), "EUR": ("avro", "sent"), "GBP": ("sterlin", "peni")}


def okunus(x: float, code: str) -> str:
    """Sesli okuma için: 7555.54 TRY → 'yedi bin beş yüz elli beş lira elli dört kuruş'."""
    from tom.skills.text import sayi_yaz

    whole, frac = int(x), round((x - int(x)) * 100)
    if frac == 100:
        whole, frac = whole + 1, 0
    unit, sub = _PARA.get(code, (code, ""))
    if whole > 9999:  # sayi_yaz 0-9999
        s = f"{whole:,}".replace(",", ".") + f" {unit}"
    else:
        s = f"{sayi_yaz(whole)} {unit}"
    return s + (f" {sayi_yaz(frac)} {sub}" if frac and sub else "")


_ALIASES = {"dolar": "USD", "usd": "USD", "euro": "EUR", "avro": "EUR", "eur": "EUR", "sterlin": "GBP",
            "pound": "GBP", "gbp": "GBP", "lira": "TRY", "tl": "TRY", "try": "TRY", "türk lirası": "TRY",
            "yen": "JPY", "frank": "CHF", "ruble": "RUB", "yuan": "CNY", "riyal": "SAR", "manat": "AZN"}


def _code(x: str) -> str:
    x = x.strip().lower()
    return _ALIASES.get(x, x.upper())


def doviz(kaynak: str = "USD", hedef: str = "TRY", miktar: float = 1) -> str:
    k, h = _code(kaynak), _code(hedef)
    d = _get_json(f"https://open.er-api.com/v6/latest/{k}")
    if d.get("result") != "success" or h not in d.get("rates", {}):
        return f"Kur bulunamadı: {k}→{h}."
    rate = d["rates"][h]
    total = miktar * rate
    when = ""
    try:
        import email.utils
        t = email.utils.parsedate_to_datetime(d.get("time_last_update_utc", ""))
        when = f"; kur {t.day} {_AYLAR[t.month - 1]} tarihli"
    except (TypeError, ValueError):
        pass
    return (f"{miktar:g} {k} = {total:.2f} {h} (okunuşu: {okunus(total, h)}; 1 {k} = {rate:.4f} {h}{when})")


_WMO = {0: "açık", 1: "çoğunlukla açık", 2: "parçalı bulutlu", 3: "kapalı", 45: "sisli", 48: "kırağılı sis",
        51: "hafif çisenti", 53: "çisenti", 55: "yoğun çisenti", 61: "hafif yağmurlu", 63: "yağmurlu",
        65: "kuvvetli yağmurlu", 71: "hafif karlı", 73: "karlı", 75: "yoğun karlı", 80: "sağanak",
        81: "kuvvetli sağanak", 82: "şiddetli sağanak", 95: "gök gürültülü fırtına", 96: "dolulu fırtına"}


def hava_tahmini(sehir: str, gun: int = 3) -> str:
    g = _get_json("https://geocoding-api.open-meteo.com/v1/search?count=1&language=tr&name="
                  + urllib.parse.quote(sehir))
    if not g.get("results"):
        return f"'{sehir}' bulunamadı."
    p = g["results"][0]
    gun = max(1, min(int(gun), 7))
    f = _get_json(f"https://api.open-meteo.com/v1/forecast?latitude={p['latitude']}&longitude={p['longitude']}"
                  f"&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max"
                  f"&current=temperature_2m,weather_code&timezone=auto&forecast_days={gun}")
    cur = f.get("current", {})
    d = f["daily"]
    r = lambda v: round(v) if isinstance(v, (int, float)) else v  # sesli okumada ondalık tuhaf duruyor
    lines = [f"{p['name']} ({p.get('country', '')}) şu an {r(cur.get('temperature_2m'))} derece, "
             f"{_WMO.get(cur.get('weather_code'), '')}."]
    for i, day in enumerate(d["time"]):
        lines.append(f"{day}: {_WMO.get(d['weather_code'][i], '')}, en yüksek {r(d['temperature_2m_max'][i])} derece, "
                     f"en düşük {r(d['temperature_2m_min'][i])} derece, yağış ihtimali "
                     f"yüzde {d['precipitation_probability_max'][i]}")
    return "\n".join(lines)
