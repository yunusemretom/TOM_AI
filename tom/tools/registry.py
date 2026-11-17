"""TOM'un varsayılan araç kutusu (modelin gördüğü açıklamalar Türkçe ve kısa: bağlam küçük)."""

from __future__ import annotations

from tom.tools import info, pc, web
from tom.tools.base import Tool, Toolbox
from tom.tools.memory import Memory

S = {"type": "string"}
I = {"type": "integer"}
N = {"type": "number"}


def default_toolbox(memory: Memory) -> Toolbox:
    return Toolbox([
        Tool("web_ara", "İnternette arar; en iyi sayfaların metnini döner. Güncel olaylar, haberler, maç sonuçları, "
             "fiyatlar, kişiler, bilmediğin ya da emin olmadığın her şey için kullan.",
             {"sorgu": {**S, "description": "Arama sorgusu (Türkçe ya da İngilizce)"}}, ["sorgu"], web.web_ara),
        Tool("web_oku", "Bir web sayfasının metnini okur (kullanıcı adres verirse ya da aramadaki bir sayfanın "
             "ayrıntısı gerekirse).", {"adres": {**S, "description": "URL"}}, ["adres"], web.web_oku),
        Tool("haberler", "Son haber başlıklarını getirir.",
             {"konu": {**S, "description": "Konu; boş bırakılırsa Türkiye gündemi"}}, [], web.haberler),
        Tool("hesapla", "Matematik hesabı yapar (+ - * / ** % sqrt…).",
             {"ifade": {**S, "description": "Ör. (125*18)/3 ya da sqrt(2)"}}, ["ifade"], info.hesapla),
        Tool("doviz", "Güncel döviz kuru ve çevirme.",
             {"kaynak": {**S, "description": "Ör. USD, EUR, dolar"}, "hedef": {**S, "description": "Ör. TRY"},
              "miktar": {**N, "description": "Varsayılan 1"}}, ["kaynak", "hedef"], info.doviz),
        Tool("hava_tahmini", "Bir şehrin şu anki havası ve önümüzdeki günlerin tahmini.",
             {"sehir": S, "gun": {**I, "description": "Kaç gün (1-7)"}}, ["sehir"], info.hava_tahmini),
        Tool("hatirlatici_kur", "Belirli bir tarih ve saatte sesli hatırlatma kurar (alarm). Şu anki tarih ve "
             "saati sistem mesajından al; 'yarın 7'de' gibi ifadeleri kesin zamana çevir.",
             {"zaman": {**S, "description": "YYYY-MM-DD HH:MM"}, "mesaj": S}, ["zaman", "mesaj"],
             memory.hatirlatici_kur),
        Tool("hatirlaticilari_listele", "Kurulu hatırlatıcıları listeler.", {}, [], memory.hatirlaticilar),
        Tool("hatirlatici_sil", "Hatırlatıcı siler.", {"ifade": {**S, "description": "Mesajdan bir parça ya da saat"}},
             ["ifade"], memory.hatirlatici_sil),
        Tool("not_al", "Kullanıcının söylediği notu kaydeder.", {"metin": S}, ["metin"], memory.not_al),
        Tool("notlari_oku", "Kayıtlı son notları okur.", {"son": {**I, "description": "Kaç not (varsayılan 5)"}},
             [], memory.notlari_oku),
        Tool("hatirla", "Kullanıcı hakkında kalıcı bir bilgiyi hafızaya yazar (ör. 'doğum günüm 3 Mart', "
             "'kahveyi sütsüz içerim'). Kullanıcı 'bunu hatırla' derse ya da önemli kişisel bilgi verirse kullan.",
             {"bilgi": {**S, "description": "Üçüncü şahısla kısa cümle: 'Doğum günü 3 Mart.'"}}, ["bilgi"],
             memory.hatirla),
        Tool("unut", "Hafızadaki bir bilgiyi siler.", {"ifade": S}, ["ifade"], memory.unut),
        Tool("uygulama_ac", "Bilgisayarda kurulu bir masaüstü uygulamasını açar (Dosyalar, Terminal, Spotify, "
             "Hesap Makinesi…). YouTube, Gmail, Netflix gibi web siteleri için site_ac kullan.",
             {"ad": {**S, "description": "Uygulamanın adı"}}, ["ad"], pc.uygulama_ac),
        Tool("site_ac", "Tarayıcıda bir web sitesi ya da arama sayfası açar (YouTube, Google, Gmail, Netflix…).",
             {"adres": {**S, "description": "Ör. youtube, youtube.com ya da arama metni"},
              "tarayici": {**S, "description": "İsteğe bağlı: chrome ya da firefox; söylenmezse varsayılan tarayıcı"}},
             ["adres"], pc.site_ac),
        Tool("youtube_ara", "YouTube'da video arar; oynat=true ise ilk videoyu doğrudan açar ('şu şarkıyı aç/oynat').",
             {"sorgu": {**S, "description": "Aranacak video, şarkı ya da kanal"},
              "oynat": {"type": "boolean", "description": "true: ilk videoyu aç; false: arama sonuçlarını göster"},
              "tarayici": {**S, "description": "İsteğe bağlı: chrome ya da firefox"}}, ["sorgu"], pc.youtube_ara),
        Tool("ses_ayarla", "Bilgisayarın ses seviyesini yüzdeye ayarlar.",
             {"yuzde": {**I, "description": "0-100 (gerekirse 150'ye kadar)"}}, ["yuzde"], pc.ses_ayarla),
        Tool("parlaklik_ayarla", "Ekran parlaklığını yüzdeye ayarlar.",
             {"yuzde": {**I, "description": "5-100"}}, ["yuzde"], pc.parlaklik_ayarla),
        Tool("sistem_durumu", "Bilgisayarın işlemci, RAM, disk, pil ve GPU durumunu söyler.", {}, [],
             pc.sistem_durumu),
    ])
