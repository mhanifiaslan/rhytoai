"""Tek cihaz kilidinin değişmezleri (TC-turu: sunucu hakem, son giriş kazanır).

En önemlileri:

* **Kilit yalnız ÜCRETLİ abonede** (K3): deneme kullanıcısı `is_subscriber`
  olsa da kilitlenmez; FORCE_PLUS de kilidi açmaz.
* **Başlıksız istek kilitlenmez** — eski sürüm istemci kimlik göndermez.
* **`auth_time > claimedAt` → otomatik devralma** (K2); küçük/eşit → 409.
* **Uyumsuzlukta memo'ya güvenilmez** (K4): bayat memo sahte 409 üretmez.
* **Okuma hatası = bilinmiyor → geçir, YAZMA** (K5).
* **Serbest bırakma yalnız sahipte** (K7).

Zaman `device._now` üzerinden dondurulur: `claimedAt` = 1000 sn; testler
`auth_time`'ı buna göre seçer.

Çalıştırma:  .venv\\Scripts\\python.exe -m pytest tests/test_device.py -q
"""
from __future__ import annotations

import datetime as dt

import pytest
from fastapi import HTTPException

from core import device

UTC = dt.timezone.utc


def _t(saniye: float) -> dt.datetime:
    return dt.datetime.fromtimestamp(saniye, UTC)


# ---------------------------------------------------------------------------
# Bellek içi sahte Firestore — iç içe koleksiyon, get/set(merge)/delete.
# `depo["__oku_hata__"]` / `depo["__yaz_hata__"]` bayrakları hata enjekte eder.
# ---------------------------------------------------------------------------

class _SahteAnlik:
    def __init__(self, data):
        self._data = data

    @property
    def exists(self):
        return self._data is not None

    def to_dict(self):
        return dict(self._data) if self._data else {}


class _SahteDoc:
    def __init__(self, depo, yol):
        self._depo = depo
        self._yol = yol

    def get(self):
        if self._depo.get("__oku_hata__"):
            raise RuntimeError("firestore okunamadı")
        return _SahteAnlik(self._depo.get(self._yol))

    def set(self, data, merge=False):
        if self._depo.get("__yaz_hata__"):
            raise RuntimeError("firestore yazılamadı")
        mevcut = dict(self._depo.get(self._yol) or {}) if merge else {}
        mevcut.update(data)
        self._depo[self._yol] = mevcut

    def delete(self):
        self._depo.pop(self._yol, None)

    def collection(self, ad):
        return _SahteKoleksiyon(self._depo, f"{self._yol}/{ad}")


class _SahteKoleksiyon:
    def __init__(self, depo, yol):
        self._depo = depo
        self._yol = yol

    def document(self, ad):
        return _SahteDoc(self._depo, f"{self._yol}/{ad}")


class _SahteClient:
    def __init__(self, depo):
        self._depo = depo

    def collection(self, ad):
        return _SahteKoleksiyon(self._depo, ad)


@pytest.fixture()
def depo(monkeypatch):
    """Ücretli abone, deneme kapalı, saat 1000 sn'de donmuş, memo temiz."""
    veriler: dict = {}
    monkeypatch.setattr(device.firestore_client, "get_client",
                        lambda: _SahteClient(veriler))
    monkeypatch.setattr(device.entitlements, "FORCE_PLUS", False)
    monkeypatch.setattr(device.entitlements, "get_subscription",
                        lambda uid: {"active": True})
    monkeypatch.setattr(device.entitlements, "in_trial", lambda uid: False)
    monkeypatch.setattr(device, "_now", lambda: _t(1000))
    device.clear_cache()
    yield veriler
    device.clear_cache()


def _kayit(depo, uid="u1"):
    return depo.get(f"users/{uid}/private/device")


def _sahiplen(depo, cihaz="cihaz-a", auth_time=900, platform=None):
    """İlk sahiplenme: claimedAt = 1000 (donmuş saat)."""
    device.enforce_single_device("u1", cihaz, auth_time=auth_time,
                                 platform=platform)
    assert _kayit(depo)["deviceId"] == cihaz


# ---------------------------------------------------------------------------
# Kimin için: yalnız ücretli abone
# ---------------------------------------------------------------------------

def test_basliksiz_gecer(depo):
    """Eski sürüm istemciler kimlik göndermez; kilitlemek onları kırardı."""
    device.enforce_single_device("u1", None, auth_time=900)
    device.enforce_single_device("u1", "", auth_time=900)
    assert _kayit(depo) is None


