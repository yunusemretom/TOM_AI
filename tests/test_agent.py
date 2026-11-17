from tom.brain.agent import Agent, AgentTurn
from tom.tools.base import Tool, Toolbox


def scripted_chat(script):
    """Her çağrıda sıradaki olay listesini akıtır; gelen mesajları kaydeder."""
    seen = []

    def chat(msgs, model, tools=None, options=None, think=False):
        seen.append((list(msgs), tools, think))
        yield from script.pop(0)
    return chat, seen


def box():
    return Toolbox([Tool("web_ara", "ara", {"sorgu": {"type": "string"}}, ["sorgu"],
                         lambda sorgu: f"Sonuç: {sorgu} = 3-1")])


def test_plain_answer_streams_without_tools():
    chat, seen = scripted_chat([[("text", "Merhaba "), ("text", "Yunus.")]])
    turn = AgentTurn()
    out = "".join(Agent(chat, "m", box()).stream([{"role": "user", "content": "selam"}], turn))
    assert out == "Merhaba Yunus." and turn.trace == [] and len(seen) == 1


def test_tool_call_says_filler_runs_tool_and_answers():
    chat, seen = scripted_chat([
        [("tools", [{"function": {"name": "web_ara", "arguments": {"sorgu": "maç"}}}])],
        [("text", "Maç 3-1 bitti.")],
    ])
    turn = AgentTurn()
    out = "".join(Agent(chat, "m", box()).stream([{"role": "user", "content": "maç?"}], turn))
    assert out == "Hemen araştırıyorum.Maç 3-1 bitti."  # dolgu ayrı bir Spoken parçası olarak gelir
    assert turn.tools_used == ["web_ara"]
    second_msgs = seen[1][0]
    assert second_msgs[-1] == {"role": "tool", "tool_name": "web_ara", "content": "Sonuç: maç = 3-1"}
    assert second_msgs[-2]["tool_calls"][0]["function"]["name"] == "web_ara"


def test_last_round_disables_tools_and_errors_reach_model():
    loop = [("tools", [{"function": {"name": "yok", "arguments": "{}"}}])]
    chat, seen = scripted_chat([loop, loop, [("text", "Bulamadım.")]])
    turn = AgentTurn()
    out = "".join(Agent(chat, "m", box(), max_rounds=2).stream([], turn))
    assert out.endswith("Bulamadım.") and out.count("Bir bakayım.") == 1
    assert seen[-1][1] is None  # son çağrıda araç listesi gönderilmedi
    assert "Hata" in seen[1][0][-1]["content"]


def test_toolbox_validates_and_truncates():
    t = Toolbox([Tool("uzun", "x", {"n": {"type": "integer"}}, ["n"], lambda n: "a" * 5000)])
    assert t.run("uzun", {}) .startswith("Hata: eksik")
    r = t.run("uzun", {"n": 1, "fazla": 2})
    assert len(r) < 3100 and r.endswith("(kısaltıldı)")


def test_raw_tool_call_text_is_parsed_not_spoken():
    raw = 'web_ara{sorgu:<|"|>Galatasaray maçı sonucu<|"|>}<tool_call|>'
    chat, seen = scripted_chat([
        [("text", raw[:9]), ("text", raw[9:30]), ("text", raw[30:])],
        [("text", "Maç 2-0 bitti.")],
    ])
    turn = AgentTurn()
    out = "".join(Agent(chat, "m", box()).stream([], turn))
    assert out == "Hemen araştırıyorum.Maç 2-0 bitti."
    assert turn.tools_used == ["web_ara"]
    assert seen[1][0][-1]["content"] == "Sonuç: Galatasaray maçı sonucu = 3-1"


def test_parse_raw_calls_variants():
    from tom.brain.agent import parse_raw_calls

    names = {"hava_tahmini", "uygulama_ac"}
    assert parse_raw_calls('hava_tahmini{gun:1,sehir:<|"|>İzmir<|"|>}<tool_call|>', names) == \
        [{"function": {"name": "hava_tahmini", "arguments": {"gun": 1, "sehir": "İzmir"}}}]
    assert parse_raw_calls('<|tool_call>call:uygulama_ac{ad:<|"|>Firefox<|"|>}', names)[0]["function"]["arguments"] \
        == {"ad": "Firefox"}
    assert parse_raw_calls("Hava bugün güzel.", names) is None


def test_normal_text_starting_like_a_word_is_not_held_forever():
    chat, _ = scripted_chat([[("text", "Hava "), ("text", "bugün güzel.")]])
    out = "".join(Agent(chat, "m", box()).stream([], AgentTurn()))
    assert out == "Hava bugün güzel."


