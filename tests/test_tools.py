import datetime as dt

import pytest

from tom.tools.info import hesapla
from tom.tools.memory import Memory


@pytest.mark.parametrize("e,out", [("2+3*4", "14"), ("(125*18)/3", "750"), ("sqrt(16)", "4"),
                                   ("10/4", "2.5"), ("2^10", "1024"), ("3,5*2", "7")])
def test_hesapla(e, out):
    assert hesapla(e).endswith("= " + out)


@pytest.mark.parametrize("bad", ["__import__('os')", "open('x')", "2**10000", "a+1"])
def test_hesapla_rejects_unsafe(bad):
    with pytest.raises(Exception):
        hesapla(bad)


def test_memory_facts_notes_and_reminders(tmp_path):
    now = [dt.datetime(2026, 11, 17, 9, 0)]
    m = Memory(tmp_path / "h.json", now=lambda: now[0])
    m.hatirla("Doğum günü 3 Mart.")
    m.hatirla("Doğum günü 3 Mart.")
    assert m.facts == ["Doğum günü 3 Mart."]
    m.not_al("Süt al")
    assert "Süt al" in m.notlari_oku()
    assert m.hatirlatici_kur("2026-11-17 08:00", "geçmiş").startswith("Hata")
    assert "kuruldu" in m.hatirlatici_kur("2026-11-17 09:30", "Toplantı")
    assert m.due() == []
    now[0] = dt.datetime(2026, 11, 17, 9, 30)
    assert [x["mesaj"] for x in m.due()] == ["Toplantı"]
    assert m.due() == [] and "yok" in m.hatirlaticilar()
    m2 = Memory(tmp_path / "h.json", now=lambda: now[0])  # diske yazıldı mı
    assert m2.facts == ["Doğum günü 3 Mart."] and len(m2.data["notlar"]) == 1
    assert "Silindi" in m2.unut("doğum")


def test_site_ac_builds_safe_urls(monkeypatch):
    from tom.tools import pc

    opened = []
    monkeypatch.setattr(pc.subprocess, "Popen", lambda cmd, **kw: opened.append(cmd))
    pc.site_ac("youtube.com")
    pc.site_ac("python dersleri")
    pc.site_ac("https://ornek.org/x")
    assert [c[1] for c in opened] == ["https://youtube.com", "https://duckduckgo.com/?q=python%20dersleri",
                                     "https://ornek.org/x"]
    assert all(c[0] == "xdg-open" for c in opened)


def test_tool_hint_flags_action_requests():
    from tom.brain.agent import tool_hint

    assert "hatirlatici_kur" in tool_hint("Yarın sabah dokuzda bana toplantıyı hatırlat")
    assert "hatirla" in tool_hint("Bunu hatırla, kahvemi sütsüz içerim")
    assert "sistem_durumu" in tool_hint("Bilgisayarın durumu nasıl?")
    assert "uygulama_ac" in tool_hint("Firefox'u aç")
    assert "doviz" in tool_hint("Yuro kaç lira?") and "doviz" in tool_hint("Avro kaç TL")
    assert "web_ara" in tool_hint("Yapay zeka son gelişmeler, internetten araştır.")
    assert tool_hint("Bana bir fıkra anlat") is None


def test_weather_skill_leaves_other_cities_to_llm():
    from tom.skills.builtin import WeatherSkill
    from tom.skills.text import normalize

    w = WeatherSkill("Ankara", http=lambda url: {})
    assert w.match(normalize("Hava nasıl?"))
    assert w.match(normalize("Ankara'da yarın hava nasıl"))
    assert w.match(normalize("Yarın hava da güzel mi")) is not None
    assert w.match(normalize("İzmir'de yarın hava nasıl olacak?")) is None
    assert w.match(normalize("Londra'da hava kaç derece")) is None


def test_closer_questions_are_dropped():
    from tom.brain.sentence_splitter import is_filler_closer

    for s in ["Başka bir hesaplama yapmamı ister misin?", "Başka bir hesaplama veya bilgiye ihtiyacın var mı?",
              "Bu konulardan herhangi biri hakkında daha detaylı bilgi ister misin?"]:
        assert is_filler_closer(s), s
    assert not is_filler_closer("Yarın hava güzel olacak.")


def test_spoken_filler_is_emitted_immediately():
    from tom.brain.sentence_splitter import SentenceSplitter, Spoken

    s = SentenceSplitter()
    assert s.feed(Spoken("Tamam.")) == ["Tamam."]  # 20 karakter beklemeden
    assert s.feed("Yarın sabah dokuzda hatırlatacağım. ") + s.flush() == ["Yarın sabah dokuzda hatırlatacağım."]
    from tom.brain.sentence_splitter import strip_closer_tail
    assert strip_closer_tail("Yağmur bekleniyor, başka bir şey ister misin?") == "Yağmur bekleniyor."


def is_closer(x):
    from tom.brain.sentence_splitter import is_filler_closer
    return is_filler_closer(x)


def test_web_search_does_not_wait_for_slow_pages(monkeypatch):
    import time

    from tom.tools import web

    monkeypatch.setattr(web, "_search", lambda q, n, news=False: [
        {"title": f"T{i}", "href": f"https://s{i}.com/x", "body": f"özet {i}"} for i in range(4)])
    monkeypatch.setattr(web, "FETCH_TIMEOUT", 0.3)

    def slow(url, limit=900):
        if "s0" in url:
            time.sleep(3)
        return "metin " + url

    monkeypatch.setattr(web, "page_text", slow)
    t = time.perf_counter()
    out = web.web_ara("deneme")
    assert time.perf_counter() - t < 1.5
    assert "metin https://s1.com/x" in out and "özet 0" in out  # yavaş sayfa yerine özeti kaldı


