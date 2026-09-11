r"""Kimlik dogrulama kapisinin HIZI ve dogru tarafa dusmesi.

Iki ayri kusur bu dosyada korunuyor.

**Birincisi (yavaslik).** Kimlik bilgisi cozulemedigi halde her istek ~12
saniye deneyip vazgeciyordu; kullanici bunu "sohbet gec geliyor", "ekran
acilmiyor" diye gordu. Olculen: `google.auth.default()` ADC'siz bir makinede
11,98 saniye. Ayni cagriyi Firestore istemcisi de yapiyordu.

**Ikincisi (uretimi kiran duzeltme).** Ilk duzeltme yoklamayi 3 saniye ile
sinirlayip sonuclanmazsa "kimlik yok" sayiyordu. Cloud Run soguk
baslatmasinda meta veri sunucusu 3 saniyeyi asti:

    ADC yoklamasi 3.0 sn icinde sonuclanmadi.
    Kimlik bilgisi yok; Firestore devre disi.   -> webhook 500
    ADC cozulemedi. Tum istekler 401 donecek.

Abonelik webhook'lari dustu, kullanici odeme yapti ve ekranlar kilitli kaldi.
Hata: "yoklama bitmedi" ile "kimlik yok" ayni sey sayildi.

Bu yuzden buradaki en onemli test `test_sonuclanmamis_yoklama_hicbir_seyi_
kapatmaz`. Digerleri hizi korur; o, DOGRULUGU korur.

Calistirma:  .venv\Scripts\python.exe -m pytest tests/test_auth_gate.py -q
"""
from __future__ import annotations

import asyncio
import threading
import time

import pytest

from core import auth, config, firestore, gcp_credentials


@pytest.fixture(autouse=True)
def temiz_durum():
    auth.reset_firebase_state()
    firestore._client = None
    firestore._failed = False
    yield
    auth.reset_firebase_state()
    firestore._client = None
    firestore._failed = False


class _SahteToken:
    def __init__(self, token: str = "sahte"):
        self.credentials = token


def _dusen_yoklama():
    def yokla():
        raise RuntimeError("ADC yok")

    return yokla


def _asili_yoklama(kapi: threading.Event):
    """Hic sonuclanmayan yoklama — Cloud Run'da yasanan durum."""

    def yokla():
        kapi.wait(timeout=30)
        raise RuntimeError("ADC yok")

    return yokla


# ---------------------------------------------------------------------------
# DOGRULUK — uretimi kiran kusur
# ---------------------------------------------------------------------------

def test_sonuclanmamis_yoklama_hicbir_seyi_kapatmaz(monkeypatch):
    """Yoklama sonuclanmadiysa erisim ACIK varsayilmali.

    Uretimi kiran tam olarak buydu: sonucsuz bir yoklama "kimlik yok" diye
    okundu, Firestore ve token dogrulama kapandi.
    """
    kapi = threading.Event()
    monkeypatch.setattr("google.auth.default", _asili_yoklama(kapi))
    try:
        # Yoklama arka planda asili dururken:
        assert gcp_credentials.available() is True, (
            "sonuclanmamis yoklama 'kimlik yok' sayiliyor — uretimi kiran hata"
        )
        # Ust uste sorulunca da ayni.
        for _ in range(5):
            assert gcp_credentials.available() is True
    finally:
        kapi.set()


def test_yoklama_istek_yolunu_bloklamaz(monkeypatch):
    """`available()` BEKLEMEZ. Her istegin onunde duran bir cagri bu."""
    kapi = threading.Event()
    monkeypatch.setattr("google.auth.default", _asili_yoklama(kapi))
    try:
        bas = time.monotonic()
        for _ in range(20):
            gcp_credentials.available()
        gecen = time.monotonic() - bas
        assert gecen < 0.5, f"20 cagri {gecen:.2f} sn surdu; bloklaniyor"
    finally:
        kapi.set()


def test_firestore_kimlik_yoklamasindan_KALICI_kapanmaz(monkeypatch):
    """Firestore'un `_failed` mandali kimlik yoklamasindan KURULMAMALI.

    Kalici bir mandaldi: kimlik gorunmedigi anda kuruluyordu ve Firestore
    instance omru boyunca kapaniyordu — abonelik webhook'lari 500 dondu.
    Mandal yalnizca istemci GERCEKTEN kurulamadiginda kurulmali, ki kimlik
    sonradan gorunurse toparlanabilsin.
    """
    monkeypatch.setattr("google.auth.default", _dusen_yoklama())
    gcp_credentials.warm_up()
    assert gcp_credentials._bekle(timeout=10) is False

    assert firestore.get_client() is None
    assert firestore._failed is False, (
        "kimlik yoklamasi Firestore'u KALICI olarak kapatti"
    )


