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
