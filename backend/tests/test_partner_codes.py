"""Ortak kod sistemi (W7) değişmezleri.

- Atıf TEK sefer: ikinci kod 409, sayaç artmaz.
- maxRedemptions/expiry/aktiflik kapıları.
- credit_promo uid başına idempotent (defter kimliği promo-KOD).
- Kod rezervasyonu yarışta düşer (create var olanda hata — usernames deseni).
"""
from __future__ import annotations

import datetime as dt

import pytest

from core import wallet
from services import partner_service


# --- test_wallet.py sahtesinin genişletilmiş kopyası (update/create'li) ---

class SahteAnlik:
    def __init__(self, data):
        self._data = data

    @property
    def exists(self):
        return self._data is not None

    def to_dict(self):
        return dict(self._data) if self._data else {}


class SahteDoc:
    def __init__(self, depo, yol):
        self._depo = depo
        self._yol = yol

    def get(self, transaction=None):
        return SahteAnlik(self._depo.get(self._yol))

    def set(self, data, merge=False):
        mevcut = dict(self._depo.get(self._yol) or {}) if merge else {}
        mevcut.update(data)
        self._depo[self._yol] = mevcut

    def update(self, data):
        mevcut = dict(self._depo.get(self._yol) or {})
        mevcut.update(data)
        self._depo[self._yol] = mevcut

    def create(self, data):
        if self._yol in self._depo:
            raise RuntimeError("already-exists")
        self._depo[self._yol] = dict(data)

    def collection(self, ad):
        return SahteKoleksiyon(self._depo, f"{self._yol}/{ad}")


class SahteKoleksiyon:
    def __init__(self, depo, yol):
        self._depo = depo
        self._yol = yol

    def document(self, ad=None):
        return SahteDoc(self._depo, f"{self._yol}/{ad or 'otomatik'}")


class SahteTransaction:
    def set(self, ref, data):
        ref.set(data)

    def update(self, ref, data):
        ref.update(data)


class SahteClient:
    def __init__(self, depo):
        self._depo = depo

    def collection(self, ad):
        return SahteKoleksiyon(self._depo, ad)

    def transaction(self):
        return SahteTransaction()


@pytest.fixture()
def depo(monkeypatch):
    veriler: dict = {}
    client = SahteClient(veriler)
    monkeypatch.setattr(partner_service.firestore_client, "get_client",
                        lambda: client)
    monkeypatch.setattr(wallet.firestore_client, "get_client",
                        lambda: client)
    monkeypatch.setattr("google.cloud.firestore.transactional", lambda f: f)
    return veriler


def _kod_yaz(depo, kod="ORTAK10", **ek):
    veri = {"partnerId": "p-1", "bonusTokens": 50, "maxRedemptions": None,
            "redemptionCount": 0, "expiresAt": None, "active": True}
    veri.update(ek)
    depo[f"partnerCodes/{kod}"] = veri


def test_kod_kullanimi_atif_ve_bonus(depo, monkeypatch):
    _kod_yaz(depo)
    krediler = []
    monkeypatch.setattr(partner_service.wallet, "credit_promo",
                        lambda uid, kod, m: krediler.append((uid, kod, m)))

    sonuc = partner_service.redeem("u1", "ortak10")  # küçük harf normalize
    assert sonuc == {"code": "ORTAK10", "partnerId": "p-1",
                     "bonusTokens": 50}
    assert depo["users/u1/private/attribution"]["partnerId"] == "p-1"
    assert depo["partnerCodes/ORTAK10"]["redemptionCount"] == 1
    assert krediler == [("u1", "ORTAK10", 50)]


def test_ikinci_kod_409_ve_sayac_artmaz(depo, monkeypatch):
    _kod_yaz(depo, "BIR1")
    _kod_yaz(depo, "IKI2")
    monkeypatch.setattr(partner_service.wallet, "credit_promo",
                        lambda *a: True)
    partner_service.redeem("u1", "BIR1")
    with pytest.raises(partner_service.RedeemError) as h:
        partner_service.redeem("u1", "IKI2")
    assert h.value.status == 409
    assert depo["partnerCodes/IKI2"]["redemptionCount"] == 0


def test_limit_dolunca_400(depo):
    _kod_yaz(depo, "DOLU", maxRedemptions=1, redemptionCount=1)
    with pytest.raises(partner_service.RedeemError) as h:
        partner_service.redeem("u1", "DOLU")
    assert h.value.reason == "exhausted"


def test_suresi_gecmis_ve_pasif_kod(depo):
    _kod_yaz(depo, "ESKI", expiresAt=dt.datetime(
        2020, 1, 1, tzinfo=dt.timezone.utc))
    _kod_yaz(depo, "KAPALI", active=False)
    with pytest.raises(partner_service.RedeemError) as h1:
        partner_service.redeem("u1", "ESKI")
    assert h1.value.reason == "expired"
    with pytest.raises(partner_service.RedeemError) as h2:
        partner_service.redeem("u1", "KAPALI")
    assert h2.value.reason == "inactive"


def test_bicimsiz_kod_400(depo):
    for bozuk in ["ab", "kod boşluk", "çok-türkçe-İ", "x" * 30]:
        with pytest.raises(partner_service.RedeemError) as h:
            partner_service.redeem("u1", bozuk)
        assert h.value.status == 400


def test_credit_promo_idempotent(depo):
    assert wallet.credit_promo("u1", "ORTAK10", 50) is True
    assert wallet.credit_promo("u1", "ORTAK10", 50) is False  # ikinci kez
    assert depo["users/u1/private/wallet"]["purchased"] == 50
    assert depo["users/u1/private/wallet/ledger/promo-ORTAK10"]["type"] == \
        "promo"


def test_kod_rezervasyonu_yarista_duser(depo):
    partner_service.create_code("p-1", "TEKEL", 10, None, None)
    with pytest.raises(partner_service.RedeemError) as h:
        partner_service.create_code("p-2", "TEKEL", 10, None, None)
    assert h.value.reason == "code_taken"
    assert depo["partnerCodes/TEKEL"]["partnerId"] == "p-1"