def test_kesin_olumsuz_sonuc_erisimi_kapatir(monkeypatch):
    """Yoklama KESIN olarak dustuyse erisim kapanmali — sinir orada."""
    monkeypatch.setattr("google.auth.default", _dusen_yoklama())

    gcp_credentials.warm_up()
    assert gcp_credentials._bekle(timeout=10) is False
    assert gcp_credentials.available() is False


def test_olumsuz_sonuc_kalici_degil(monkeypatch):
    """Gecici bir sorun kimlik dogrulamayi surekli kapatmamali."""
    monkeypatch.setattr("google.auth.default", _dusen_yoklama())
    monkeypatch.setattr(gcp_credentials, "NEGATIVE_TTL_SECONDS", 0.05)

    gcp_credentials.warm_up()
    assert gcp_credentials._bekle(timeout=10) is False
    assert gcp_credentials.available() is False

    time.sleep(0.1)
    # Sure dolunca yeniden yoklanir ve bu arada ERISILEBILIR varsayilir.
    assert gcp_credentials.available() is True


# ---------------------------------------------------------------------------
# HIZ — ilk kusur
# ---------------------------------------------------------------------------

def test_yoklama_bir_kez_yapilir(monkeypatch):
    """Yoklama istek basina TEKRARLANMAMALI; asil yavaslik kusuru buydu."""
    sayac = {"n": 0}

    def yokla():
        sayac["n"] += 1
        raise RuntimeError("ADC yok")

    monkeypatch.setattr("google.auth.default", yokla)

    gcp_credentials.warm_up()
    gcp_credentials._bekle(timeout=10)
    for _ in range(10):
        gcp_credentials.available()

    assert sayac["n"] == 1, f"yoklama {sayac['n']} kez calisti"


def test_firestore_ayni_yoklamayi_paylasir(monkeypatch):
    """Firestore kendi ADC cozumlemesini yapmamali — bedel iki kez odeniyordu."""
    sayac = {"n": 0}

    def yokla():
        sayac["n"] += 1
        raise RuntimeError("ADC yok")

    monkeypatch.setattr("google.auth.default", yokla)

    gcp_credentials.warm_up()
    gcp_credentials._bekle(timeout=10)
    auth._init_firebase()
    firestore.get_client()

    assert sayac["n"] == 1, "auth ve firestore ayri ayri yokluyor"


# ---------------------------------------------------------------------------
# Kapi davranisi
# ---------------------------------------------------------------------------

def test_kimlik_yoksa_uretimde_401(monkeypatch):
    """Kimlik KESIN yoksa uretim FAIL-CLOSED kalmali."""
    monkeypatch.setattr("google.auth.default", _dusen_yoklama())
    monkeypatch.setattr(config, "DEV_MODE", False)

    gcp_credentials.warm_up()
    gcp_credentials._bekle(timeout=10)

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as hata:
        asyncio.run(auth.get_current_user(credentials=_SahteToken(), lang="tr"))
    assert hata.value.status_code == 401


def test_dogrulama_olay_dongusunu_bloklamaz(monkeypatch):
    """`verify_id_token` bloklayan bir cagri; is parcacigi havuzunda kosmali.

    Imza anahtarlari ~6 saatte bir Google'dan yeniden cekiliyor. Bu ag turu
    olay dongusunde yapilirsa o sirada gelen TUM istekler bekler.
    """
    monkeypatch.setattr(auth, "_firebase_ready", True)
    monkeypatch.setattr(config, "DEV_MODE", False)

    def yavas_dogrula(token):
        time.sleep(0.4)
        return {"uid": "u1", "email": "a@b.c"}

    monkeypatch.setattr(auth, "_verify", yavas_dogrula)

    isaret = {"kosti": False}

    async def digeri():
        await asyncio.sleep(0.1)
        isaret["kosti"] = True

    async def senaryo():
        _, kullanici = await asyncio.gather(
            digeri(),
            auth.get_current_user(credentials=_SahteToken(), lang="tr"),
        )
        return kullanici

    kullanici = asyncio.run(senaryo())

    assert kullanici.uid == "u1"
    assert isaret["kosti"], "olay dongusu bloklandi"


# ---------------------------------------------------------------------------
# Surum aynasi (PBZ, K10): users/{uid}.appBuild
# ---------------------------------------------------------------------------