def test_deneme_kullanicisi_kilitlenmez(depo, monkeypatch):
    """K3: deneme `is_subscriber`'ı açar ama kilidi AÇMAZ — kayıt bile yok."""
    monkeypatch.setattr(device.entitlements, "get_subscription",
                        lambda uid: {"active": False})
    monkeypatch.setattr(device.entitlements, "in_trial", lambda uid: True)
    assert device.entitlements.is_subscriber("u1") is True  # sahte tutarlı

    device.enforce_single_device("u1", "cihaz-a", auth_time=900)
    device.enforce_single_device("u1", "cihaz-b", auth_time=900)
    assert _kayit(depo) is None


def test_force_plus_kilidi_acmaz(depo, monkeypatch):
    monkeypatch.setattr(device.entitlements, "get_subscription",
                        lambda uid: {"active": False})
    monkeypatch.setattr(device.entitlements, "FORCE_PLUS", True)
    device.enforce_single_device("u1", "cihaz-a", auth_time=900)
    device.enforce_single_device("u1", "cihaz-b", auth_time=900)
    assert _kayit(depo) is None


def test_ucretli_abone_kilitlenir(depo):
    _sahiplen(depo)  # claimedAt = 1000
    with pytest.raises(HTTPException) as exc:
        device.enforce_single_device("u1", "cihaz-b", auth_time=900)
    assert exc.value.status_code == 409
    assert exc.value.headers["X-Device-Conflict"] == "1"
    # Kayıt DEĞİŞMEDİ: 409 devralma değildir.
    assert _kayit(depo)["deviceId"] == "cihaz-a"


# ---------------------------------------------------------------------------
# Sahiplenme ve "son giriş kazanır"
# ---------------------------------------------------------------------------

def test_kayit_yoksa_sahiplenir_authtime_ile(depo):
    device.enforce_single_device("u1", "cihaz-a", auth_time=900,
                                 platform="ios")
    k = _kayit(depo)
    assert k["deviceId"] == "cihaz-a"
    assert k["authTime"] == 900
    assert k["platform"] == "ios"
    assert k["claimedAt"] == _t(1000)
    assert k["lastSeenAt"] == _t(1000)
    # Platform aynası profile de düşer (adminStats kırılımı).
    assert depo["users/u1"]["platform"] == "ios"


def test_ayni_cihaz_gecer(depo):
    _sahiplen(depo)
    device.enforce_single_device("u1", "cihaz-a", auth_time=900)  # fırlatmamalı
    assert _kayit(depo)["claimedAt"] == _t(1000)  # yeniden yazılmadı


def test_sonraki_giris_otomatik_devralir(depo, monkeypatch):
    """K2: B'nin girişi A'nın devralmasından SONRA → B soru görmeden alır."""
    _sahiplen(depo, "cihaz-a", auth_time=900, platform="android")
    monkeypatch.setattr(device, "_now", lambda: _t(2000))

    device.enforce_single_device("u1", "cihaz-b", auth_time=1500)  # 1500 > 1000

    k = _kayit(depo)
    assert k["deviceId"] == "cihaz-b"
    assert k["authTime"] == 1500
    assert k["claimedAt"] == _t(2000)
    # Eski cihaz artık düşer: girişi (900) yeni devralmadan (2000) önce.
    with pytest.raises(HTTPException) as exc:
        device.enforce_single_device("u1", "cihaz-a", auth_time=900)
    assert exc.value.status_code == 409


def test_onceki_giris_409_ve_other_bilgisi(depo):
    """auth_time < claimedAt → 409; öbür cihazın bilgisi başlıklarda,
    detail düz metin (istemci friendlyError ile gösterir)."""
    _sahiplen(depo, "cihaz-a", auth_time=900, platform="android")

    with pytest.raises(HTTPException) as exc:
        device.enforce_single_device("u1", "cihaz-b", auth_time=999, lang="tr")

    assert exc.value.status_code == 409
    basliklar = exc.value.headers
    assert basliklar["X-Device-Conflict"] == "1"
    assert basliklar["X-Device-Other-Platform"] == "android"
    assert basliklar["X-Device-Claimed-At"] == "1970-01-01T00:16:40+00:00"
    assert isinstance(exc.value.detail, str) and "cihaz" in exc.value.detail
    assert _kayit(depo)["deviceId"] == "cihaz-a"


def test_esit_authtime_eskiyi_korur(depo):
    """Eşitlik devralma DEĞİL: `>` şart, ping-pong yalnız kullanıcı isteğiyle."""
    _sahiplen(depo)  # claimedAt = 1000
    with pytest.raises(HTTPException):
        device.enforce_single_device("u1", "cihaz-b", auth_time=1000)
    assert _kayit(depo)["deviceId"] == "cihaz-a"