def test_money_reading_and_speaker_label():
    from tom.brain.sentence_splitter import SentenceSplitter
    from tom.tools.info import okunus

    assert okunus(50.3703, "TRY") == "elli lira otuz yedi kuruş"
    assert okunus(7555.54, "TRY") == "yedi bin beş yüz elli beş lira elli dört kuruş"
    assert okunus(12.0, "USD") == "on iki dolar"
    s = SentenceSplitter()
    assert (s.feed("TOM: Yunus, maç üç iki bitti. ") + s.flush())[0].startswith("Yunus")


def test_greeting_by_time_and_reminders():
    import datetime as dt

    from tom.brain.persona import selam

    assert selam("Yunus", dt.datetime(2026, 11, 17, 8, 0)) == "Günaydın Yunus, hazırım."
    assert selam("Yunus", dt.datetime(2026, 11, 17, 20, 0)).startswith("İyi akşamlar")
    r = [{"zaman": "2026-11-17 21:30", "mesaj": "Annemi ara"}, {"zaman": "2026-11-18 09:00", "mesaj": "x"}]
    assert selam("Yunus", dt.datetime(2026, 11, 17, 20, 0), r).endswith(
        "Bugün saat yirmi bir otuz için bir hatırlatıcın var: Annemi ara.")
    assert "yeniden başladım" in selam("Yunus", restarted=True)


def test_crash_restart_gives_up_after_too_many(monkeypatch, tmp_path):
    import time

    import pytest

    import tom.__main__ as m

    monkeypatch.setattr(m, "HISTORY_FILE", tmp_path / "k.json")
    execs = []
    monkeypatch.setattr(m.os, "execv", lambda exe, argv: execs.append(argv))
    monkeypatch.setenv("TOM_RESTART_TIMES", "")
    monkeypatch.setenv("TOM_RESTARTED", "0")

    class Bot:
        history = [{"role": "user", "content": "selam"}]

    m.restart_after_crash(Bot(), RuntimeError("CUDA failed with error out of memory"))
    assert execs and m.os.environ["TOM_RESTARTED"] == "1" and (tmp_path / "k.json").exists()
    now = time.time()
    monkeypatch.setenv("TOM_RESTART_TIMES", f"{now - 30:.0f},{now - 20:.0f},{now - 10:.0f}")
    with pytest.raises(SystemExit):
        m.restart_after_crash(Bot(), RuntimeError("out of memory"))


def test_youtube_opens_site_not_a_keyword_app(monkeypatch):
    from tom.tools import pc

    opened = []
    monkeypatch.setattr(pc.subprocess, "Popen", lambda cmd, **kw: opened.append(cmd))
    monkeypatch.setattr(pc, "installed_apps", lambda: [
        ("Shotwell", "/usr/share/applications/shotwell.desktop", "shotwell fotoğraf youtube flickr"),
        ("Hesap Makinesi", "/usr/share/applications/calc.desktop", "hesap makinesi calculator")])
    assert "youtube.com" in pc.uygulama_ac("YouTube'u")
    assert opened[-1] == ["xdg-open", "https://www.youtube.com"]
    assert "Hesap Makinesi açıldı" in pc.uygulama_ac("hesap makinesi")
    monkeypatch.setattr(pc.shutil, "which", lambda x: "/usr/bin/" + x if x == "google-chrome" else None)
    assert "google-chrome ile" in pc.site_ac("YouTube", tarayici="Chrome'dan")
    assert opened[-1] == ["/usr/bin/google-chrome", "https://www.youtube.com"]


def test_open_hint_catches_inflections():
    from tom.brain.agent import tool_hint

    for q in ["YouTube'u açmanı istiyorum Chrome'dan", "Youtube açtın mı?", "Youtube açılmadı", "Chrome'u başlatır mısın"]:
        assert tool_hint(q) and "site_ac" in tool_hint(q), q


def test_youtube_search_and_play(monkeypatch):
    import io
    import urllib.request

    from tom.tools import pc

    opened = []
    monkeypatch.setattr(pc, "site_ac", lambda url, tarayici="": opened.append((url, tarayici)) or "ok")
    page = '{"videoRenderer":{"videoId":"zd8IFDgQCUc","thumbnail":{},"title":{"runs":[{"text":"Barış Manço - Gülpembe"}]'
    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=0: io.BytesIO(page.encode()))
    assert pc.youtube_ara("barış manço gülpembe", oynat=True) == "YouTube'da ilk video açıldı: Barış Manço - Gülpembe"
    assert opened[-1] == ("https://www.youtube.com/watch?v=zd8IFDgQCUc", "")
    pc.youtube_ara("lo-fi müzik", tarayici="chrome")
    assert opened[-1] == ("https://www.youtube.com/results?search_query=lo-fi+m%C3%BCzik", "chrome")


def test_youtube_and_volume_hints():
    from tom.brain.agent import hinted_tools

    assert "youtube_ara" in hinted_tools("YouTube'da Barış Manço'nun Gülpembe şarkısını aç")
    assert "ses_ayarla" in hinted_tools("Ses yüzde kırk olsun mu acaba")
    assert "parlaklik_ayarla" in hinted_tools("Parlaklık biraz fazla gibi")
