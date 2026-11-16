"""Ollama'ya akışlı sohbet isteği (ek bağımlılık yok, düz HTTP)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Iterator

DEFAULT_HOST = "http://localhost:11434"


def _post(host: str, path: str, body: dict, timeout: float = 300):
    req = urllib.request.Request(
        host + path, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}
    )
    return urllib.request.urlopen(req, timeout=timeout)


def stream_chat(
    messages: list[dict],
    model: str,
    *,
    host: str = DEFAULT_HOST,
    options: dict | None = None,
    keep_alive: str | int = "30m",
    think: bool | None = False,
) -> Iterator[str]:
    """Yanıt metnini geldiği gibi parça parça verir.

    `think=False`: düşünme modu olan modellerde (gemma4, qwen3) gizli akıl yürütmeyi kapatır,
    yoksa ilk kelime saniyelerce gecikir. Desteklemeyen modelde alan gönderilmeden yeniden denenir.
    """
    body = {
        "model": model,
        "messages": messages,
        "stream": True,
        "keep_alive": keep_alive,
        "options": options or {},
    }
    if think is not None:
        body["think"] = think
    try:
        resp = _post(host, "/api/chat", body)
    except urllib.error.HTTPError as e:
        if think is not None and e.code == 400:
            body.pop("think")
            resp = _post(host, "/api/chat", body)
        else:
            raise
    with resp:
        for line in resp:
            if not line.strip():
                continue
            msg = json.loads(line)
            if "error" in msg:
                raise RuntimeError(msg["error"])
            piece = msg.get("message", {}).get("content", "")
            if piece:
                yield piece
            if msg.get("done"):
                break


def loaded_models(host: str = DEFAULT_HOST) -> list[dict]:
    """Bellekteki modeller; `size` ve `size_vram` ile GPU'ya ne kadarının sığdığı görülür."""
    with urllib.request.urlopen(host + "/api/ps", timeout=10) as r:
        return json.load(r).get("models", [])


def unload(model: str, host: str = DEFAULT_HOST) -> None:
    with _post(host, "/api/generate", {"model": model, "keep_alive": 0}):
        pass


def unload_all(host: str = DEFAULT_HOST) -> list[str]:
    """Bellekte kalan tüm modelleri boşaltır (GPU'da yer açmak için). Ollama kapalıysa [] döner."""
    try:
        names = [m["name"] for m in loaded_models(host)]
    except Exception:
        return []
    for n in names:
        unload(n, host)
    return names