def test_acik_devralma_eski_cihazi_dislar(depo, monkeypatch):
    """"Bu cihazda kullan": claimedAt=now yazar → öbür cihazın auth_time'ı
    ondan küçük kalır, yeniden giriş yapmadan geri alamaz."""
    _sahiplen(depo, "cihaz-a", auth_time=900)
    monkeypatch.setattr(device, "_now", lambda: _t(2000))
    device.enforce_single_device("u1", "cihaz-b", auth_time=1500)  # B devraldı
    monkeypatch.setattr(device, "_now", lambda: _t(3000))

    assert device.claim_device("u1", "cihaz-a", auth_time=900,
                               platform="android") == {"claimed": True}

    device.enforce_single_device("u1", "cihaz-a", auth_time=900)  # A geçer
    with pytest.raises(HTTPException):
        device.enforce_single_device("u1", "cihaz-b", auth_time=1500)  # B düşer


# ---------------------------------------------------------------------------
# Memo ve okuma hatası
# ---------------------------------------------------------------------------

def _sayan_client(monkeypatch):
    sayac = {"n": 0}
    orijinal = device.firestore_client.get_client

    def sayan():
        sayac["n"] += 1
        return orijinal()

    monkeypatch.setattr(device.firestore_client, "get_client", sayan)
    return sayac


def test_bayat_memo_uyumsuzlukta_firestore_yeniden_okunur(depo, monkeypatch):
    """K4: bu instance memo'da A'yı tutarken başka instance B'yi devraldı.
    B'nin isteği memo'ya güvenilseydi 409 alırdı (900 < 1000); Firestore
    yeniden okununca eşit → geçer, yazım yok, memo B olur."""
    _sahiplen(depo, "cihaz-a", auth_time=900)  # memo: A, claimedAt 1000
    depo["users/u1/private/device"] = {
        "deviceId": "cihaz-b", "platform": "ios", "authTime": 1200,
        "claimedAt": _t(1500), "lastSeenAt": _t(1500)}
    kopya = dict(depo["users/u1/private/device"])

    device.enforce_single_device("u1", "cihaz-b", auth_time=900)  # fırlatmamalı
    assert depo["users/u1/private/device"] == kopya  # yeniden yazılmadı

    # Memo tazelendi: B'nin sonraki istekleri Firestore'a gitmez.
    sayac = _sayan_client(monkeypatch)
    for _ in range(5):
        device.enforce_single_device("u1", "cihaz-b", auth_time=900)
    assert sayac["n"] == 0


def test_onbellek_esitlik_yolunda_okumayi_keser(depo, monkeypatch):
    _sahiplen(depo)
    sayac = _sayan_client(monkeypatch)
    for _ in range(5):
        device.enforce_single_device("u1", "cihaz-a", auth_time=900)
    assert sayac["n"] == 0, "memo varken Firestore'a gidilmemeli"


def test_okuma_hatasi_gecer_ve_YAZMAZ(depo):
    """K5: geçici hata sahipliği ters çeviremez — ne 409 ne sahiplenme."""
    depo["__oku_hata__"] = True
    device.enforce_single_device("u1", "cihaz-a", auth_time=900)  # fırlatmamalı
    assert _kayit(depo) is None


def test_okuma_hatasi_mevcut_kaydi_ezmez(depo):
    """Kayıt A'da, memo boş, Firestore düşük → B geçer ama A'nın kaydı durur."""
    _sahiplen(depo, "cihaz-a")
    device.clear_cache()
    depo["__oku_hata__"] = True
    device.enforce_single_device("u1", "cihaz-b", auth_time=5000)
    assert _kayit(depo)["deviceId"] == "cihaz-a"


def test_firestore_yokken_kilit_atlanir(monkeypatch):
    """Fail-open: altyapı sorunu aboneyi kilitlemez."""
    monkeypatch.setattr(device.firestore_client, "get_client", lambda: None)
    monkeypatch.setattr(device.entitlements, "get_subscription",
                        lambda uid: {"active": True})
    device.clear_cache()
    device.enforce_single_device("u1", "cihaz-a", auth_time=900)  # fırlatmamalı


# ---------------------------------------------------------------------------
# Serbest bırakma ve açık devralma dürüstlüğü
# ---------------------------------------------------------------------------

def test_release_yalniz_sahip_siler(depo):
    _sahiplen(depo, "cihaz-a")
    assert device.release_device("u1", "cihaz-a") == {"released": True}
    assert _kayit(depo) is None
    # Memo düştü: bir sonraki cihaz sessizce sahiplenir, 409 yok.
    device.enforce_single_device("u1", "cihaz-b", auth_time=900)
    assert _kayit(depo)["deviceId"] == "cihaz-b"


