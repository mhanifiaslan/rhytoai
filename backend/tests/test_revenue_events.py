"""Gelir defteri (W3): revenueEvents append-only koleksiyonu.

Değişmezler:
- Parasal olaylar (INITIAL_PURCHASE, RENEWAL, TRIAL_CONVERTED,
  NON_RENEWING_PURCHASE, REFUND) deftere yazılır; TRIAL_STARTED yazılmaz.
- Doküman kimliği event.id — aynı olayın tekrarı ikinci kayıt üretmez.
- Atıf dokümanı varsa partnerId damgalanır; yoksa null.
- Defter yazımı düşse bile webhook 200 döner (en-iyi-çaba).
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from core import config

try:
    from main import app
    _APP_IMPORT_ERROR = None
except Exception as exc:  # pragma: no cover - ortama bagli
    app = None
    _APP_IMPORT_ERROR = str(exc)

uygulama_gerekir = pytest.mark.skipif(
    _APP_IMPORT_ERROR is not None,
    reason=f"FastAPI uygulamasi ice aktarilamadi: {_APP_IMPORT_ERROR}",
)


@pytest.fixture()
def sahte(monkeypatch):
    """Yol farkında sahte Firestore: revenueEvents ve attribution ayrışır."""
    monkeypatch.setattr(config, "REVENUECAT_WEBHOOK_SECRET", "anahtar")
    for ad in ("credit_pack", "debit_refund"):
        monkeypatch.setattr(f"api.billing.wallet.{ad}",
                            lambda *a, **k: True)
    monkeypatch.setattr("api.billing.wallet.reset_allowance",
                        lambda uid, exp: None)

    kayit = {"revenue": {}, "attribution": None}

    class SahteDoc:
        def __init__(self, yol):
            self.yol = yol

        def collection(self, ad):
            return SahteKoleksiyon(self.yol + [ad])

        def set(self, data, merge=False):
            if self.yol[0] == "revenueEvents":
                kayit["revenue"][self.yol[1]] = data
            # abonelik yazımları bu testte umursanmaz

        def get(self):
            class Anlik:
                exists = kayit["attribution"] is not None

                @staticmethod
                def to_dict():
                    return kayit["attribution"]
            return Anlik()

    class SahteKoleksiyon:
        def __init__(self, yol):
            self.yol = yol

        def document(self, ad):
            return SahteDoc(self.yol + [ad])

    class SahteClient:
        def collection(self, ad):
            return SahteKoleksiyon([ad])

    monkeypatch.setattr("api.billing.firestore_client.get_client",
                        lambda: SahteClient())
    return kayit


def _gonder(client, event):
    return client.post("/api/v1/billing/revenuecat", json={"event": event},
                       headers={"Authorization": "anahtar"})


_SATIS = {
    "type": "INITIAL_PURCHASE", "app_user_id": "u", "id": "evt-g1",
    "product_id": "rytho_plus_monthly", "store": "PLAY_STORE",
    "price": 4.99, "price_in_purchased_currency": 169.99,
    "currency": "TRY", "country_code": "TR",
    "event_timestamp_ms": 1754300000000,
}


@uygulama_gerekir
def test_abonelik_satisi_deftere_yazilir(sahte):
    with TestClient(app) as client:
        assert _gonder(client, _SATIS).status_code == 200

    kayit = sahte["revenue"]["evt-g1"]
    assert kayit["uid"] == "u"
    assert kayit["eventType"] == "INITIAL_PURCHASE"
    assert kayit["price"] == 4.99
    assert kayit["currency"] == "TRY"
    assert kayit["countryCode"] == "TR"
    assert kayit["partnerId"] is None  # atıf yok — null


@uygulama_gerekir
def test_ayni_olay_tek_dokuman(sahte):
    """Doküman kimliği event.id: tekrar aynı dokümanı ezer, ikinci kayıt yok."""
    with TestClient(app) as client:
        _gonder(client, _SATIS)
        _gonder(client, _SATIS)
    assert len(sahte["revenue"]) == 1


@uygulama_gerekir
def test_deneme_baslangici_defterde_yok(sahte):
    """TRIAL_STARTED'da para el değiştirmez — gelir kaydı üretilmez."""
    with TestClient(app) as client:
        _gonder(client, {**_SATIS, "type": "TRIAL_STARTED", "id": "evt-g2"})
    assert sahte["revenue"] == {}


@uygulama_gerekir
def test_paket_satisi_da_gelir_olayidir(sahte):
    with TestClient(app) as client:
        _gonder(client, {
            "type": "NON_RENEWING_PURCHASE", "app_user_id": "u",
            "id": "evt-g3", "product_id": "rytho_tokens_small",
            "price": 1.99, "currency": "USD"})
    assert sahte["revenue"]["evt-g3"]["eventType"] == "NON_RENEWING_PURCHASE"
    assert sahte["revenue"]["evt-g3"]["productId"] == "rytho_tokens_small"


@uygulama_gerekir
def test_abonelik_iadesi_hem_kapatir_hem_deftere_gecer(sahte):
    with TestClient(app) as client:
        _gonder(client, {**_SATIS, "type": "REFUND", "id": "evt-g4"})
    assert sahte["revenue"]["evt-g4"]["eventType"] == "REFUND"


@uygulama_gerekir
def test_atif_varsa_partner_damgalanir(sahte):
    """W7 öncülü: private/attribution dokümanı varsa partnerId işlenir."""
    sahte["attribution"] = {"code": "ORTAK10", "partnerId": "p-1"}
    with TestClient(app) as client:
        _gonder(client, {**_SATIS, "id": "evt-g5"})
    assert sahte["revenue"]["evt-g5"]["partnerId"] == "p-1"


@uygulama_gerekir
def test_kimliksiz_olay_defteri_atlar_ama_200(sahte):
    with TestClient(app) as client:
        yanit = _gonder(client, {k: v for k, v in _SATIS.items() if k != "id"})
    assert yanit.status_code == 200
    assert sahte["revenue"] == {}
