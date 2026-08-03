"""Tek cihaz kilidinin değişmezleri (Revize R2).

En önemli ikisi:

* **Ücretsiz kullanıcı HİÇ etkilenmez** — gereksinim "aboneler" diyor;
  yanlışlıkla herkese uygulanan bir kilit, ücretsiz katmanı sessizce kırar.
* **Başlıksız istek kilitlenmez** — eski uygulama sürümleri kimlik
  göndermez; onları kilitlemek güncelleme yayılana kadar tüm aboneleri
  kırmak olurdu.
"""
from __future__ import annotations

import pytest
from fastapi import HTTPException

from core import device


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
        return _SahteAnlik(self._depo.get(self._yol))

    def set(self, data, merge=False):
        mevcut = dict(self._depo.get(self._yol) or {}) if merge else {}
        mevcut.update(data)
        self._depo[self._yol] = mevcut


class _SahteKoleksiyon:
    def __init__(self, depo, yol):
        self._depo = depo
        self._yol = yol

    def document(self, ad):
        yeni = f"{self._yol}/{ad}"
        return _SahteDocVeKoleksiyon(self._depo, yeni)


class _SahteDocVeKoleksiyon(_SahteDoc):
    def collection(self, ad):
        return _SahteKoleksiyon(self._depo, f"{self._yol}/{ad}")


class _SahteClient:
    def __init__(self, depo):
        self._depo = depo

    def collection(self, ad):
        return _SahteKoleksiyon(self._depo, ad)


@pytest.fixture()
def depo(monkeypatch):
    veriler: dict = {}
    monkeypatch.setattr(device.firestore_client, "get_client",
                        lambda: _SahteClient(veriler))
    monkeypatch.setattr(device.entitlements, "is_subscriber",
                        lambda uid: True)
    device.clear_cache()
    yield veriler
    device.clear_cache()


def _kayit(depo, uid="u1"):
    return depo.get(f"users/{uid}/private/device")


def test_ucretsiz_kullanici_hic_etkilenmez(depo, monkeypatch):
    monkeypatch.setattr(device.entitlements, "is_subscriber",
                        lambda uid: False)
    # Farklı kimlikle bile istek geçer ve HİÇBİR kayıt yazılmaz.
    device.enforce_single_device("u1", "cihaz-a")
    device.enforce_single_device("u1", "cihaz-b")
    assert _kayit(depo) is None


def test_basliksiz_istek_kilitlenmez(depo):
    """Eski sürüm istemciler kimlik göndermez; kilitlemek onları kırardı."""
    device.enforce_single_device("u1", None)
    device.enforce_single_device("u1", "")
    assert _kayit(depo) is None


def test_ilk_cihaz_sessizce_sahiplenir(depo):
    device.enforce_single_device("u1", "cihaz-a")
    assert _kayit(depo)["deviceId"] == "cihaz-a"


def test_ayni_cihaz_gecer(depo):
    device.enforce_single_device("u1", "cihaz-a")
    device.enforce_single_device("u1", "cihaz-a")  # fırlatmamalı


def test_farkli_cihaz_409_ve_baslik(depo):
    device.enforce_single_device("u1", "cihaz-a")

    with pytest.raises(HTTPException) as exc:
        device.enforce_single_device("u1", "cihaz-b")

    assert exc.value.status_code == 409
    assert exc.value.headers["X-Device-Conflict"] == "1"
    # Kayıt DEĞİŞMEDİ: 409 devralma değildir.
    assert _kayit(depo)["deviceId"] == "cihaz-a"


def test_devralma_eski_cihazi_dislar(depo):
    """WhatsApp modeli: yeni cihaz claim eder, eski cihaz 409 almaya başlar."""
    device.enforce_single_device("u1", "cihaz-a")
    device.claim_device("u1", "cihaz-b", platform="android")

    device.enforce_single_device("u1", "cihaz-b")  # yeni geçer
    with pytest.raises(HTTPException):
        device.enforce_single_device("u1", "cihaz-a")  # eski düşer


def test_onbellek_firestore_okumasini_keser(depo, monkeypatch):
    """60 sn'lik süreç içi önbellek: ardışık isteklerde +1 okuma binmez."""
    device.enforce_single_device("u1", "cihaz-a")

    sayac = {"n": 0}
    orijinal = device.firestore_client.get_client

    def sayan():
        sayac["n"] += 1
        return orijinal()

    monkeypatch.setattr(device.firestore_client, "get_client", sayan)
    for _ in range(5):
        device.enforce_single_device("u1", "cihaz-a")
    assert sayac["n"] == 0, "önbellek varken Firestore'a gidilmemeli"


def test_firestore_yokken_kilit_atlanir(monkeypatch):
    """Fail-open: altyapı sorunu aboneyi kilitlemez."""
    monkeypatch.setattr(device.firestore_client, "get_client", lambda: None)
    monkeypatch.setattr(device.entitlements, "is_subscriber",
                        lambda uid: True)
    device.clear_cache()
    device.enforce_single_device("u1", "cihaz-a")  # fırlatmamalı


def test_durum_sorgusu(depo):
    assert device.device_status("u1", "cihaz-a") == {
        "claimed": False, "this_device": False}

    device.claim_device("u1", "cihaz-a")
    assert device.device_status("u1", "cihaz-a") == {
        "claimed": True, "this_device": True}
    assert device.device_status("u1", "cihaz-b") == {
        "claimed": True, "this_device": False}
