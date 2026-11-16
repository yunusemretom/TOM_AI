import datetime as dt

import pytest

from tom.brain.persona import Persona
from tom.skills.builtin import (ClockSkill, DeviceBackend, DeviceSkill, MediaSkill, TimerSkill,
                                WeatherSkill)
from tom.skills.router import Router
from tom.skills.text import normalize, parse_duration, sayi_yaz, sure_yaz

NOW = dt.datetime(2026, 11, 16, 14, 5)


class FakeCmd:
    def __init__(self, players=("org.mpris.MediaPlayer2.spotify",), status="Paused", volume=50):
        self.players, self.status, self.volume, self.calls = list(players), status, volume, []

    def __call__(self, cmd):
        self.calls.append(cmd)
        if cmd[-1] == "org.freedesktop.DBus.ListNames":
            return "([" + ", ".join(f"'{p}'" for p in self.players) + "],)"
        if "PlaybackStatus" in cmd:
            return f"(<'{self.status}'>,)"
        if cmd[:2] == ["pactl", "get-sink-volume"]:
            return f"Volume: front-left: 32768 / {self.volume}% / -18 dB"
        if cmd[:2] == ["pactl", "set-sink-volume"]:
            self.volume = int(cmd[-1].rstrip("%"))
        return ""


class FakeTimer:
    def __init__(self, secs, fn):
        self.secs, self.fn, self.alive, self.daemon = secs, fn, False, False

    def start(self):
        self.alive = True

    def cancel(self):
        self.alive = False

    def is_alive(self):
        return self.alive


FORECAST = {
    "current": {"temperature_2m": 12.8, "weather_code": 2},
    "daily": {"temperature_2m_max": [15.2, 9.6], "temperature_2m_min": [4.1, 2.0],
              "precipitation_probability_max": [10, 70], "weather_code": [2, 61]},
}


def fake_http(url):
    if "geocoding" in url:
        return {"results": [{"latitude": 39.9, "longitude": 32.8, "name": "Ankara"}]}
    return FORECAST


def make_router(**kw):
    announced = []
    cmd = kw.get("cmd") or FakeCmd()
    skills = [ClockSkill(lambda: NOW), TimerSkill(announced.append, FakeTimer),
              WeatherSkill(kw.get("city", "Ankara"), fake_http), MediaSkill(cmd), DeviceSkill()]
    return Router(skills), announced, cmd


# --- metin yardımcıları ---------------------------------------------------------
def test_normalize_and_numbers():
    assert normalize("Işıkları AÇ, lütfen!") == "ışıkları aç lütfen"
    assert normalize("Saat 14:05 mi?") == "saat 14.05 mi"
    assert sayi_yaz(14) == "on dört"
    assert sayi_yaz(2026) == "iki bin yirmi altı"
    assert sayi_yaz(100) == "yüz"
    assert sure_yaz(90) == "bir dakika otuz saniye"


@pytest.mark.parametrize("text,secs", [
    ("5 dakikalık zamanlayıcı kur", 300),
    ("beş dakika sonra hatırlat", 300),
    ("yirmi beş saniye", 25),
    ("iki buçuk saat", 9000),
    ("yarım saat sonra", 1800),
    ("1 dakika 30 saniye", 90),
    ("on dakika", 600),
    ("birkaç dakika sonra", None),
])
def test_parse_duration(text, secs):
    assert parse_duration(normalize(text)) == secs


# --- yönlendirme: doğru komut ----------------------------------------------------
@pytest.mark.parametrize("text,skill", [
    ("Saat kaç?", "saat"),
    ("Şu an saat kaç acaba", "saat"),
    ("Bugün ayın kaçı?", "saat"),
    ("Bugün günlerden ne?", "saat"),
    ("Hava nasıl?", "hava"),
    ("Bugün hava durumu nasıl olacak?", "hava"),
    ("Yarın yağmur yağacak mı?", "hava"),
    ("Dışarısı kaç derece?", "hava"),
    ("Şemsiye almalı mıyım?", "hava"),
    ("Müzik çal", "medya"),
    ("Biraz müzik açar mısın", "medya"),
    ("Şarkıyı değiştir", "medya"),
    ("Sonraki şarkıya geç", "medya"),
    ("Müziği durdur", "medya"),
    ("Sesi biraz aç", "medya"),
    ("Sesi kıs", "medya"),
    ("Sesi yüzde 40 yap", "medya"),
    ("5 dakikalık zamanlayıcı kur", "zamanlayıcı"),
    ("10 dakika sonra çayı kapatmamı hatırlat", "zamanlayıcı"),
    ("Zamanlayıcıyı iptal et", "zamanlayıcı"),
    ("Işıkları açar mısın?", "cihaz"),
    ("Lambayı kapat", "cihaz"),
    ("Klimayı aç", "cihaz"),
    ("Televizyonu kapat", "cihaz"),
])
def test_routes_to_skill(text, skill):
    r, _, _ = make_router()
    routed = r.route(text)
    assert [n for n, _ in routed.results] == [skill], routed
    assert routed.rest == ""