class _SahteAyna:
    """Yalnizca users/{uid}.set(..., merge=True) yuzeyi; yazimlari sayar."""

    def __init__(self):
        self.yazimlar: list = []
        self._uid = None

    def collection(self, ad):
        assert ad == "users"
        return self

    def document(self, uid):
        self._uid = uid
        return self

    def set(self, veri, merge=False):
        self.yazimlar.append((self._uid, veri, merge))


@pytest.fixture()
def ayna(monkeypatch):
    """Dogrulanmis token yolu (DEV_MODE kapali) + sahte Firestore."""
    from core import app_gate

    depo = _SahteAyna()
    monkeypatch.setattr(app_gate.firestore_client, "get_client", lambda: depo)
    monkeypatch.setattr(auth, "_firebase_ready", True)
    monkeypatch.setattr(auth, "_verify", lambda t: {"uid": "u1"})
    monkeypatch.setattr(config, "DEV_MODE", False)
    app_gate.reset_memo()
    yield depo
    app_gate.reset_memo()


def _dogrula(**kw):
    return asyncio.run(auth.get_current_user(
        credentials=_SahteToken(), lang="tr", **kw))


def test_ayna_uid_basina_bir_kez(ayna):
    """Her kimlikli istek buradan geciyor; yazim uid basina gunde bir."""
    for _ in range(5):
        kullanici = _dogrula(x_app_build="35")
        assert kullanici.uid == "u1"
    assert ayna.yazimlar == [("u1", {"appBuild": 35}, True)]


def test_ayna_surum_degisince_yeniden_yazar(ayna):
    """Gun icinde guncelleyen kullanici eski surumde gorunmemeli."""
    _dogrula(x_app_build="35")
    _dogrula(x_app_build="36")
    _dogrula(x_app_build="36")
    assert [v["appBuild"] for _, v, _ in ayna.yazimlar] == [35, 36]


def test_basliksiz_ve_bozuk_baslik_yazmaz(ayna):
    """Baslik yoksa 'bilinmiyor' durustce bilinmiyor kalir (0 yazilmaz)."""
    _dogrula(x_app_build=None)
    _dogrula(x_app_build="abc")
    _dogrula(x_app_build="0")
    _dogrula(x_app_build="-2")
    assert ayna.yazimlar == []


def test_depends_disi_cagri_sentinel_yazmaz(ayna):
    """api/admin.py collect ve bu dosyadaki testler `x_app_build` vermeden
    cagiriyor; o yolda parametre None DEGIL, FastAPI'nin truthy Header
    nesnesi olur. Dizgi sanilip yazilmamali, kimlik de dusmemeli."""
    kullanici = _dogrula()
    assert kullanici.uid == "u1"
    assert ayna.yazimlar == []


def test_ayna_dusunce_kimlik_dusmez(ayna, monkeypatch):
    """Best-effort: Firestore patlasa da istek 401'e DONMEZ."""
    from core import app_gate

    class _Bozuk:
        def collection(self, ad):
            raise RuntimeError("Firestore dustu")

    monkeypatch.setattr(app_gate.firestore_client, "get_client",
                        lambda: _Bozuk())
    kullanici = _dogrula(x_app_build="35")
    assert kullanici.uid == "u1"


def test_ayna_yazim_dusunce_memo_kurulmaz(ayna, monkeypatch):
    """Gecici hata: bir sonraki istek yeniden dener (24 saat beklemez)."""
    from core import app_gate

    class _Bozuk:
        def collection(self, ad):
            raise RuntimeError("Firestore dustu")

    monkeypatch.setattr(app_gate.firestore_client, "get_client",
                        lambda: _Bozuk())
    _dogrula(x_app_build="35")
    monkeypatch.setattr(app_gate.firestore_client, "get_client", lambda: ayna)
    _dogrula(x_app_build="35")
    assert ayna.yazimlar == [("u1", {"appBuild": 35}, True)]


def test_dev_mode_anonim_yolunda_ayna_yok(ayna, monkeypatch):
    """DEV_MODE'un dev-user'i icin ayna yazilmaz — dogrulanmis token yolu
    disinda yazim yok."""
    monkeypatch.setattr(config, "DEV_MODE", True)
    monkeypatch.setattr(auth, "_init_firebase", lambda: False)
    kullanici = asyncio.run(auth.get_current_user(
        credentials=None, lang="tr", x_app_build="35"))
    assert kullanici.uid == "dev-user"
    assert ayna.yazimlar == []
