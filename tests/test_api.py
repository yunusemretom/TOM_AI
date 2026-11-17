import asyncio
import json

from tom.api import TomBrain, make_app, text_of, tool_status
from tom.research import Report, Source
from tom.tools.base import Tool, Toolbox
from tom.tools.memory import Memory


class FakePersona:
    def chat_prompt(self, now=None, facts=None):
        return "SİSTEM " + ";".join(facts or [])


def brain(tmp_path, script, voice=False, research=None):
    seen = []

    def chat(msgs, model, tools=None, options=None, think=False):
        seen.append({"msgs": list(msgs), "tools": tools, "options": options})
        yield from script.pop(0)

    box = Toolbox([Tool("web_ara", "ara", {"sorgu": {"type": "string"}}, ["sorgu"], lambda sorgu: "Sonuç 3-1")])
    b = TomBrain("m", {"num_ctx": 8192}, {"num_ctx": 4096, "num_gpu": 26}, chat=chat, toolbox=box,
                 persona=FakePersona(), memory=Memory(tmp_path / "h.json"), research_factory=research,
                 is_voice_running=lambda: voice)
    b.plain_chat = lambda msgs, model, options=None: iter(["Başlık"])
    return b, seen


def test_text_of_handles_content_parts():
    assert text_of("selam") == "selam"
    assert text_of([{"type": "text", "text": "a"}, {"type": "image_url", "image_url": {}}, {"type": "text", "text": "b"}]) == "a\nb"
    assert text_of(None) == ""
    assert "web_ara: maç" in tool_status("web_ara", {"sorgu": "maç"})


def test_answer_uses_persona_tools_and_drops_spoken_filler(tmp_path):
    b, seen = brain(tmp_path, [
        [("tools", [{"function": {"name": "web_ara", "arguments": {"sorgu": "maç"}}}])],
        [("text", "Maç **3-1** bitti.")],
    ])
    b.memory.hatirla("Fenerbahçeli")
    out = "".join(b.answer([{"role": "system", "content": "Kısa yaz"},
                            {"role": "user", "content": "dünkü maç kaç kaç bitti?"}]))
    assert "Hemen araştırıyorum" not in out and "Bir bakayım" not in out  # sesli dolgu yazılıda yok
    assert "> 🔎 _web_ara: maç_" in out and out.endswith("Maç **3-1** bitti.")
    sys = seen[0]["msgs"][0]
    assert sys["role"] == "system" and sys["content"].startswith("SİSTEM Fenerbahçeli") and "Kısa yaz" in sys["content"]
    assert seen[0]["options"] == {"num_ctx": 8192}


def test_voice_running_switches_to_voice_options(tmp_path):
    b, seen = brain(tmp_path, [[("text", "Selam.")]], voice=True)
    assert "".join(b.answer([{"role": "user", "content": "selam"}])) == "Selam."
    assert seen[0]["options"] == {"num_ctx": 4096, "num_gpu": 26}


def test_openwebui_task_prompt_bypasses_agent(tmp_path):
    b, seen = brain(tmp_path, [])
    out = "".join(b.answer([{"role": "user", "content": "### Task:\nGenerate a concise title..."}]))
    assert out == "Başlık" and seen == []


def test_history_is_trimmed(tmp_path):
    b, seen = brain(tmp_path, [[("text", "ok")]])
    b.max_history = 4
    msgs = [{"role": "user" if i % 2 == 0 else "assistant", "content": f"m{i}"} for i in range(11)]
    "".join(b.answer(msgs))
    assert [m["content"] for m in seen[0]["msgs"][1:]] == ["m7", "m8", "m9", "m10"]


class FakeResearch:
    def run(self, question, progress, on_text):
        progress("🧭 Plan")
        on_text("Özet: cevap [1]")
        return Report(question, sources=[Source(1, "Kaynak A", "https://a.com")])


def test_research_streams_progress_report_and_sources(tmp_path):
    b, _ = brain(tmp_path, [], research=FakeResearch)
    out = "".join(b.research([{"role": "user", "content": "soru"}]))
    assert out.startswith("> 🧭 Plan") and "Özet: cevap [1]" in out
    assert "### Kaynaklar\n1. [Kaynak A](https://a.com)" in out


def run_client(app, fn):
    from aiohttp.test_utils import TestClient, TestServer

    async def go():
        async with TestClient(TestServer(app)) as c:
            return await fn(c)
    return asyncio.run(go())


def test_http_models_stream_and_auth(tmp_path):
    b, _ = brain(tmp_path, [[("text", "Mer"), ("text", "haba")], [("text", "Tek")]])
    app = make_app(b, api_key="k")
    H = {"Authorization": "Bearer k"}

    async def fn(c):
        assert (await c.get("/v1/models")).status == 401
        ids = [m["id"] for m in (await (await c.get("/v1/models", headers=H)).json())["data"]]
        r = await c.post("/v1/chat/completions", headers=H, json={
            "model": "tom", "stream": True, "messages": [{"role": "user", "content": "selam"}]})
        body = await r.text()
        r2 = await c.post("/v1/chat/completions", headers=H, json={
            "model": "tom", "messages": [{"role": "user", "content": "selam"}]})
        bad = await c.post("/v1/chat/completions", headers=H, json={"model": "x", "messages": []})
        return ids, r.headers["Content-Type"], body, await r2.json(), bad.status

    ids, ctype, body, plain, bad = run_client(app, fn)
    assert ids == ["tom", "tom-derin"] and ctype.startswith("text/event-stream") and bad == 404
    events = [l[6:] for l in body.splitlines() if l.startswith("data: ")]
    assert events[-1] == "[DONE]"
    chunks = [json.loads(e) for e in events[:-1]]
    assert "".join(c["choices"][0]["delta"].get("content", "") for c in chunks) == "Merhaba"
    assert chunks[-1]["choices"][0]["finish_reason"] == "stop"
    assert plain["choices"][0]["message"]["content"] == "Tek"