def test_release_sahip_degilse_noop_false(depo):
    _sahiplen(depo, "cihaz-a")
    assert device.release_device("u1", "cihaz-b") == {"released": False}
    assert device.release_device("u1", None) == {"released": False}
    assert device.release_device("u1", "") == {"released": False}
    assert _kayit(depo)["deviceId"] == "cihaz-a"


def test_release_kayit_yokken_false(depo):
    assert device.release_device("u1", "cihaz-a") == {"released": False}


def test_claim_client_yokken_false(monkeypatch):
    monkeypatch.setattr(device.firestore_client, "get_client", lambda: None)
    device.clear_cache()
    assert device.claim_device("u1", "cihaz-a", auth_time=900,
                               platform="ios") == {"claimed": False}


def test_claim_yazma_hatasinda_false(depo):
    depo["__yaz_hata__"] = True
    assert device.claim_device("u1", "cihaz-a", auth_time=900,
                               platform="ios") == {"claimed": False}
    assert _kayit(depo) is None


def test_platform_yoksa_kaybedenin_platformu_kalmaz(depo, monkeypatch):
    """Otomatik devralma platform bilmiyorsa (eski istemci, başlık yok)
    KAYBEDENİN platformu kayıtta KALMAZ: kalsaydı A'nın 409 ekranı "öbür
    cihaz" diye A'nın kendi platformunu söylerdi. Bilinmiyor → boş başlık."""
    device.claim_device("u1", "cihaz-a", auth_time=900, platform="ios")
    monkeypatch.setattr(device, "_now", lambda: _t(2000))

    device.enforce_single_device("u1", "cihaz-b", auth_time=1500)  # platform=None

    k = _kayit(depo)
    assert k["deviceId"] == "cihaz-b"
    assert k["platform"] is None
    with pytest.raises(HTTPException) as exc:
        device.enforce_single_device("u1", "cihaz-a", auth_time=900)
    assert exc.value.headers["X-Device-Other-Platform"] == ""


def test_korumali_istegin_platformu_devralmada_yazilir(depo, monkeypatch):
    """36+ istemci her isteğe `X-Device-Platform` koyar; otomatik
    devralma onu yazar ve kaybeden cihaz 409'da KAZANANIN platformunu
    görür (ana yol: B sessizce devralır, A ekranda "iOS cihazında" okur)."""
    device.claim_device("u1", "cihaz-a", auth_time=900, platform="android")
    monkeypatch.setattr(device, "_now", lambda: _t(2000))

    device.enforce_single_device("u1", "cihaz-b", auth_time=1500,
                                 platform="iOS")

    assert _kayit(depo)["platform"] == "iOS"
    with pytest.raises(HTTPException) as exc:
        device.enforce_single_device("u1", "cihaz-a", auth_time=900,
                                     platform="android")
    assert exc.value.headers["X-Device-Other-Platform"] == "iOS"
    assert _kayit(depo)["platform"] == "iOS"  # 409 yazmaz


# ---------------------------------------------------------------------------
# Durum ve yönetici kaçış kapısı
# ---------------------------------------------------------------------------

def test_durum_sorgusu(depo, monkeypatch):
    assert device.device_status("u1", "cihaz-a") == {
        "locked": True, "claimed": False, "this_device": False, "other": None}

    device.claim_device("u1", "cihaz-a", auth_time=900, platform="ios")
    assert device.device_status("u1", "cihaz-a") == {
        "locked": True, "claimed": True, "this_device": True, "other": None}
    assert device.device_status("u1", "cihaz-b") == {
        "locked": True, "claimed": True, "this_device": False,
        "other": {"platform": "ios",
                  "claimedAt": "1970-01-01T00:16:40+00:00"}}

    # Deneme/ücretsiz: kayıt olsa da kilit etkin değil.
    monkeypatch.setattr(device.entitlements, "get_subscription",
                        lambda uid: {"active": False})
    assert device.device_status("u1", "cihaz-b")["locked"] is False


def test_force_release_kaydi_siler_ve_memo_duser(depo):
    _sahiplen(depo, "cihaz-a")
    assert device.force_release("u1") is True
    assert _kayit(depo) is None
    assert device.force_release("u1") is False  # silinecek kayıt yoktu
    device.enforce_single_device("u1", "cihaz-b", auth_time=900)
    assert _kayit(depo)["deviceId"] == "cihaz-b"


def test_force_release_firestore_yokken_firlatir(monkeypatch):
    """Admin "sıfırlandı" sanmasın: altyapı hatası sessiz False değil."""
    monkeypatch.setattr(device.firestore_client, "get_client", lambda: None)
    with pytest.raises(RuntimeError):
        device.force_release("u1")
