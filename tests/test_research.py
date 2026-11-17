import datetime as dt

from tom.research import DeepResearch


def make(tmp_path, monkeypatch):
    import tom.research as r

    monkeypatch.setattr(r, "OUT_DIR", tmp_path)
    asked = []

    def chat(msgs):
        p = msgs[-1]["content"]
        asked.append(p)
        if "JSON dizi" in p:
            yield '["yapay zeka çip ihracatı", "nvidia export controls"]'
        elif "Kaynak:" in p:
            yield "İLGİSİZ" if "Tarif" in p else "- Nvidia H20 satışı kısıtlandı (2025) "
        else:
            yield "Özet: Nvidia ABD kısıtları yüzünden satış yapamıyor [1].\n\n## Bulgular\n- Kısıt [1]\n\n## Sonuç\nTamam."

    def search(q, n):
        return [{"title": "Haber A", "href": "https://a.com/x", "body": ""},
                {"title": "Tarif", "href": "https://b.com/y", "body": ""},
                {"title": "Video", "href": "https://youtube.com/watch?v=1", "body": ""},
                {"title": "Haber A tekrar", "href": "https://a.com/x?utm=1", "body": ""}]

    return DeepResearch(chat, search, lambda u: "metin " * 100, now=lambda: dt.datetime(2026, 11, 17, 15, 0)), asked


def test_full_research_flow(tmp_path, monkeypatch):
    dr, asked = make(tmp_path, monkeypatch)
    steps, streamed = [], []
    rep = dr.run("Nvidia çiplerini neden kısıtlıyor?", progress=steps.append, on_text=streamed.append)
    assert rep.queries[0] == "Nvidia çiplerini neden kısıtlıyor?" and "nvidia export controls" in rep.queries
    assert [s.url for s in rep.sources] == ["https://a.com/x"]  # tekrar, video ve ilgisiz kaynak atıldı
    assert rep.summary == "Nvidia ABD kısıtları yüzünden satış yapamıyor [1]."
    assert "".join(streamed) == rep.text and any("Rapor yazılıyor" in s for s in steps)
    md = rep.path.read_text()
    assert md.startswith("# Nvidia") and "## Kaynaklar" in md and "1. [Haber A](https://a.com/x)" in md


def test_plan_falls_back_when_no_json(tmp_path, monkeypatch):
    dr, _ = make(tmp_path, monkeypatch)
    dr.chat = lambda msgs: iter(["1. birinci sorgu\n2. ikinci sorgu"])
    assert dr.plan("soru") == ["soru", "birinci sorgu", "ikinci sorgu"]