def test_python_style_raw_call():
    from tom.brain.agent import parse_raw_calls

    names = {"web_ara", "hava_tahmini"}
    assert parse_raw_calls('web_ara(sorgu="Galatasaray maçı sonucu")', names) == \
        [{"function": {"name": "web_ara", "arguments": {"sorgu": "Galatasaray maçı sonucu"}}}]
    assert parse_raw_calls('hava_tahmini(gun=1,sehir="İzmir")', names)[0]["function"]["arguments"] == \
        {"gun": 1, "sehir": "İzmir"}
    assert parse_raw_calls("web_ara(os.system('x'))", names) is None


def test_expected_tool_skipped_is_forced_by_name_then_thinking_and_never_spoken():
    chat, seen = scripted_chat([
        [("text", "Tamam, kurdum.")],                                                  # yalan: araç yok
        [("text", "Kurdum dedim ya.")],                                                # zorlama da tutmadı
        [("tools", [{"function": {"name": "web_ara", "arguments": {"sorgu": "x"}}}])],  # düşünerek: doğru
        [("text", "Kuruldu.")],
    ])
    turn = AgentTurn()
    out = "".join(Agent(chat, "m", box()).stream([], turn, expect_tool=["web_ara"]))
    assert "kurdum" not in out.lower() and out.endswith("Kuruldu.")
    assert turn.retried and [s[2] for s in seen] == [False, False, None, False]
    assert "web_ara aracını çağır" in seen[1][0][-1]["content"]
    assert not any("aracını çağır" in m.get("content", "") for m in seen[3][0])  # zorlama notu sonra silinir


def test_skipped_no_arg_tool_is_called_directly_without_retry():
    news = Toolbox([Tool("haberler", "haber", {"konu": {"type": "string"}}, [], lambda konu="": "başlıklar")])
    chat, seen = scripted_chat([[("text", "Haberlere erişimim yok.")], [("text", "Gündem şöyle.")]])
    turn = AgentTurn()
    out = "".join(Agent(chat, "m", news).stream([], turn, expect_tool=["haberler"]))
    assert out == "Haberlere bakıyorum.Gündem şöyle." and turn.tools_used == ["haberler"] and len(seen) == 2


def test_positional_and_colon_raw_calls():
    from tom.brain.agent import parse_raw_calls

    p = {"web_ara": ["sorgu"]}
    for raw in ['web_ara("bu yıl nobel ödülü")', 'web_ara(sorgu: "bu yıl nobel ödülü")']:
        assert parse_raw_calls(raw, {"web_ara"}, p)[0]["function"]["arguments"] == {"sorgu": "bu yıl nobel ödülü"}


def test_unquoted_raw_call_is_recovered_not_spoken():
    from tom.brain.agent import parse_raw_calls

    p = {"web_ara": ["sorgu"], "doviz": ["kaynak", "hedef", "miktar"]}
    r = parse_raw_calls("web_ara(sorgu:Dünya Kupası elemelerinde Türkiye'nin son maçı sonucu)", set(p), p)
    assert r[0]["function"]["arguments"] == {"sorgu": "Dünya Kupası elemelerinde Türkiye'nin son maçı sonucu"}
    assert parse_raw_calls("doviz(USD, TRY)", set(p), p) is None  # belirsiz çok parametre: tahmin yok


def test_unparseable_raw_call_triggers_retry_instead_of_speaking():
    chat, seen = scripted_chat([
        [("text", "web_ara(sorgu: x, y, z, ???)")],
        [("text", "Bulamadım.")],
    ])
    box2 = Toolbox([Tool("web_ara", "ara", {"sorgu": {"type": "string"}, "ek": {"type": "string"}}, ["sorgu"],
                         lambda sorgu, ek="": "x")])
    out = "".join(Agent(chat, "m", box2).stream([], AgentTurn()))
    assert "web_ara" not in out and out == "Bulamadım."


def test_forced_retry_without_false_claim_is_spoken_not_thought():
    chat, seen = scripted_chat([
        [("text", "Ne zaman hatırlatayım?")],
        [("text", "Hangi saatte hatırlatmamı istersin?")],
    ])
    turn = AgentTurn()
    out = "".join(Agent(chat, "m", box()).stream([], turn, expect_tool=["web_ara"]))
    assert out == "Hangi saatte hatırlatmamı istersin?" and len(seen) == 2  # düşünme moduna geçilmedi


def test_negative_requests_get_no_hint():
    from tom.brain.agent import hinted_tools, tool_hint

    assert tool_hint("Hayır, bir şey hatırlatmanı istemiyorum") is None
    assert hinted_tools("YouTube'u açma") == []
