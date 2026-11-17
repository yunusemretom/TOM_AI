"""TOM'un beyni OpenAI uyumlu API olarak: Open WebUI (ya da herhangi bir OpenAI istemcisi) bağlanır.

    PYTHONPATH=. .venv/bin/python -m tom.api            # http://127.0.0.1:8800/v1

Modeller:
- `tom`        Gemma 4 + araçlar (web arama/okuma, haberler, hesap, döviz, hava, not, hafıza, YouTube…)
- `tom-derin`  derin araştırma: plan → çok kaynak → notlar → kaynak numaralı rapor (1-3 dk)

Ses yok: XTTS/Whisper yüklenmez, yalnız Ollama'daki LLM kullanılır. Hafıza (data/hafiza.json) sesli TOM ile
ortaktır. Sesli TOM açıksa onunla aynı model ayarları kullanılır: model iki ayar arasında yeniden
yüklenmez ve GPU'da Whisper'a yer kalır.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import subprocess
import threading
import time
import uuid
from typing import Callable, Iterator

MODELS = {
    "tom": "TOM — araçlı yerel asistan (web, hesap, döviz, hava, hafıza…)",
    "tom-derin": "TOM Derin Araştırma — çok kaynaklı, kaynak numaralı rapor",
}
VOICE_PATTERN = r"\.venv/bin/python -m tom(\.gui)?( |$)"
# Open WebUI'nin başlık/etiket/öneri üretme istekleri ("### Task:" ile başlar): araçsız, kişiliksiz cevaplanır
_TASK = re.compile(r"^\s*###\s*Task:", re.M)
_TOOL_ICON = {"web_ara": "🔎", "web_oku": "📄", "haberler": "📰", "hava_tahmini": "🌤️", "doviz": "💱",
              "hesapla": "🧮", "youtube_ara": "▶️", "site_ac": "🌐", "uygulama_ac": "🖥️", "hatirla": "🧠",
              "not_al": "📝", "hatirlatici_kur": "⏰", "sistem_durumu": "💻"}


def voice_running() -> bool:
    try:
        return subprocess.run(["pgrep", "-f", VOICE_PATTERN], capture_output=True).returncode == 0
    except FileNotFoundError:
        return False


def text_of(content) -> str:
    """OpenAI mesaj içeriği: metin ya da [{"type": "text", "text": ...}, {"type": "image_url"...}]."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(p.get("text", "") for p in content if isinstance(p, dict) and p.get("type") == "text")
    return ""


def tool_status(name: str, args: dict) -> str:
    detail = args.get("sorgu") or args.get("adres") or args.get("konu") or args.get("ifade") or \
        args.get("sehir") or args.get("ad") or args.get("bilgi") or args.get("metin") or ""
    detail = f": {detail}" if detail else ""
    return f"\n> {_TOOL_ICON.get(name, '🔧')} _{name}{detail}_\n\n"


class TomBrain:
    """İstek başına cevap akışı üretir (senkron üreteçler; API bunları thread'de çalıştırır)."""

    def __init__(self, model: str, options: dict, voice_options: dict, max_history: int = 16,
                 chat=None, toolbox=None, persona=None, memory=None, research_factory=None,
                 is_voice_running: Callable[[], bool] = voice_running):
        from tom.brain.ollama_client import stream_chat, stream_chat_events
        from tom.brain.persona import Persona
        from tom.tools.memory import Memory
        from tom.tools.registry import default_toolbox

        self.model = model
        self.base_options, self.voice_options = options, voice_options
        self.max_history = max_history
        self.memory = memory or Memory()
        self.persona = persona or Persona.load()
        self.toolbox = toolbox or default_toolbox(self.memory)
        self.chat_events = chat or stream_chat_events
        self.plain_chat = stream_chat
        self.research_factory = research_factory
        self.is_voice_running = is_voice_running

    def options(self) -> dict:
        return dict(self.voice_options if self.is_voice_running() else self.base_options)

    # ---- tom ----
    def answer(self, messages: list[dict]) -> Iterator[str]:
        from tom.brain.agent import Agent, AgentTurn, hinted_tools, tool_hint
        from tom.brain.sentence_splitter import Spoken

        msgs = [{"role": m["role"], "content": text_of(m.get("content"))} for m in messages
                if m.get("role") in ("user", "assistant", "system")]
        last = next((m["content"] for m in reversed(msgs) if m["role"] == "user"), "")
        if _TASK.search(last):  # Open WebUI görevi (başlık/etiket): olduğu gibi modele
            yield from self.plain_chat(msgs, self.model, options=self.options())
            return
        history = [m for m in msgs if m["role"] != "system"][-self.max_history:]
        system = self.persona.chat_prompt(facts=self.memory.facts)
        extra_system = [m["content"] for m in msgs if m["role"] == "system"]  # Open WebUI'deki sistem istemi
        if extra_system:
            system += "\n\n" + "\n".join(extra_system)
        hint = tool_hint(last)
        if hint and history:  # yazılı sohbette kısa cevap şartı yok
            hint = hint.replace(" Cevabın kısa olsun.", "")
            history[-1] = {"role": "user", "content": history[-1]["content"] + "\n" + hint}
        status: list[str] = []
        agent = Agent(self.chat_events, self.model, self.toolbox, options=self.options(),
                      on_tool_start=lambda name, args: status.append(tool_status(name, args)))
        turn = AgentTurn()
        for piece in agent.stream([{"role": "system", "content": system}] + history, turn,
                                  expect_tool=hinted_tools(last) or bool(hint)):
            while status:
                yield status.pop(0)
            if isinstance(piece, Spoken):  # sesli moddaki "Bir bakayım." yazılıda gereksiz
                continue
            yield piece
        while status:
            yield status.pop(0)

    # ---- tom-derin ----
    def research(self, messages: list[dict]) -> Iterator[str]:
        import queue

        question = next((text_of(m.get("content")) for m in reversed(messages) if m.get("role") == "user"), "")
        if _TASK.search(question):
            yield from self.plain_chat([{"role": "user", "content": question}], self.model, options=self.options())
            return
        if self.research_factory is not None:
            dr = self.research_factory()
        else:
            from tom.research import default_research
            dr = default_research(self.model, self.options())
        q: queue.Queue = queue.Queue()
        done = object()
        result = {}

        def work():
            try:
                result["rep"] = dr.run(question, progress=lambda s: q.put(f"> {s}\n>\n"),
                                       on_text=lambda t: q.put(("text", t)))
            except Exception as e:  # noqa: BLE001
                q.put(f"\n\n**Araştırma hatası:** {type(e).__name__}: {e}\n")
            finally:
                q.put(done)

        threading.Thread(target=work, daemon=True).start()
        started = False
        while True:
            item = q.get()
            if item is done:
                break
            if isinstance(item, tuple):
                if not started:
                    started = True
                    yield "\n"
                yield item[1]
            else:
                yield item
        rep = result.get("rep")
        if rep is not None and rep.sources:
            yield "\n\n### Kaynaklar\n" + "\n".join(f"{s.n}. [{s.title}]({s.url})" for s in rep.sources) + "\n"
            if rep.path:
                yield f"\n_Rapor kaydedildi: `{rep.path}`_\n"


