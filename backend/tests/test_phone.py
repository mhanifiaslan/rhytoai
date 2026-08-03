"""Telefon eşleme kaydının değişmezleri (Revize R2).

Güven zinciri testin merkezinde: numara İSTEMCİDEN alınmaz, doğrulanmış
token claim'inden gelir. Uç seviyesindeki testler bunu tutuyor — gövdeyle
numara gönderen bir istemci HİÇBİR ŞEY kaydettiremez.
"""
from __future__ import annotations

import pytest

from services import phone_service


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
    veriler: dict = {}
    monkeypatch.setattr(phone_service.firestore_client, "get_client",
                        lambda: _SahteClient(veriler))
    return veriler


_NUMARA = "+905551112233"


def _hash(n=_NUMARA):
    return phone_service.phone_hash(n)


def test_kayit_iki_yere_yazilir(depo):
    phone_service.sync_phone("u1", _NUMARA)

    assert depo[f"phoneHashes/{_hash()}"]["uid"] == "u1"
    assert depo["users/u1/private/phone"]["hash"] == _hash()


def test_ham_numara_hicbir_yere_yazilmaz(depo):
    """Firestore'a ham numara girmez — Firebase Auth'taki kopya yeter,
    ikincisi yeni bir sizinti yuzeyi olurdu."""
    phone_service.sync_phone("u1", _NUMARA)

    for yol, veri in depo.items():
        for deger in veri.values():
            assert _NUMARA not in str(deger), f"{yol} ham numara iceriyor"


def test_ayni_kullanici_idempotent(depo):
    phone_service.sync_phone("u1", _NUMARA)
    sonuc = phone_service.sync_phone("u1", _NUMARA)
    assert sonuc == {"linked": True, "changed": False}


def test_baska_hesaba_bagli_numara_reddedilir(depo):
    """Bir numara TEK hesaba baglanir; aksi halde rehber eslesmesi ayni
    numara icin iki kisi dondururdu."""
    phone_service.sync_phone("u1", _NUMARA)

    with pytest.raises(phone_service.PhoneTakenError):
        phone_service.sync_phone("u2", _NUMARA)

    assert depo[f"phoneHashes/{_hash()}"]["uid"] == "u1"


def test_numara_degisince_eski_hash_serbest_kalir(depo):
    """Kullanici adi deseninin aynisi: eski kayit sarkarsa numaranin yeni
    sahibi kaydolamaz."""
    phone_service.sync_phone("u1", _NUMARA)
    yeni = "+905559998877"
    phone_service.sync_phone("u1", yeni)

    assert f"phoneHashes/{_hash()}" not in depo
    assert depo[f"phoneHashes/{_hash(yeni)}"]["uid"] == "u1"
    assert depo["users/u1/private/phone"]["hash"] == _hash(yeni)


def test_release_hash_dizinini_temizler(depo):
    phone_service.sync_phone("u1", _NUMARA)
    phone_service.release_phone("u1")
    assert f"phoneHashes/{_hash()}" not in depo


def test_hash_normalize_bosluk(depo):
    assert phone_service.phone_hash(" +905551112233 ") == _hash()
