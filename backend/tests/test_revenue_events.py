"""Gelir defteri (W3): revenueEvents append-only koleksiyonu.

Değişmezler:
- Parasal olaylar (INITIAL_PURCHASE, RENEWAL, TRIAL_CONVERTED,
  NON_RENEWING_PURCHASE, REFUND) `monetary=True` ile; parasal olmayanlar
  (TRIAL_STARTED, CANCELLATION, …) `monetary=False, price=0` ile yazılır (AD5).
- `environment` her olayda (varsayılan PRODUCTION); parasal olay
  `private/revenueTotals.{ENV}`i Increment ile artırır; abonelik yazımı
  `users/{uid}.plan` aynasını günceller.
- Doküman kimliği event.id — aynı olayın tekrarı ikinci kayıt üretmez.
- Atıf dokümanı varsa partnerId damgalanır; yoksa null.
- Defter yazımı düşse bile webhook 200 döner (en-iyi-çaba).
"""
from __future__ import annotations

import datetime as dt

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
def test_deneme_baslangici_parasal_degil(sahte):
    """TRIAL_STARTED'da para el değiştirmez — AD5 ile kayıt yine düşer ama
    `monetary=False, price=0`: zaman çizelgesinde görünür, gelire girmez."""
    with TestClient(app) as client:
        _gonder(client, {**_SATIS, "type": "TRIAL_STARTED", "id": "evt-g2",
                         "period_type": "TRIAL"})
    kayit = sahte["revenue"]["evt-g2"]
    assert kayit["monetary"] is False
    assert kayit["price"] == 0
    assert kayit["priceInPurchasedCurrency"] == 0
    assert kayit["periodType"] == "TRIAL"
    assert kayit["isTrial"] is True


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


# ---------------------------------------------------------------------------
# AD5: ortam, parasal olmayan olaylar, transfer, toplamlar, plan aynası —
# yol-farkında paylaşımlı sahte ile (private/revenueTotals + users/{uid})
# ---------------------------------------------------------------------------

@pytest.fixture()
def depo(monkeypatch):
    from _sahte_firestore import SahteFirestore
    monkeypatch.setattr(config, "REVENUECAT_WEBHOOK_SECRET", "anahtar")
    for ad in ("credit_pack", "debit_refund"):
        monkeypatch.setattr(f"api.billing.wallet.{ad}", lambda *a, **k: True)
    monkeypatch.setattr("api.billing.wallet.reset_allowance",
                        lambda uid, exp: None)
    # `event_id` anahtar sozcugu: devrin tekrar korumasi artik deftere bagli
    # (bkz. core/wallet.transfer_wallet). Sahte onu KABUL ETMELI, yoksa
    # gercek imza degisikligi burada TypeError'a donusur.
    monkeypatch.setattr("api.billing.wallet.transfer_wallet",
                        lambda c, s, t, **k: None)
    sahte = SahteFirestore({"users/u": {"displayName": "U"},
                            "users/hedef": {"displayName": "H"}})
    monkeypatch.setattr("api.billing.firestore_client.get_client",
                        lambda: sahte)
    return sahte


@uygulama_gerekir
def test_ortam_alani_ve_toplamlar(depo):
    with TestClient(app) as client:
        _gonder(client, {**_SATIS, "id": "p1"})                     # ortamsız → PRODUCTION
        _gonder(client, {**_SATIS, "id": "s1", "environment": "sandbox",
                         "type": "RENEWAL", "price": 2.0})
        _gonder(client, {**_SATIS, "id": "s2", "environment": "SANDBOX",
                         "type": "REFUND", "price": 2.0})
    assert depo.docs["revenueEvents/p1"]["environment"] == "PRODUCTION"
    assert depo.docs["revenueEvents/s1"]["environment"] == "SANDBOX"
    t = depo.docs["users/u/private/revenueTotals"]
    assert t["PRODUCTION"] == {"grossUsd": 4.99, "events": 1}
    assert t["SANDBOX"] == {"grossUsd": 2.0, "refundsUsd": 2.0, "events": 2}


