"""Faz 6 testleri: bildirim zamanlamasi, metni ve uc yetkilendirmesi.

En kritik iki degismez:

1. **Kullanici basina LLM cagrisi YOK.** Bildirim metni burc basina uretilir
   ve onbellege alinir. Bu kural bozulursa maliyet kullanici sayisiyla
   dogrusal buyur ve urunun birim ekonomisi coker.
2. **Gece bildirim gitmez.** Sessiz saat, tercih ve tekrar korumasi birlikte
   calisir; herhangi biri kacarsa kullanici uygulamayi siler.

Calistirma:  .venv\\Scripts\\python.exe -m pytest tests/test_notifications.py -q
"""
from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

from core import cache, config
from services import notification_service as ns

try:
    from main import app
    _APP_IMPORT_ERROR = None
except Exception as exc:  # pragma: no cover
    app = None
    _APP_IMPORT_ERROR = str(exc)

uygulama_gerekir = pytest.mark.skipif(
    _APP_IMPORT_ERROR is not None,
    reason=f"FastAPI uygulamasi ice aktarilamadi: {_APP_IMPORT_ERROR}",
)


@pytest.fixture(autouse=True)
def temiz_onbellek(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(config, "CACHE_BACKEND", "file")
    cache._memory.clear()
    yield
    cache._memory.clear()


def profil(**alanlar):
    """Bildirim almaya uygun asgari profil."""
    temel = {
        "uid": "u1",
        "fcmToken": "token-1",
        "onboardingCompleted": True,
        "timezone": "Europe/Istanbul",
        "language": "tr",
        "sunSign": "Aslan ♌",
        "streakCount": 5,
    }
    temel.update(alanlar)
    return temel


def utc(saat: int, dakika: int = 0, gun: int = 15) -> dt.datetime:
    return dt.datetime(2026, 6, gun, saat, dakika, tzinfo=dt.timezone.utc)


# --------------------------------------------------------------------------
# Yerel saat
# --------------------------------------------------------------------------

def test_yerel_saat_dilime_gore():
    istanbul = profil(timezone="Europe/Istanbul")
    newyork = profil(timezone="America/New_York")

    an = utc(6)  # 06:00 UTC
    assert ns.local_now(istanbul, an).hour == 9   # UTC+3
    assert ns.local_now(newyork, an).hour == 2    # UTC-4 (yaz saati)


def test_taninmayan_saat_dilimi_varsayilana_duser():
    """Tek bozuk profil tum toplu gonderimi dusurmemeli."""
    assert ns.user_timezone(profil(timezone="Mars/Olympus")) == \
        ZoneInfo(ns.DEFAULT_TIMEZONE)
    assert ns.user_timezone(profil(timezone="")) == \
        ZoneInfo(ns.DEFAULT_TIMEZONE)
    assert ns.user_timezone({}) == ZoneInfo(ns.DEFAULT_TIMEZONE)


def test_ayni_anda_farkli_dilimlerden_yalnizca_sirasi_gelen():
    """Tek bir zamanlayici isi tum saat dilimlerini karsilamali."""
    an = utc(6)  # Istanbul 09:00, Londra 07:00
    istanbul = profil(uid="tr", timezone="Europe/Istanbul")
    londra = profil(uid="uk", timezone="Europe/London")

    assert ns.local_now(istanbul, an).hour == ns.TARGET_HOURS["daily"]
    assert ns.local_now(londra, an).hour != ns.TARGET_HOURS["daily"]


# --------------------------------------------------------------------------
# Sessiz saat
# --------------------------------------------------------------------------

@pytest.mark.parametrize("saat,beklenen", [
    (23, True), (0, True), (3, True), (7, True),   # 22:00-08:00 arasi
    (8, False), (12, False), (21, False),
])
def test_varsayilan_sessiz_saat_gece_yarisini_asar(saat, beklenen):
    yerel = dt.datetime(2026, 6, 15, saat, tzinfo=ZoneInfo("Europe/Istanbul"))
    assert ns.in_quiet_hours(profil(), yerel) is beklenen


def test_gunduz_sessiz_araligi():
    p = profil(quietFrom=13, quietTo=15)
    tz = ZoneInfo("Europe/Istanbul")
    assert ns.in_quiet_hours(p, dt.datetime(2026, 6, 15, 14, tzinfo=tz))
    assert not ns.in_quiet_hours(p, dt.datetime(2026, 6, 15, 16, tzinfo=tz))
    assert not ns.in_quiet_hours(p, dt.datetime(2026, 6, 15, 2, tzinfo=tz))


def test_esit_sinirlar_sessiz_saati_kapatir():
    """from == to "24 saat sessiz" sayilsaydi kullanici hic bildirim almazdi
    ve bunu fark etmesi imkansiz olurdu."""
    p = profil(quietFrom=9, quietTo=9)
    tz = ZoneInfo("Europe/Istanbul")
    for saat in (0, 9, 15, 23):
        assert not ns.in_quiet_hours(p, dt.datetime(2026, 6, 15, saat, tzinfo=tz))


def test_bozuk_sessiz_saat_degeri_varsayilana_duser():
    for bozuk in ("abc", None, -1, 99, 24):
        p = profil(quietFrom=bozuk, quietTo=bozuk)
        yerel = dt.datetime(2026, 6, 15, 3, tzinfo=ZoneInfo("Europe/Istanbul"))
        assert ns.in_quiet_hours(p, yerel), f"bozuk deger: {bozuk}"


# --------------------------------------------------------------------------
# Gonderim karari
# --------------------------------------------------------------------------

@pytest.fixture
def gonderilmemis(monkeypatch):
    monkeypatch.setattr(ns, "already_sent", lambda uid, tur, gun: False)
    monkeypatch.setattr(ns, "mark_sent", lambda uid, tur, gun: None)


def test_hedef_saatte_gonderilir(gonderilmemis):
    gonder, gerekce = ns.should_send(profil(), "daily", utc(6))
    assert gonder, gerekce


@pytest.mark.parametrize("degisiklik,beklenen_gerekce", [
    ({"fcmToken": None}, "token-yok"),
    ({"onboardingCompleted": False}, "onboarding-tamamlanmamis"),
    ({"notifyDaily": False}, "tercih-kapali"),
])
def test_gonderilmeme_gerekceleri(gonderilmemis, degisiklik, beklenen_gerekce):
    gonder, gerekce = ns.should_send(profil(**degisiklik), "daily", utc(6))
    assert not gonder
    assert gerekce == beklenen_gerekce


def test_saat_uymuyorsa_gonderilmez(gonderilmemis):
    gonder, gerekce = ns.should_send(profil(), "daily", utc(12))
    assert not gonder
    assert gerekce == "saat-uygun-degil"


def test_tercih_alani_yoksa_acik_sayilir(gonderilmemis):
    """Mevcut kullanicilarin profilinde bu alan yok; varsayilan kapali
    olsaydi hicbiri bildirim almazdi."""
    p = profil()
    p.pop("notifyDaily", None)
    assert ns.wants(p, "daily")
    gonder, _ = ns.should_send(p, "daily", utc(6))
    assert gonder


def test_hedef_saat_sessiz_araliktaysa_kullanici_kazanir(gonderilmemis):
    p = profil(quietFrom=8, quietTo=10)  # 09:00 sessiz araliga dusuyor
    gonder, gerekce = ns.should_send(p, "daily", utc(6))
    assert not gonder
    assert gerekce == "sessiz-saat"


def test_ayni_gun_ikinci_kez_gonderilmez(monkeypatch):
    """Zamanlayici yeniden deneyebilir; ayni bildirim iki kez gitmemeli."""
    monkeypatch.setattr(ns, "already_sent", lambda uid, tur, gun: True)
    gonder, gerekce = ns.should_send(profil(), "daily", utc(6))
    assert not gonder
    assert gerekce == "zaten-gonderildi"


def test_firestore_yoksa_tekrar_korumasi_gondermemeye_duser(monkeypatch):
    """Kaydi okuyamiyorsak guvenli taraf GONDERMEMEKTIR: ayni bildirimi iki
    kez atmak, hic atmamaktan kotudur."""
    monkeypatch.setattr(ns.firestore_client, "get_client", lambda: None)
    assert ns.already_sent("u1", "daily", "2026-06-15") is True


# --- Seri hatirlatmasi ---

def test_seri_bugun_okunduysa_hatirlatilmaz(gonderilmemis):
    yerel_gun = ns.local_now(profil(), utc(17)).date().isoformat()
    p = profil(lastSeenDaily=yerel_gun)
    gonder, gerekce = ns.should_send(p, "streak", utc(17))  # 20:00 yerel
    assert not gonder
    assert gerekce == "bugun-zaten-okudu"


def test_kisa_seri_hatirlatilmaz(gonderilmemis):
    """Tek gunluk seri icin bildirim gondermek rahatsiz edici; kaybedilecek
    bir sey yok."""
    gonder, gerekce = ns.should_send(profil(streakCount=1), "streak", utc(17))
    assert not gonder
    assert gerekce == "seri-kisa"


def test_seri_hatirlatmasi_aksam_gonderilir(gonderilmemis):
    gonder, gerekce = ns.should_send(profil(streakCount=4), "streak", utc(17))
    assert gonder, gerekce


# --- Aksam check-in sorusu (KA4) ---

def test_checkin_aksam_saatinde(gonderilmemis):
    """Hedef saat 20:00 yerel; sabah saatinde gitmez."""
    assert ns.TARGET_HOURS["checkin"] == 20
    gonder, gerekce = ns.should_send(profil(), "checkin", utc(17))
    assert gonder, gerekce
    gonder, gerekce = ns.should_send(profil(), "checkin", utc(6))
    assert not gonder and gerekce == "saat-uygun-degil"


def test_checkin_streak_tercihini_paylasir(gonderilmemis):
    """Ayri bir `notifyCheckin` alani BILEREK yok: ikisi de "aksam
    durtmesi" ailesi ve aksam en fazla biri gidiyor. Streak'i kapatan
    kullanici check-in de almaz."""
    assert ns.PREF_FIELDS["checkin"] == "notifyStreak"
    gonder, gerekce = ns.should_send(
        profil(notifyStreak=False), "checkin", utc(17))
    assert not gonder and gerekce == "tercih-kapali"


def test_aksam_en_fazla_bir_bildirim(monkeypatch):
    """Karsilikli bastirma iki yonde de tutar: check-in gittiyse streak
    susar, streak gittiyse check-in gitmez — is sirasi/yeniden deneme
    fark etmez."""
    monkeypatch.setattr(ns, "mark_sent", lambda uid, tur, gun: None)

    def checkin_gitti(uid, tur, gun):
        return tur == "checkin"

    monkeypatch.setattr(ns, "already_sent", checkin_gitti)
    gonder, gerekce = ns.should_send(profil(streakCount=4), "streak", utc(17))
    assert not gonder and gerekce == "aksam-checkin-gitti"

    def streak_gitti(uid, tur, gun):
        return tur == "streak"

    monkeypatch.setattr(ns, "already_sent", streak_gitti)
    gonder, gerekce = ns.should_send(profil(), "checkin", utc(17))
    assert not gonder and gerekce == "aksam-streak-gitti"


def test_checkin_gunun_okunmasina_bakmaz(gonderilmemis):
    """`lastSeenDaily` yalniz streak'i susturur: gunun okumasini acmis
    kullaniciya da aksam sorusu gider — soru okumanin degil GUNUN
    kendisinin takibi."""
    yerel_gun = ns.local_now(profil(), utc(17)).date().isoformat()
    gonder, gerekce = ns.should_send(
        profil(lastSeenDaily=yerel_gun), "checkin", utc(17))
    assert gonder, gerekce


# --- Ogle olculu slotu (OB3) ---

def _midday_ham(gunler: int, tarih: str = "2026-06-15"):
    """days_to_exact degistirilebilir sahte sinyal kumesi."""
    return {
        "generated_for": tarih,
        "signals": [
            {"transit": "Jupiter", "natal": "Sun", "aspect": "Trine",
             "orb": 2.1, "theme": "career", "active": True,
             "movement": "applying"},
            {"transit": "Saturn", "natal": "Moon", "aspect": "Square",
             "orb": 0.3, "theme": "inner", "active": True,
             "exact_on": tarih, "days_to_exact": gunler},
        ],
    }


def test_midday_ogle_saatinde(gonderilmemis):
    """Hedef saat 13:00 yerel; tercih `notifyDaily` ailesinden (ayni
    commit kurali: PREF_FIELDS'ta olmayan tur SESSIZCE gitmez)."""
    assert ns.TARGET_HOURS["midday"] == 13
    assert ns.PREF_FIELDS["midday"] == "notifyDaily"
    gonder, gerekce = ns.should_send(profil(), "midday", utc(10))
    assert gonder, gerekce
    gonder, gerekce = ns.should_send(profil(), "midday", utc(6))
    assert not gonder and gerekce == "saat-uygun-degil"
    gonder, gerekce = ns.should_send(
        profil(notifyDaily=False), "midday", utc(10))
    assert not gonder and gerekce == "tercih-kapali"


def test_midday_bugun_kesinlesen_kendi_haritasindan(monkeypatch):
    """(a) dali: bugun kesinlesen sinyal varsa gövde paketteki INDEKS
    HIZALI cümle, yuk birebir sabahki daily deseni + src=midday — mobilde
    sifir yeni tuketici. Tum FCM degerleri dize olmali."""
    from services import signal_service

    ham = _midday_ham(gunler=0)
    monkeypatch.setattr(signal_service, "cached_signals",
                        lambda p, today=None: ham)
    monkeypatch.setattr(
        signal_service, "cached_insight_bundle",
        lambda h, lang, generate_if_missing=True: {
            "insights": ["Kariyer cümlesi.", "Bugün iç dünyanda kapanış var."],
            "checkin_question": None,
        })

    sonuc, gerekce = ns.midday_push(profil(), "tr",
                                    today=dt.date(2026, 6, 15))
    assert sonuc is not None and gerekce == "gonderilecek"
    baslik, govde, veri = sonuc
    assert govde == "Bugün iç dünyanda kapanış var."      # idx 1, hizali
    assert "🌙" in baslik                                  # inner temasi
    assert veri["type"] == "daily" and veri["route"] == "signal"
    assert veri["idx"] == "1" and veri["src"] == "midday"
    assert veri["d"] == "2026-06-15"
    assert all(isinstance(v, str) for v in veri.values())


def test_midday_paketi_yalniz_okur(monkeypatch):
    """Ogle LLM YAKMAZ: paket yoksa uretim cagrilmaz, dürüst teknik satira
    düşülür (o da ölçülmüş veridir)."""
    from services import signal_service

    ham = _midday_ham(gunler=0)
    monkeypatch.setattr(signal_service, "cached_signals",
                        lambda p, today=None: ham)

    def uretim_yasak(*a, **k):
        raise AssertionError("ogle yolu insight_bundle CAGIRMAMALI")

    monkeypatch.setattr(signal_service, "insight_bundle", uretim_yasak)
    monkeypatch.setattr(ns.gemini_service, "generate", uretim_yasak)

    sonuc, _gerekce = ns.midday_push(profil(), "tr",
                                     today=dt.date(2026, 6, 15))
    assert sonuc is not None
    _, govde, veri = sonuc
    assert govde and veri["src"] == "midday"   # teknik satir dolu


def test_midday_olay_yoksa_none(monkeypatch):
    """Kesinlesen yok + cift onbellegi bos → None; cagiran 'olay-yok' ile
    atlar. Ogle bildirimi bir hak degil, olayin haberi."""
    from services import circle_context, people_service, signal_service

    monkeypatch.setattr(signal_service, "cached_signals",
                        lambda p, today=None: _midday_ham(gunler=3))
    monkeypatch.setattr(circle_context, "list_accepted_friend_uids",
                        lambda uid, limit=5: [])
    monkeypatch.setattr(people_service, "list_people", lambda uid: [])

    assert ns.midday_push(profil(), "tr",
                          today=dt.date(2026, 6, 15)) == (None, "olay-yok")


def test_midday_cift_ani_yalniz_onbellekten(monkeypatch):
    """(b) dali ASLA hesaplamaz: get_transits patlasa bile onbellekli
    vurus push uretir. Yuk type=friend → Çevrem sekmesi."""
    from services import (astro_service, circle_context, people_service,
                          signal_service, synastry_service)

    monkeypatch.setattr(signal_service, "cached_signals",
                        lambda p, today=None: None)
    monkeypatch.setattr(circle_context, "list_accepted_friend_uids",
                        lambda uid, limit=5: ["f1"])
    monkeypatch.setattr(people_service, "list_people", lambda uid: [])

    cp = synastry_service.Counterpart(
        key="u1-f1", birth={}, label="Erkan", sun_sign="leo")
    monkeypatch.setattr(synastry_service, "friend_counterpart",
                        lambda uid, fuid: cp)
    monkeypatch.setattr(
        synastry_service, "pair_transits_cached",
        lambda uid, other, today=None: {
            "date": "2026-06-15",
            "hits": [{"side": "user", "transit": "Saturn", "natal": "Venus",
                      "aspect": "Trine", "orb": 0.8,
                      "movement": "applying"}],
        })

    def hesap_yasak(*a, **k):
        raise AssertionError("ogle yolu efemeris HESAPLAMAMALI")

    monkeypatch.setattr(astro_service, "get_transits", hesap_yasak)

    sonuc, gerekce = ns.midday_push(profil(), "tr",
                                    today=dt.date(2026, 6, 15))
    assert sonuc is not None and gerekce == "gonderilecek"
    baslik, govde, veri = sonuc
    assert "Erkan" in baslik
    assert govde
    assert veri["type"] == "friend" and veri["src"] == "midday"
    # BY-turu: hedef kimliği taşınır — dokununca O ilişkinin ekranı
    # açılır; kimliksiz yük istemciyi yalnız sekmeye bırakıyordu.
    assert veri["fromUid"] == "f1"
    assert all(isinstance(v, str) for v in veri.values())


# --- OT-turu: tekrar korumasi + tema rotasyonu ---

def test_midday_sabahin_kopyasini_gondermez(monkeypatch):
    """CANLI ACIK (OT1.2): bugun kesinlesen sinyal cogunlukla sabahin
    odagiydi ve 13:00 govdesi 09:00'unkiyle BAYT-AYNI cikiyordu. Artik:
    ayni paketten FARKLI sinyal denenir; hepsi kopyaysa 'sabahla-ayni'
    ile atlanir. Degismez: sabah govdesi == ogle govdesi ASLA."""
    from services import signal_service

    ham = _midday_ham(gunler=0)
    sabah_govde = "Bugün iç dünyanda kapanış var."
    monkeypatch.setattr(signal_service, "cached_signals",
                        lambda p, today=None: ham)
    monkeypatch.setattr(
        signal_service, "cached_insight_bundle",
        lambda h, lang, generate_if_missing=True: {
            "insights": ["Kariyer cümlesi.", sabah_govde],
            "checkin_question": None,
        })
    monkeypatch.setattr(
        ns, "last_daily_sent",
        lambda uid: {"day": "2026-06-15", "body": sabah_govde,
                     "bodyHash": ns._body_hash(sabah_govde),
                     "focusFp": "Saturn-Square-Moon", "focusIdx": 1,
                     "theme": "inner"})

    sonuc, gerekce = ns.midday_push(profil(), "tr",
                                    today=dt.date(2026, 6, 15))
    assert sonuc is not None and gerekce == "gonderilecek"
    _, govde, veri = sonuc
    assert govde != sabah_govde            # degismez: kopya yasak
    assert govde == "Kariyer cümlesi."     # ayni paketten farkli sinyal
    assert veri["idx"] == "0"


def test_midday_tum_adaylar_kopyaysa_atlanir(monkeypatch):
    """Tek sinyalli haritada gövde sabahınkiyse öğle 'sabahla-ayni' ile
    susar (çift önbelleği de boşsa) — kopya hiçbir koşulda gitmez."""
    from services import circle_context, people_service, signal_service

    ham = {"generated_for": "2026-06-15", "signals": [
        {"transit": "Saturn", "natal": "Moon", "aspect": "Square",
         "orb": 0.3, "theme": "inner", "active": True,
         "exact_on": "2026-06-15", "days_to_exact": 0}]}
    sabah_govde = "Bugün iç dünyanda kapanış var."
    monkeypatch.setattr(signal_service, "cached_signals",
                        lambda p, today=None: ham)
    monkeypatch.setattr(
        signal_service, "cached_insight_bundle",
        lambda h, lang, generate_if_missing=True: {
            "insights": [sabah_govde], "checkin_question": None})
    monkeypatch.setattr(
        ns, "last_daily_sent",
        lambda uid: {"day": "2026-06-15", "body": sabah_govde,
                     "bodyHash": ns._body_hash(sabah_govde),
                     "focusFp": "Saturn-Square-Moon", "focusIdx": 0,
                     "theme": "inner"})
    monkeypatch.setattr(circle_context, "list_accepted_friend_uids",
                        lambda uid, limit=5: [])
    monkeypatch.setattr(people_service, "list_people", lambda uid: [])

    assert ns.midday_push(profil(), "tr", today=dt.date(2026, 6, 15)) == \
        (None, "sabahla-ayni")


def test_daily_focus_index_rotasyon():
    """OT1.3 tema çarkı (kullanıcı kararı: 'bir gün ilişki, bir gün mali,
    bir gün iç dünya'): dünkü temadan SONRAKİ temaya geçilir; bugün
    kesinleşen olay rotasyonu döver; dünkü sinyalin kendisi ancak başka
    aday yoksa seçilir."""
    from services import signal_service as ss

    ham = {"signals": [
        {"transit": "Jupiter", "natal": "Sun", "aspect": "Trine",
         "theme": "career"},
        {"transit": "Saturn", "natal": "Venus", "aspect": "Square",
         "theme": "relationships"},
        {"transit": "Pluto", "natal": "Moon", "aspect": "Sextile",
         "theme": "inner"},
    ]}
    # Dün ilişkiler gittiyse çark finance arar, yoksa inner'a düşer.
    assert ss.daily_focus_index(ham, prev_theme="relationships") == 2
    # Dün inner gittiyse sıradaki career.
    assert ss.daily_focus_index(ham, prev_theme="inner") == 0
    # Hafıza yoksa çark başından (relationships mevcut → idx 1).
    assert ss.daily_focus_index(ham) == 1
    # Bugün kesinleşen olay her şeyi döver.
    olayli = {"signals": [
        {"transit": "Jupiter", "natal": "Sun", "aspect": "Trine",
         "theme": "career"},
        {"transit": "Saturn", "natal": "Moon", "aspect": "Square",
         "theme": "inner", "exact_on": "2026-06-15", "days_to_exact": 0},
    ]}
    assert ss.daily_focus_index(olayli, prev_theme="inner") == 1
    # Dünkü sinyalin TA KENDİSİ ancak tek adaysa seçilir.
    tek = {"signals": [{"transit": "Pluto", "natal": "Moon",
                        "aspect": "Sextile", "theme": "inner"}]}
    assert ss.daily_focus_index(tek, prev_theme="career",
                                prev_fp="Pluto-Sextile-Moon") == 0


def test_signal_push_dunla_ayni_govdeyi_yeniden_uretir(monkeypatch):
    """OT1.3 sınırlı tekrar koruması: gövde dünkü gövdeyle aynıysa TEK
    yeniden üretim (dünkü cümle negatif örnek) yapılır; o da tutmazsa
    gün-farkındalıklı teknik satıra düşülür. Asla dünkü metnin kopyası
    dönmez ve en fazla 1 ek LLM çağrısı yapılır."""
    from services import signal_service

    ham = {"generated_for": "2026-06-15", "signals": [
        {"transit": "Saturn", "natal": "Moon", "aspect": "Square",
         "orb": 0.3, "theme": "inner", "active": True,
         "exact_on": "2026-06-18", "days_to_exact": 3,
         "movement": "applying"}]}
    dunku = "Aynı cümle."
    monkeypatch.setattr(signal_service, "cached_signals",
                        lambda p, today=None: ham)
    monkeypatch.setattr(
        signal_service, "cached_insight_bundle",
        lambda h, lang, generate_if_missing=True: {
            "insights": [dunku], "checkin_question": None})

    cagrilar: list = []

    def sahte_uretim(h, lang, avoid=None):
        cagrilar.append(avoid)
        return {"insights": ["Yepyeni bir açı."], "checkin_question": None}

    monkeypatch.setattr(signal_service, "insight_bundle", sahte_uretim)

    onceki = {"day": "2026-06-14", "body": dunku,
              "bodyHash": ns._body_hash(dunku),
              "focusFp": "Saturn-Square-Moon", "focusIdx": 0,
              "theme": "inner"}
    sonuc = ns.signal_push(profil(), "tr", today=dt.date(2026, 6, 15),
                           onceki=onceki)
    assert sonuc is not None
    _, govde, _iz, _idx, _extra = sonuc
    assert govde == "Yepyeni bir açı."
    assert cagrilar == [dunku]  # tam 1 yeniden üretim, negatif örnekle

    # Yeniden üretim de aynı çıkarsa: teknik satıra düşülür (o satır
    # geri sayımlı olduğu için dünle aynı olamaz).
    cagrilar.clear()
    monkeypatch.setattr(
        signal_service, "insight_bundle",
        lambda h, lang, avoid=None: {"insights": [dunku],
                                     "checkin_question": None})
    sonuc = ns.signal_push(profil(), "tr", today=dt.date(2026, 6, 15),
                           onceki=onceki)
    assert sonuc is not None
    _, govde, _iz, _idx, _extra = sonuc
    assert "3 gün sonra" in govde  # gün-farkındalıklı teknik satır


def test_teknik_satir_geri_sayimli():
    """OT1.4: sabit tarihli satır iki kötü sabahda bayt-aynı bildirim
    üretiyordu; geri sayım ({days}) her gün azalır."""
    from services import prompts as p

    veri = {"signals": [
        {"transit": "Saturn", "natal": "Moon", "aspect": "square",
         "orb": 0.3, "theme": "inner", "exact_on": "2026-06-18",
         "days_to_exact": 3}]}
    uc_gun = p.localize_signals("tr", veri)["signals"][0]["technical"]
    veri["signals"][0]["days_to_exact"] = 2
    iki_gun = p.localize_signals("tr", veri)["signals"][0]["technical"]
    assert "3 gün sonra" in uc_gun and "2 gün sonra" in iki_gun
    assert uc_gun != iki_gun


@uygulama_gerekir
def test_gecici_fcm_hatasi_gunu_yakmaz(monkeypatch):
    """OT1.5: eskiden yalnız ölü token'lar işaretlenmiyordu — geçici FCM
    hatası alan kullanıcı 'gönderildi' sayılıp o günü kaybediyordu.
    Artık failed_uids'teki hiçbir kullanıcı işaretlenmez."""
    from api import notify
    from services import push_service

    monkeypatch.setattr(config, "NOTIFY_SCHEDULER_SECRET", "dogru")
    monkeypatch.setattr(notify, "_iter_profiles", lambda: iter([
        profil(uid="tamam", quietFrom=0, quietTo=0),
        profil(uid="gecici-hata", fcmToken="token-2",
               quietFrom=0, quietTo=0),
    ]))
    monkeypatch.setattr(notify, "get_sky_now", lambda: SAHTE_GOKYUZU)
    monkeypatch.setattr(ns, "already_sent", lambda uid, tur, gun: False)
    monkeypatch.setattr(ns, "last_daily_sent", lambda uid: None)
    monkeypatch.setattr(
        ns, "signal_push",
        lambda p, lang, today=None, onceki=None: (
            "Başlık", "Gövde.", "iz", 0, {}))

    isaretlenen: list = []
    monkeypatch.setattr(
        ns, "mark_sent",
        lambda uid, tur, gun, extra=None: isaretlenen.append(uid))

    def sahte_gonder(mesajlar):
        return push_service.SendResult(
            sent=1, failed=1, pruned=[], failed_uids=["gecici-hata"])

    monkeypatch.setattr(push_service, "send", sahte_gonder)
    with TestClient(app) as client:
        client.post("/api/v1/notify/run?type=daily&force=true",
                    headers={"Authorization": "dogru"})
    assert isaretlenen == ["tamam"]


# --- Olay tabanli (arkadas tepkisi) ---

def test_arkadas_tepkisi_sessiz_saatte_dusurulur():
    an = utc(0)  # Istanbul 03:00
    gonder, gerekce = ns.can_send_event(profil(), "friend", an)
    assert not gonder
    assert gerekce == "sessiz-saat"


def test_arkadas_tepkisi_gunduz_gonderilir():
    gonder, _ = ns.can_send_event(profil(), "friend", utc(12))
    assert gonder


def test_arkadas_tepkisi_tercihe_saygi_gosterir():
    gonder, gerekce = ns.can_send_event(
        profil(notifyFriends=False), "friend", utc(12))
    assert not gonder
    assert gerekce == "tercih-kapali"


# --------------------------------------------------------------------------
# Bildirim metni — birim ekonomi
# --------------------------------------------------------------------------

SAHTE_GOKYUZU = {
    "moon_phase": {"key": "full_moon", "name": "Dolunay", "illumination": 98},
    "retrogrades": ["Satürn"],
}


def test_gunluk_metin_burc_basina_bir_kez_uretilir(monkeypatch):
    """Kullanici basina LLM cagrisi olsaydi maliyet kullanici sayisiyla
    dogrusal buyurdu ve urun batardi."""
    cagrilar: list[str] = []

    def sahte_generate(prompt, **k):
        cagrilar.append(k.get("lang") or "?")
        return "Bugun gokyuzu sana bir kapi araliyor."

    monkeypatch.setattr(ns.gemini_service, "generate", sahte_generate)

    # Ayni burc ve dil icin 50 kullanici
    for _ in range(50):
        ns.daily_push_body("leo", SAHTE_GOKYUZU, "tr", "2026-06-15")

    assert len(cagrilar) == 1, f"burc basina 1 cagri bekleniyordu: {cagrilar}"


def test_gunluk_metin_dile_gore_ayrisir(monkeypatch):
    uretilen: list[str] = []
    monkeypatch.setattr(
        ns.gemini_service, "generate",
        lambda prompt, **k: uretilen.append(k.get("lang")) or f"line {k.get('lang')}")

    tr = ns.daily_push_body("leo", SAHTE_GOKYUZU, "tr", "2026-06-15")
    en = ns.daily_push_body("leo", SAHTE_GOKYUZU, "en", "2026-06-15")

    assert tr != en
    assert uretilen == ["tr", "en"]


def test_gunluk_metin_gune_gore_ayrisir(monkeypatch):
    sayac = []
    monkeypatch.setattr(ns.gemini_service, "generate",
                        lambda prompt, **k: sayac.append(1) or "metin")
    ns.daily_push_body("leo", SAHTE_GOKYUZU, "tr", "2026-06-15")
    ns.daily_push_body("leo", SAHTE_GOKYUZU, "tr", "2026-06-16")
    assert len(sayac) == 2, "yeni gun yeni metin uretmeli"


def test_cok_uzun_metin_yedege_duser(monkeypatch):
    """Bildirim golgesi uzun metni kesiyor; yarim cumle guvensizlik veriyor."""
    monkeypatch.setattr(ns.gemini_service, "generate",
                        lambda prompt, **k: "x" * 400)
    metin = ns.daily_push_body("leo", SAHTE_GOKYUZU, "tr", "2026-06-15")
    assert len(metin) <= ns.MAX_PUSH_BODY
    assert "Aslan" in metin


def test_llm_bosken_yedek_metin_de_onbelleklenir(monkeypatch):
    """Gemini'nin sorunlu oldugu bir saatte her burc icin tekrar tekrar
    denenmemeli."""
    cagrilar = []
    monkeypatch.setattr(ns.gemini_service, "generate",
                        lambda prompt, **k: cagrilar.append(1) or None)
    ns.daily_push_body("leo", SAHTE_GOKYUZU, "tr", "2026-06-15")
    ns.daily_push_body("leo", SAHTE_GOKYUZU, "tr", "2026-06-15")
    assert len(cagrilar) == 1


def test_tirnak_temizlenir(monkeypatch):
    monkeypatch.setattr(ns.gemini_service, "generate",
                        lambda prompt, **k: '"Bugun sabir gunu."')
    metin = ns.daily_push_body("leo", SAHTE_GOKYUZU, "tr", "2026-06-15")
    assert not metin.startswith('"')


def test_seri_ve_arkadas_metinleri_llm_cagirmaz(monkeypatch):
    def patla(*a, **k):
        raise AssertionError("Sablon bildirimde LLM cagrilmamali")

    monkeypatch.setattr(ns.gemini_service, "generate", patla)

    baslik, govde = ns.streak_push(profil(streakCount=7), "tr")
    assert "7" in baslik and govde

    baslik, govde = ns.friend_push("Ada", "🔥", "Seriyi surdur", "en")
    assert "Ada" in baslik and "🔥" in govde


def test_metinler_dile_gore():
    tr_baslik, _ = ns.streak_push(profil(streakCount=3), "tr")
    en_baslik, _ = ns.streak_push(profil(streakCount=3), "en")
    assert tr_baslik != en_baslik


def test_profil_dili_dogrulanir():
    assert ns.profile_language({"language": "en"}) == "en"
    assert ns.profile_language({"language": "de"}) == "tr"   # desteklenmiyor
    assert ns.profile_language({}) == "tr"


# --------------------------------------------------------------------------
# Uc yetkilendirmesi
# --------------------------------------------------------------------------

@uygulama_gerekir
def test_toplu_gonderim_anahtarsiz_calismaz(monkeypatch):
    """Anahtar tanimsizken ucu acik birakmak, herkesin tum kullanicilara
    bildirim gonderebilmesi demek olurdu."""
    monkeypatch.setattr(config, "NOTIFY_SCHEDULER_SECRET", None)
    with TestClient(app) as client:
        yanit = client.post("/api/v1/notify/run?type=daily")
    assert yanit.status_code == 503


@uygulama_gerekir
def test_toplu_gonderim_yanlis_anahtari_reddeder(monkeypatch):
    monkeypatch.setattr(config, "NOTIFY_SCHEDULER_SECRET", "dogru")
    with TestClient(app) as client:
        yanit = client.post("/api/v1/notify/run?type=daily",
                            headers={"Authorization": "yanlis"})
    assert yanit.status_code == 401


@uygulama_gerekir
def test_toplu_gonderim_kullanici_oturumuyla_acilmaz(monkeypatch):
    """Uc kullanici auth'u kabul etseydi herkes herkese bildirim attirabilirdi."""
    monkeypatch.setattr(config, "NOTIFY_SCHEDULER_SECRET", "dogru")
    with TestClient(app) as client:
        yanit = client.post("/api/v1/notify/run?type=daily",
                            headers={"Authorization": "Bearer kullanici-token"})
    assert yanit.status_code == 401


@uygulama_gerekir
def test_gecersiz_tur_reddedilir(monkeypatch):
    monkeypatch.setattr(config, "NOTIFY_SCHEDULER_SECRET", "dogru")
    with TestClient(app) as client:
        yanit = client.post("/api/v1/notify/run?type=spam",
                            headers={"Authorization": "dogru"})
    assert yanit.status_code == 422


@uygulama_gerekir
def test_tepki_bildirimi_arkadas_olmayana_gitmez(monkeypatch):
    from services import profile_service

    monkeypatch.setattr(profile_service, "are_friends", lambda a, b: False)
    with TestClient(app) as client:
        yanit = client.post("/api/v1/notify/reaction",
                            json={"friend_uid": "yabanci", "reaction": "shine"},
                            headers={"Authorization": "Bearer test-1"})
    assert yanit.status_code == 403


@uygulama_gerekir
def test_tepki_bildiriminde_kapali_kume_zorunlu(monkeypatch):
    from services import profile_service

    monkeypatch.setattr(profile_service, "are_friends", lambda a, b: True)
    with TestClient(app) as client:
        yanit = client.post(
            "/api/v1/notify/reaction",
            json={"friend_uid": "arkadas", "reaction": "serbest metin"},
            headers={"Authorization": "Bearer test-2"})
    assert yanit.status_code == 400


@uygulama_gerekir
def test_tepki_bildirimi_kendine_gonderilemez(monkeypatch):
    with TestClient(app) as client:
        yanit = client.post("/api/v1/notify/reaction",
                            json={"friend_uid": "dev-user", "reaction": "shine"},
                            headers={"Authorization": "Bearer test-3"})
    assert yanit.status_code == 400


# --------------------------------------------------------------------------
# Davet / kabul push'lari (OB2)
# --------------------------------------------------------------------------

@uygulama_gerekir
def test_davet_bildirimi_kendine_gonderilemez():
    with TestClient(app) as client:
        yanit = client.post("/api/v1/notify/invite",
                            json={"friend_uid": "dev-user"},
                            headers={"Authorization": "Bearer test-4"})
    assert yanit.status_code == 400


@uygulama_gerekir
def test_davet_bildirimi_gercek_kenar_sart(monkeypatch):
    """Spam kapisi: alicinin agacinda GERCEK `incoming` kenari yoksa 403.
    firestore.rules o kenari yalniz gercek davet akisinin kurmasina izin
    verdigi icin 'davet etmeden push atma' vektoru kaynakta kapali."""
    from services import profile_service

    monkeypatch.setattr(profile_service, "has_pending_invite",
                        lambda a, b: False)
    with TestClient(app) as client:
        yanit = client.post("/api/v1/notify/invite",
                            json={"friend_uid": "kurban"},
                            headers={"Authorization": "Bearer test-5"})
    assert yanit.status_code == 403


@uygulama_gerekir
def test_davet_bildirimi_gider_ve_ayni_gun_tekrarlamaz(monkeypatch):
    """Mutlu yol + cift-basina-gunluk tekrar korumasi: ikinci cagri
    'skipped' doner (davet geri cek-tekrar gonder spam'ine ikinci hat)."""
    import types

    from api import notify
    from services import profile_service, push_service

    monkeypatch.setattr(profile_service, "has_pending_invite",
                        lambda a, b: True)
    monkeypatch.setattr(
        profile_service, "get_profile",
        lambda uid: profil(uid=uid, quietFrom=0, quietTo=0,
                           displayName="Gonderen" if uid == "dev-user"
                           else "Alici"))

    gonderilenler: dict[tuple, str] = {}
    monkeypatch.setattr(
        ns, "already_sent",
        lambda uid, tur, gun: gonderilenler.get((uid, tur)) == gun)
    monkeypatch.setattr(
        ns, "mark_sent",
        lambda uid, tur, gun: gonderilenler.__setitem__((uid, tur), gun))

    yakalanan: list = []

    def sahte_send(mesajlar):
        yakalanan.extend(mesajlar)
        return types.SimpleNamespace(sent=len(mesajlar), failed=0, pruned=[])

    monkeypatch.setattr(push_service, "send", sahte_send)

    with TestClient(app) as client:
        bir = client.post("/api/v1/notify/invite",
                          json={"friend_uid": "alici-1"},
                          headers={"Authorization": "Bearer test-6"})
        iki = client.post("/api/v1/notify/invite",
                          json={"friend_uid": "alici-1"},
                          headers={"Authorization": "Bearer test-6"})

    assert bir.json()["status"] == "ok"
    assert iki.json()["status"] == "skipped"
    assert iki.json()["reason"] == "zaten-gonderildi"
    assert len(yakalanan) == 1
    mesaj = yakalanan[0]
    # BY-turu: `src` istemciye daveti tepkiden/kabulden ayırt ettirir.
    assert mesaj.data == {"type": "friend", "fromUid": "dev-user",
                          "src": "invite"}
    assert "🤝" in mesaj.title and "Gonderen" in mesaj.title
    assert notify is not None  # import dumani


@uygulama_gerekir
def test_davet_bildirimi_sessiz_saatte_duser(monkeypatch):
    """Dogrulamadan sonra asla raise yok: sessiz saatte 200 + skipped —
    davet Firestore'da zaten duruyor, push ustune eklenen bir sey."""
    from services import profile_service

    monkeypatch.setattr(profile_service, "has_pending_invite",
                        lambda a, b: True)
    monkeypatch.setattr(profile_service, "get_profile",
                        lambda uid: profil(uid=uid))
    monkeypatch.setattr(ns, "can_send_event",
                        lambda p, tur, now_utc=None: (False, "sessiz-saat"))

    with TestClient(app) as client:
        yanit = client.post("/api/v1/notify/invite",
                            json={"friend_uid": "alici-2"},
                            headers={"Authorization": "Bearer test-7"})
    assert yanit.status_code == 200
    assert yanit.json() == {"status": "skipped", "reason": "sessiz-saat"}


@uygulama_gerekir
def test_kabul_bildirimi_arkadaslik_sart(monkeypatch):
    from services import profile_service

    monkeypatch.setattr(profile_service, "are_friends", lambda a, b: False)
    with TestClient(app) as client:
        yanit = client.post("/api/v1/notify/invite-accepted",
                            json={"friend_uid": "yabanci"},
                            headers={"Authorization": "Bearer test-8"})
    assert yanit.status_code == 403


@uygulama_gerekir
def test_kabul_bildirimi_daveti_gonderene_gider(monkeypatch):
    import types

    from services import profile_service, push_service

    monkeypatch.setattr(profile_service, "are_friends", lambda a, b: True)
    monkeypatch.setattr(
        profile_service, "get_profile",
        lambda uid: profil(uid=uid, quietFrom=0, quietTo=0,
                           displayName="Kabul-Eden" if uid == "dev-user"
                           else "Davet-Eden"))
    monkeypatch.setattr(ns, "already_sent", lambda uid, tur, gun: False)
    monkeypatch.setattr(ns, "mark_sent", lambda uid, tur, gun: None)

    yakalanan: list = []

    def sahte_send(mesajlar):
        yakalanan.extend(mesajlar)
        return types.SimpleNamespace(sent=len(mesajlar), failed=0, pruned=[])

    monkeypatch.setattr(push_service, "send", sahte_send)

    with TestClient(app) as client:
        yanit = client.post("/api/v1/notify/invite-accepted",
                            json={"friend_uid": "davet-eden"},
                            headers={"Authorization": "Bearer test-9"})
    assert yanit.json()["status"] == "ok"
    assert len(yakalanan) == 1
    assert "🎉" in yakalanan[0].title
    assert "Kabul-Eden" in yakalanan[0].title
    assert yakalanan[0].data == {"type": "friend", "fromUid": "dev-user",
                                 "src": "invite_accepted"}


# --------------------------------------------------------------------------
# Tepki kumesi istemciyle ayni mi
# --------------------------------------------------------------------------

def test_tepki_kumesi_firestore_kuraliyla_ayni():
    """Sunucudaki kume kuraldan genisse, kuralin reddettigi bir tepki icin
    bildirim uretmeye calisirdik."""
    from api import notify
    import pathlib

    kurallar = (pathlib.Path(__file__).resolve().parents[2]
                / "infra" / "firestore.rules").read_text(encoding="utf-8")
    for anahtar in notify.REACTION_EMOJIS:
        assert f"'{anahtar}'" in kurallar, f"kuralda yok: {anahtar}"


def test_tepki_etiketleri_her_dilde_tam():
    from api import notify
    from core import i18n

    for kod in i18n.SUPPORTED:
        eksik = set(notify.REACTION_EMOJIS) - set(notify.REACTION_LABELS[kod])
        assert not eksik, f"{kod} dilinde eksik tepki etiketi: {eksik}"


def test_tepki_emojileri_istemciyle_ayni():
    """OB5 surtuklenme onarimi: eski test yalniz ANAHTARLARI karsilastiriyordu
    ve same_frequency sunucuda 🌊, mobil pickerda 🛰️ idi — kullanicinin
    BASTIGI emoji alicinin bildiriminde farkli gorunuyordu. Artik DEGERLER
    de birebir ayni olmak zorunda (kanonik = mobil)."""
    import pathlib
    import re

    from api import notify

    dart = (pathlib.Path(__file__).resolve().parents[2] / "apps" / "mobile"
            / "lib" / "core" / "friends.dart").read_text(encoding="utf-8")
    blok = dart.split("kReactions = {")[1].split("};")[0]
    istemci = dict(re.findall(r"'([a-z_]+)':\s*'([^']+)'", blok))
    assert istemci == notify.REACTION_EMOJIS, (
        "Tepki emojileri istemci/sunucu ayristi: "
        f"{set(istemci.items()) ^ set(notify.REACTION_EMOJIS.items())}")


def test_tema_emojileri_mobil_kThemeIcons_ile_ayni():
    """PUSH_SIGNAL_TITLE/PUSH_MIDDAY_TITLE'daki tema emojisi (OB5) mobil
    kart ikonlariyla ayni dortluden gelmeli — bildirimde 💼 gorup kartta
    baska simge bulmak guveni kirar."""
    import pathlib

    from services import prompts

    import re

    assert set(prompts.THEME_EMOJIS) == {
        "career", "relationships", "inner", "finance"}
    dart = (pathlib.Path(__file__).resolve().parents[2] / "apps" / "mobile"
            / "lib" / "widgets" / "basis_sheet.dart").read_text(
                encoding="utf-8")
    blok = dart.split("kThemeIcons = {")[1].split("};")[0]
    istemci = dict(re.findall(r"'([a-z_]+)':\s*'([^']+)'", blok))
    assert istemci == prompts.THEME_EMOJIS


# --------------------------------------------------------------------------
# Operasyon bayraklari
# --------------------------------------------------------------------------

def test_force_yalnizca_hedef_saati_atlar(gonderilmemis):
    """Hepsini atlayan bir bayrak, elinde anahtar olan birinin kullaniciyi
    gece yarisi uyandirmasina izin verirdi."""
    an = utc(12)  # Istanbul 15:00 — hedef saat degil

    gonder, gerekce = ns.should_send(profil(), "daily", an)
    assert not gonder and gerekce == "saat-uygun-degil"

    gonder, _ = ns.should_send(profil(), "daily", an, ignore_target_hour=True)
    assert gonder, "force hedef saati atlamali"


def test_force_sessiz_saati_atlamaz(gonderilmemis):
    an = utc(0)  # Istanbul 03:00 — sessiz aralik
    gonder, gerekce = ns.should_send(profil(), "daily", an,
                                     ignore_target_hour=True)
    assert not gonder
    assert gerekce == "sessiz-saat"


def test_force_tercihi_atlamaz(gonderilmemis):
    gonder, gerekce = ns.should_send(
        profil(notifyDaily=False), "daily", utc(12), ignore_target_hour=True)
    assert not gonder
    assert gerekce == "tercih-kapali"


def test_force_tekrar_korumasini_atlamaz(monkeypatch):
    monkeypatch.setattr(ns, "already_sent", lambda uid, tur, gun: True)
    gonder, gerekce = ns.should_send(profil(), "daily", utc(12),
                                     ignore_target_hour=True)
    assert not gonder
    assert gerekce == "zaten-gonderildi"


@uygulama_gerekir
def test_prova_gondermez_ve_kaydetmez(monkeypatch):
    """dry_run sifir riskli olmali: ne bildirim gider ne gonderim kaydi yazilir."""
    from api import notify
    from services import push_service

    monkeypatch.setattr(config, "NOTIFY_SCHEDULER_SECRET", "dogru")
    # Sessiz saat KAPALI (quietFrom == quietTo): aksi halde test duvar
    # saatine bagli olurdu ve gece calistirildiginda kirmizi donerdi.
    monkeypatch.setattr(notify, "_iter_profiles",
                        lambda: iter([profil(quietFrom=0, quietTo=0)]))
    monkeypatch.setattr(notify, "get_sky_now", lambda: SAHTE_GOKYUZU)
    monkeypatch.setattr(ns, "already_sent", lambda uid, tur, gun: False)
    monkeypatch.setattr(ns.gemini_service, "generate",
                        lambda prompt, **k: "Bugun kisa bir aralik var.")

    def gondermemeli(mesajlar):
        raise AssertionError("prova modunda gonderim yapilmamali")

    def kaydetmemeli(*a, **k):
        raise AssertionError("prova modunda gonderim kaydi yazilmamali")

    monkeypatch.setattr(push_service, "send", gondermemeli)
    monkeypatch.setattr(ns, "mark_sent", kaydetmemeli)

    with TestClient(app) as client:
        yanit = client.post(
            "/api/v1/notify/run?type=daily&dry_run=true&force=true",
            headers={"Authorization": "dogru"})

    assert yanit.status_code == 200
    govde = yanit.json()
    assert govde["status"] == "dry-run"
    assert govde["queued"] == 1
    assert govde["sent"] == 0


@uygulama_gerekir
def test_daily_fcm_yuku_derin_baglanti_alanlari_tasir(monkeypatch):
    """KA5: sabah bildiriminin data yükü route/fp/idx/d taşır — istemci
    dokununca ilgili sinyal kartının dayanak sayfasını açar. Eski yük
    yalnız {type, sign} idi ve dokunma sekme numarasından öteye gidemezdi."""
    from api import notify
    from services import push_service

    monkeypatch.setattr(config, "NOTIFY_SCHEDULER_SECRET", "dogru")
    monkeypatch.setattr(notify, "_iter_profiles",
                        lambda: iter([profil(quietFrom=0, quietTo=0)]))
    monkeypatch.setattr(notify, "get_sky_now", lambda: SAHTE_GOKYUZU)
    monkeypatch.setattr(ns, "already_sent", lambda uid, tur, gun: False)
    isaretler: list = []
    monkeypatch.setattr(
        ns, "mark_sent",
        lambda uid, tur, gun, extra=None: isaretler.append((uid, extra)))
    monkeypatch.setattr(ns, "last_daily_sent", lambda uid: None)
    # OT1.3: signal_push artık odak idx'i ve hafıza alanlarını da döner;
    # yük hep "0" değil GERÇEK idx'i taşır (tema çarkı 1'i seçebilir).
    monkeypatch.setattr(
        ns, "signal_push",
        lambda p, lang, today=None, onceki=None: (
            "🌙 Bugün: İç dünya", "Güne özgü cümle.", "iz123", 1,
            {"dailyBodyHash": "h1", "dailyTheme": "inner"}))

    yakalanan = []

    def sahte_gonder(mesajlar):
        yakalanan.extend(mesajlar)
        return push_service.SendResult(sent=len(mesajlar), failed=0,
                                       pruned=[], failed_uids=[])

    monkeypatch.setattr(push_service, "send", sahte_gonder)
    with TestClient(app) as client:
        yanit = client.post("/api/v1/notify/run?type=daily&force=true",
                            headers={"Authorization": "dogru"})
    assert yanit.status_code == 200 and yanit.json()["sent"] == 1
    veri = yakalanan[0].data
    assert veri["type"] == "daily"
    assert veri["route"] == "signal"
    assert veri["fp"] == "iz123"
    assert veri["idx"] == "1"
    assert veri["d"]  # yerel gün — bayat dokunma koruması
    # OT1.1: gönderim hafızası (gövde/odak) mark_sent'e ulaştı.
    assert isaretler and isaretler[0][1]["dailyBodyHash"] == "h1"


@uygulama_gerekir
def test_checkin_fcm_yuku_soruyu_tasir(monkeypatch):
    """KA4/KA5: check-in yükü soruyu ve gününü taşır (soğuk açılışta ağ
    turu olmadan sohbet soruyla açılır); soru yoksa kullanıcı atlanır."""
    from api import notify
    from services import push_service

    monkeypatch.setattr(config, "NOTIFY_SCHEDULER_SECRET", "dogru")
    monkeypatch.setattr(notify, "_iter_profiles",
                        lambda: iter([profil(quietFrom=0, quietTo=0)]))
    monkeypatch.setattr(notify, "get_sky_now", lambda: SAHTE_GOKYUZU)
    monkeypatch.setattr(ns, "already_sent", lambda uid, tur, gun: False)
    monkeypatch.setattr(ns, "mark_sent",
                        lambda uid, tur, gun, extra=None: None)
    monkeypatch.setattr(
        ns, "checkin_push",
        lambda p, lang, today=None: ("Rytho merak ediyor",
                                     "Bugün iş tarafı nasıl geçti?"))

    yakalanan = []

    def sahte_gonder(mesajlar):
        yakalanan.extend(mesajlar)
        return push_service.SendResult(sent=len(mesajlar), failed=0,
                                       pruned=[], failed_uids=[])

    monkeypatch.setattr(push_service, "send", sahte_gonder)
    with TestClient(app) as client:
        yanit = client.post("/api/v1/notify/run?type=checkin&force=true",
                            headers={"Authorization": "dogru"})
    assert yanit.status_code == 200 and yanit.json()["sent"] == 1
    veri = yakalanan[0].data
    assert veri["type"] == "checkin"
    assert veri["route"] == "chat"
    assert veri["q"] == "Bugün iş tarafı nasıl geçti?"
    assert veri["q_date"]

    # Soru yoksa: kullanıcı "soru-yok" ile atlanır, streak işine kalır.
    monkeypatch.setattr(notify, "_iter_profiles",
                        lambda: iter([profil(quietFrom=0, quietTo=0)]))
    monkeypatch.setattr(ns, "checkin_push", lambda p, lang, today=None: None)
    with TestClient(app) as client:
        yanit = client.post("/api/v1/notify/run?type=checkin&force=true",
                            headers={"Authorization": "dogru"})
    assert yanit.json()["sent"] == 0  # yeni gonderim yok
    assert yanit.json()["skipped"].get("soru-yok") == 1


def test_ignore_dedupe_yalnizca_tekrar_korumasini_atlar(monkeypatch):
    monkeypatch.setattr(ns, "already_sent", lambda uid, tur, gun: True)

    gonder, gerekce = ns.should_send(profil(), "daily", utc(6))
    assert not gonder and gerekce == "zaten-gonderildi"

    gonder, _ = ns.should_send(profil(), "daily", utc(6), ignore_dedupe=True)
    assert gonder


def test_hicbir_bayrak_sessiz_saati_veya_tercihi_atlamaz(monkeypatch):
    """Elinde zamanlayici anahtari olan biri bile kullaniciyi gece yarisi
    uyandiramamali ya da kapattigi bildirimi ona gonderememeli."""
    monkeypatch.setattr(ns, "already_sent", lambda uid, tur, gun: False)

    gece = utc(0)  # Istanbul 03:00
    gonder, gerekce = ns.should_send(profil(), "daily", gece,
                                     ignore_target_hour=True,
                                     ignore_dedupe=True)
    assert not gonder and gerekce == "sessiz-saat"

    gonder, gerekce = ns.should_send(
        profil(notifyDaily=False, quietFrom=0, quietTo=0), "daily", utc(12),
        ignore_target_hour=True, ignore_dedupe=True)
    assert not gonder and gerekce == "tercih-kapali"


@uygulama_gerekir
def test_ignore_dedupe_force_olmadan_reddedilir(monkeypatch):
    monkeypatch.setattr(config, "NOTIFY_SCHEDULER_SECRET", "dogru")
    with TestClient(app) as client:
        yanit = client.post(
            "/api/v1/notify/run?type=daily&ignore_dedupe=true",
            headers={"Authorization": "dogru"})
    assert yanit.status_code == 400


def test_android_kanal_kimligi_istemciyle_ayni():
    """Kanal kimlikleri ayrisirsa Android bildirimi varsayilan kanala dusurur
    ve bildirim ekranin ustunde belirmez."""
    import pathlib
    from services import push_service

    dart = (pathlib.Path(__file__).resolve().parents[2] / "apps" / "mobile"
            / "lib" / "core" / "notifications.dart").read_text(encoding="utf-8")
    assert f"'{push_service.ANDROID_CHANNEL_ID}'" in dart, (
        f"Istemcide {push_service.ANDROID_CHANNEL_ID} kanali tanimli degil")