def make_app(brain: TomBrain, api_key: str | None = None):
    from aiohttp import web

    def auth_ok(request) -> bool:
        if not api_key:
            return True
        return request.headers.get("Authorization", "") == f"Bearer {api_key}"

    async def models(request):
        if not auth_ok(request):
            return web.json_response({"error": {"message": "yetkisiz"}}, status=401)
        now = int(time.time())
        return web.json_response({"object": "list", "data": [
            {"id": m, "object": "model", "created": now, "owned_by": "tom", "name": desc}
            for m, desc in MODELS.items()]})

    async def completions(request):
        if not auth_ok(request):
            return web.json_response({"error": {"message": "yetkisiz"}}, status=401)
        body = await request.json()
        model = body.get("model", "tom")
        if model not in MODELS:
            return web.json_response({"error": {"message": f"bilinmeyen model: {model}"}}, status=404)
        gen = brain.research if model == "tom-derin" else brain.answer
        messages = body.get("messages", [])
        cid = f"chatcmpl-{uuid.uuid4().hex[:24]}"
        created = int(time.time())

        loop = asyncio.get_running_loop()
        q: asyncio.Queue = asyncio.Queue()
        end = object()

        def run():
            try:
                for piece in gen(messages):
                    if piece:
                        loop.call_soon_threadsafe(q.put_nowait, piece)
            except Exception as e:  # noqa: BLE001 — hatayı sohbete yaz
                loop.call_soon_threadsafe(q.put_nowait, f"\n\n**Hata:** {type(e).__name__}: {e}")
            finally:
                loop.call_soon_threadsafe(q.put_nowait, end)

        threading.Thread(target=run, daemon=True, name="tom-api").start()

        if not body.get("stream"):
            parts = []
            while (item := await q.get()) is not end:
                parts.append(item)
            text = "".join(parts)
            return web.json_response({
                "id": cid, "object": "chat.completion", "created": created, "model": model,
                "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}})

        resp = web.StreamResponse(headers={"Content-Type": "text/event-stream", "Cache-Control": "no-cache"})
        await resp.prepare(request)

        def chunk(delta: dict, finish=None) -> bytes:
            return ("data: " + json.dumps({"id": cid, "object": "chat.completion.chunk", "created": created,
                                           "model": model, "choices": [{"index": 0, "delta": delta,
                                                                        "finish_reason": finish}]},
                                          ensure_ascii=False) + "\n\n").encode()

        try:
            await resp.write(chunk({"role": "assistant", "content": ""}))
            while (item := await q.get()) is not end:
                await resp.write(chunk({"content": item}))
            await resp.write(chunk({}, "stop"))
            await resp.write(b"data: [DONE]\n\n")
        except (ConnectionResetError, asyncio.CancelledError):
            pass  # kullanıcı durdurdu: üreteç arkada biter
        return resp

    async def health(_):
        return web.json_response({"ok": True, "voice_running": brain.is_voice_running(), "model": brain.model})

    app = web.Application(client_max_size=20 * 1024 * 1024)
    app.router.add_get("/v1/models", models)
    app.router.add_post("/v1/chat/completions", completions)
    app.router.add_get("/health", health)
    return app


def main():
    from aiohttp import web

    ap = argparse.ArgumentParser(prog="tom.api", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8800)
    ap.add_argument("--llm", default="gemma4:e4b")
    ap.add_argument("--api-key", default=os.environ.get("TOM_API_KEY"), help="İsteğe bağlı: Bearer anahtarı")
    args = ap.parse_args()
    base = {"num_ctx": 8192, "temperature": 0.5}  # sesli TOM kapalıyken: GPU tamamen LLM'in, bağlam geniş
    voice = {"num_ctx": 4096, "temperature": 0.4, "num_gpu": 26}  # sesli TOM'un ayarlarıyla birebir
    brain = TomBrain(args.llm, base, voice)
    print(f"TOM API: http://{args.host}:{args.port}/v1  · modeller: {', '.join(MODELS)}  · LLM: {args.llm}", flush=True)
    web.run_app(make_app(brain, args.api_key), host=args.host, port=args.port, print=None)


if __name__ == "__main__":
    main()
