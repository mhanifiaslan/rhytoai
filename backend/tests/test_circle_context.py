"""Çevre fısıltısı bekçileri (KA6).

İki değişmez korunur:

1. **Gizlilik**: eklenen kişilerin GERÇEK ADI sunucuda yok — fısıltı ilişki
   etiketi ("eşin") + burçlarla kurulur; kişi dokümanından ad SIZAMAZ.
2. **Tahmin yok**: akraba-kelime eşleşmesi aynı türde birden çok kişi
   bulursa fısıltıya KİMSE iliştirilmez — yanlış kişinin ölçümünü
   iliştirmek, hiç iliştirmemekten kötü.

Çalıştırma:  .venv\\Scripts\\python.exe -m pytest tests/test_circle_context.py -q
"""
from __future__ import annotations

import pytest

from services import circle_context, people_service, profile_service


# --------------------------------------------------------------------------
# Akraba-kelime eşleşmesi
# --------------------------------------------------------------------------

@pytest.mark.parametrize("mesaj,beklenen", [
    ("Eşimle aram nasıl olacak?", "partner"),
    ("kocam beni anlamıyor", "partner"),
    ("Oğlum bu hafta sınava giriyor", "child"),
    ("Annemle konuşamıyorum", "parent"),
    ("kardeşimle kavga ettik", "sibling"),
    ("patronum çok baskı yapıyor", "work"),
    ("bugün nasıl bir gün", None),
    ("işimle ilgili karar veremiyorum", None),
])
def test_akraba_kelime_eslesmesi_tr(mesaj, beklenen):
    assert circle_context.match_relation(mesaj, "tr") == beklenen


@pytest.mark.parametrize("mesaj,beklenen", [
    ("How are things with my wife?", "partner"),
    ("My son starts school next week", "child"),
    ("I can't talk to my mother", "parent"),
    ("what does today look like", None),
])
def test_akraba_kelime_eslesmesi_en(mesaj, beklenen):
    assert circle_context.match_relation(mesaj, "en") == beklenen


def test_noktali_buyuk_i_tuzagi():
    """Türkçe cümle başındaki "Eşim" — `str.lower()` yalın kullanılsa
    birleşik nokta yüzünden eşleşme sessizce kaçardı (İ tuzağı)."""
    assert circle_context.match_relation("EŞİM için soruyorum", "tr") == \
        "partner"


# --------------------------------------------------------------------------
# Kişi çözümü
# --------------------------------------------------------------------------

def _kisiler(monkeypatch, kayitlar):
    monkeypatch.setattr(people_service, "list_people",
                        lambda uid: kayitlar)


def test_tek_aday_kimligi_doner(monkeypatch):
    _kisiler(monkeypatch, [
        {"id": "p1", "relation": "partner", "birthDate": "1992-03-04"},
        {"id": "p2", "relation": "child", "birthDate": "2015-06-07"},
    ])
    assert circle_context.person_for_relation("u", "partner") == "p1"


def test_coklu_aday_tahmin_edilmez(monkeypatch):
    _kisiler(monkeypatch, [
        {"id": "p1", "relation": "child", "birthDate": "2015-06-07"},
        {"id": "p2", "relation": "child", "birthDate": "2018-01-02"},
    ])
    assert circle_context.person_for_relation("u", "child") is None


def test_dogum_verisiz_kisi_aday_olmaz(monkeypatch):
    _kisiler(monkeypatch, [
        {"id": "p1", "relation": "partner", "birthDate": ""},
    ])
    assert circle_context.person_for_relation("u", "partner") is None


def test_oncelik_sirasi_partner_once(monkeypatch):
    _kisiler(monkeypatch, [
        {"id": "c1", "relation": "child", "birthDate": "2015-06-07"},
        {"id": "e1", "relation": "partner", "birthDate": "1992-03-04"},
    ])
    assert circle_context.priority_person("u") == "e1"


# --------------------------------------------------------------------------
# Fısıltı içeriği
# --------------------------------------------------------------------------

@pytest.fixture
def bellek(monkeypatch):
    import core.cache as cache_mod
    depo: dict = {}
    monkeypatch.setattr(cache_mod, "get", depo.get)
    monkeypatch.setattr(
        cache_mod, "set",
        lambda k, v, ttl_seconds=0, owner_uid=None: depo.update({k: v}))
    return depo