# --- yönlendirme: komut sanılmaması gerekenler ------------------------------------
@pytest.mark.parametrize("text", [
    "Işık hızı nedir?",
    "Hava yolu bileti ne kadar?",
    "Müzik tarihindeki en önemli besteci kim?",
    "Saat kulesini kim yaptırdı?",
    "Bana kısa bir fıkra anlat.",
    "Merhaba, nasılsın?",
    "Hızlı ses işleme modelleri hakkında ne biliyorsun?",
    "Kahve mi çay mı daha sağlıklı?",
    "Kapıyı çalan kimdi acaba",
])
def test_chat_goes_to_llm(text):
    r, _, _ = make_router()
    routed = r.route(text)
    assert routed.results == []
    assert routed.rest == text.strip()


def test_mixed_command_and_chat():
    r, _, _ = make_router()
    routed = r.route("Işıkları aç ve bana kısa bir fıkra anlat.")
    assert [n for n, _ in routed.results] == ["cihaz"]
    assert routed.rest == "bana kısa bir fıkra anlat"


def test_two_commands_in_one_sentence():
    r, _, _ = make_router()
    routed = r.route("Saat kaç, bir de hava nasıl?")
    assert [n for n, _ in routed.results] == ["saat", "hava"]


# --- skill davranışları ----------------------------------------------------------
def test_clock_answers_in_words():
    r, _, _ = make_router()
    assert r.route("Saat kaç?").results[0][1].say == "Saat on dört, beş."
    assert r.route("Bugün günlerden ne?").results[0][1].say == "Bugün on altı Kasım, Pazartesi."


def test_weather_today_and_tomorrow():
    r, _, _ = make_router()
    today = r.route("Hava nasıl?").results[0][1].say
    assert today.startswith("Ankara şu an parçalı bulutlu, on üç derece.")
    assert "şemsiye" not in today
    tomorrow = r.route("Yarın hava nasıl olacak?").results[0][1].say
    assert tomorrow.startswith("Yarın Ankara hafif yağmurlu")
    assert "yüzde yetmiş" in tomorrow and "şemsiye" in tomorrow


def test_weather_without_city_asks():
    r, _, _ = make_router(city="")
    res = r.route("Hava nasıl?").results[0][1]
    assert "Hangi şehrin" in res.say and res.cacheable


def test_media_controls_player_and_volume():
    cmd = FakeCmd(volume=50)
    r, _, _ = make_router(cmd=cmd)
    assert r.route("Müzik çal").results[0][1].say == "Müzik başlıyor."
    assert cmd.calls[-1][-1] == "org.mpris.MediaPlayer2.Player.Play"
    assert cmd.calls[-1][4] == "org.mpris.MediaPlayer2.spotify"
    assert r.route("Sesi aç").results[0][1].say == "Ses yüzde altmış."
    assert r.route("Sesi yüzde 30 yap").results[0][1].say == "Ses yüzde otuz."
    assert cmd.volume == 30


def test_media_without_player():
    r, _, _ = make_router(cmd=FakeCmd(players=()))
    assert r.route("Müziği durdur").results[0][1].say == "Açık bir müzik çalar bulamadım."


def test_timer_announces_with_note_and_cancels():
    r, announced, _ = make_router()
    skill = next(s for s in r.skills if s.name == "zamanlayıcı")
    res = r.route("10 dakika sonra çayı kapatmamı hatırlat").results[0][1]
    assert res.say == "Tamam, on dakika sonra haber vereceğim."
    t = skill.timers[0]
    assert t.secs == 600
    t.fn()
    assert announced == ["Zaman doldu. Çayı kapatmamı."]
    assert r.route("Zamanlayıcıyı iptal et").results[0][1].say == "Zamanlayıcıyı iptal ettim."
    assert not t.alive


def test_devices_not_connected_is_honest():
    r, _, _ = make_router()
    assert r.route("Işıkları aç").results[0][1].say == "Işıklar için henüz bir bağlantım yok."


def test_device_backend_is_called_when_connected():
    calls = []

    class B(DeviceBackend):
        connected = True

        def set(self, device, state):
            calls.append((device, state))

    r = Router([DeviceSkill(B())])
    assert r.route("Klimayı kapat").results[0][1].say == "Tamam."
    assert calls == [("klima", "off")]


def test_skill_error_does_not_crash():
    def broken_http(url):
        raise TimeoutError()

    r = Router([WeatherSkill("Ankara", broken_http)])
    res = r.route("Hava nasıl?").results[0][1]
    assert "sorun" in res.say


# --- kişilik ---------------------------------------------------------------------
def test_persona_prompt(tmp_path):
    p = tmp_path / "k.yaml"
    p.write_text("asistan_adi: TOM\nkullanici:\n  hitap: Yunus\n  hakkinda: ['Kahve severim']\n"
                 "konum:\n  sehir: Ankara\nkisilik: Esprili ol.\nkonusma_kurallari: ['Kısa konuş.']\n",
                 encoding="utf-8")
    s = Persona.load(p).system_prompt(NOW, ["saati söylemek"])
    assert "Senin adın TOM" in s and "Esprili ol." in s and '"Yunus"' in s
    assert "Kahve severim." in s and "16 Kasım 2026, Pazartesi" in s and "Ankara" in s
    assert "saati söylemek" in s and "uydurma" in s and s.endswith("Kısa konuş.")


def test_example_persona_loads():
    p = Persona.load()
    assert p.asistan_adi == "TOM" and p.konusma_kurallari