@uygulama_gerekir
def test_parasal_olmayan_olay_deftere_girer_toplama_girmez(depo):
    with TestClient(app) as client:
        _gonder(client, {**_SATIS, "type": "CANCELLATION", "id": "c1",
                         "cancel_reason": "UNSUBSCRIBE",
                         "expiration_at_ms": 4102444800000})
        _gonder(client, {**_SATIS, "type": "BILLING_ISSUE", "id": "b1"})
    c = depo.docs["revenueEvents/c1"]
    assert c["monetary"] is False and c["price"] == 0
    assert c["cancelReason"] == "UNSUBSCRIBE"
    assert c["expirationAt"].year == 2100
    assert depo.docs["revenueEvents/b1"]["eventType"] == "BILLING_ISSUE"
    assert "users/u/private/revenueTotals" not in depo.docs
    # Abonelik "yenilenmeyecek ama açık": plan aynası hâlâ plus.
    assert depo.docs["users/u"]["plan"] == "plus"
    assert depo.docs["users/u"]["planProduct"] == "rytho_plus_monthly"


@uygulama_gerekir
def test_plan_aynasi_free_trial_plus(depo):
    with TestClient(app) as client:
        _gonder(client, {**_SATIS, "type": "TRIAL_STARTED", "id": "t1",
                         "period_type": "TRIAL",
                         "expiration_at_ms": 4102444800000})
        assert depo.docs["users/u"]["plan"] == "trial"
        _gonder(client, {**_SATIS, "type": "TRIAL_CONVERTED", "id": "t2",
                         "expiration_at_ms": 4102444800000})
        assert depo.docs["users/u"]["plan"] == "plus"
        _gonder(client, {**_SATIS, "type": "EXPIRATION", "id": "x1"})
        assert depo.docs["users/u"]["plan"] == "free"
        assert depo.docs["users/u"]["planAt"]
        # Anonim kimlik: users dokümanı yok → hayalet doküman ÜRETİLMEZ.
        _gonder(client, {**_SATIS, "app_user_id": "$RCAnonymousID:zzz", "id": "a1"})
    assert "users/$RCAnonymousID:zzz" not in depo.docs
    assert depo.docs["revenueEvents/a1"]["uid"] == "$RCAnonymousID:zzz"


@uygulama_gerekir
def test_transfer_hedef_basina_kayit_ve_plan(depo):
    depo.docs["users/$RCAnonymousID:abc/private/subscription"] = {
        "active": True, "productId": "rytho_plus_monthly",
        "expiresAt": dt.datetime(2100, 1, 1, tzinfo=dt.timezone.utc)}
    depo.docs["users/$RCAnonymousID:abc"] = {"plan": "plus"}
    with TestClient(app) as client:
        yanit = _gonder(client, {
            "type": "TRANSFER", "id": "tr1",
            "transferred_from": ["$RCAnonymousID:abc"],
            "transferred_to": ["hedef"]})
    assert yanit.status_code == 200
    k = depo.docs["revenueEvents/tr1-hedef"]
    assert k["uid"] == "hedef" and k["eventType"] == "TRANSFER"
    assert k["monetary"] is False
    assert depo.docs["users/hedef"]["plan"] == "plus"
    assert depo.docs["users/$RCAnonymousID:abc"]["plan"] == "free"


def test_plan_from_kurallari():
    from api import billing
    gelecek = dt.datetime(2100, 1, 1, tzinfo=dt.timezone.utc)
    gecmis = dt.datetime(2000, 1, 1, tzinfo=dt.timezone.utc)
    assert billing._plan_from(None) == "free"
    assert billing._plan_from({"active": False}) == "free"
    assert billing._plan_from({"active": True, "expiresAt": gecmis}) == "free"
    assert billing._plan_from({"active": True, "expiresAt": gelecek}) == "plus"
    assert billing._plan_from({"active": True, "expiresAt": gelecek,
                               "isTrial": True}) == "trial"
    assert billing._plan_from({"active": True}) == "plus"   # bitişsiz kayıt