def test_fisilti_etiket_ve_burc_tasir_ad_TASIMAZ(monkeypatch, bellek):
    """Kişi dokümanında ad zaten yok; bu test yapıyı kilitler — biri bir
    gün `displayName` sızdırırsa fısıltı yine de onu OKUMAZ."""
    _kisiler(monkeypatch, [
        {"id": "p1", "relation": "partner", "birthDate": "1992-03-04",
         "birthTime": "10:15", "sunSign": "Terazi ♎", "moonSign": "Yengeç ♋",
         "displayName": "SIZINTI-ADI"},
        {"id": "p2", "relation": "child", "birthDate": "2015-06-07",
         "sunSign": "Koç ♈"},
    ])
    monkeypatch.setattr(circle_context, "list_accepted_friend_uids",
                        lambda uid, limit=5: [])
    metin = circle_context.circle_whisper("u", "tr")
    assert "eşin" in metin
    assert "Terazi" in metin
    assert "çocuğun" in metin
    assert "SIZINTI-ADI" not in metin
    # Saatsiz kişi işaretlenir (saatsiz harita disiplini fısıltıda da).
    assert "doğum saati bilinmiyor" in metin


def test_arkadaslar_ad_ve_burcla_gecer(monkeypatch, bellek):
    """Arkadaş adı SUNUCUDA zaten herkese açık (publicProfiles) — fısıltıda
    geçmesi gizlilik açmaz."""
    _kisiler(monkeypatch, [])
    monkeypatch.setattr(circle_context, "list_accepted_friend_uids",
                        lambda uid, limit=5: ["f1"])
    monkeypatch.setattr(profile_service, "get_profile",
                        lambda uid: {"displayName": "Erkan",
                                     "sunSign": "Boğa ♉"})
    metin = circle_context.circle_whisper("u", "tr")
    assert "Arkadaşları:" in metin
    assert "Erkan (Boğa)" in metin


def test_bos_cevre_bos_fisilti(monkeypatch, bellek):
    _kisiler(monkeypatch, [])
    monkeypatch.setattr(circle_context, "list_accepted_friend_uids",
                        lambda uid, limit=5: [])
    assert circle_context.circle_whisper("u", "tr") == ""


def test_fisilti_onbelleklenir(monkeypatch, bellek):
    sayac = {"n": 0}

    def sayan(uid):
        sayac["n"] += 1
        return []

    monkeypatch.setattr(people_service, "list_people", sayan)
    monkeypatch.setattr(circle_context, "list_accepted_friend_uids",
                        lambda uid, limit=5: [])
    circle_context.circle_whisper("u", "tr")
    circle_context.circle_whisper("u", "tr")
    assert sayac["n"] == 1


class TestAdKurali:
    """KL-turu: modelin adsız yakına arkadaş adı takması.

    Cihazda ölçüldü: kullanıcı "How does this week look for me?" diye
    sordu, cevap "your partner, **Aslan**, is navigating..." dedi.
    "Aslan" adı fısıltıdaki ARKADAŞ listesinden geliyor; eklenen kişinin
    adı sunucuya hiç çıkmıyor (aşağıdaki bekçi bunu ayrıca doğruluyor).
    Yani sızıntı değil, uydurma — ama kullanıcı için sonucu aynı.
    """

    def test_kisi_satiri_AD_tasimaz(self):
        from services import circle_context
        satir = circle_context._kisi_satiri(
            {"relation": "partner", "sunSign": "Aslan ♌",
             "displayName": "Zehra", "name": "Zehra"}, "tr")
        # Burç adı "Aslan" geçebilir (gezegen konumu); kişinin ADI geçemez.
        assert "Zehra" not in satir

    def test_promptta_ad_yakistirma_yasagi_iki_dilde_var(self):
        from services.prompts import tr, en
        assert "AD KURALI" in tr.WHISPER_CIRCLE
        assert "NAMING RULE" in en.WHISPER_CIRCLE
        # Kural iki şeyi birden söylemeli: ad verilmez + ad taşınmaz.
        for metin, anahtarlar in ((tr.WHISPER_CIRCLE, ("ad yakıştırma", "TAŞIMA")),
                                  (en.WHISPER_CIRCLE, ("never attach a name",
                                                       "never carry a friend's name"))):
            for anahtar in anahtarlar:
                assert anahtar in metin, anahtar
