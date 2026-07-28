"""Faz 2 testleri: yetki katmani, kotalar ve RevenueCat webhook'u.

Calistirma:  .venv\\Scripts\\python.exe -m pytest tests/test_entitlements.py -q
"""
import datetime as dt

import pytest
from fastapi.testclient import TestClient

from core import config, entitlements

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

DOGUM = {"name": "Ada", "year": 1994, "month": 8, "day": 11,
         "hour": 9, "minute": 30, "city": "Izmir"}


@pytest.fixture(autouse=True)
def zorlamayi_kapat(monkeypatch):
    """FORCE_PLUS acikken tum kapilar acilir; testler kapali varsayar."""
    monkeypatch.setattr(entitlements, "FORCE_PLUS", False)


def _basliklar(etiket: str) -> dict:
    return {"Authorization": f"Bearer test-{etiket}"}


# --------------------------------------------------------------------------
# Abonelik durumu
# --------------------------------------------------------------------------

def test_firestore_yokken_abone_sayilmaz(monkeypatch):
    """Guvenli taraf ucretsizdir: durum okunamiyorsa ucretli icerik acilmaz."""
    monkeypatch.setattr(entitlements.firestore_client, "get_client", lambda: None)
    assert entitlements.is_subscriber("kimse") is False


def test_suresi_gecmis_abonelik_aktif_sayilmaz(monkeypatch):
    gecmis = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=1)
    monkeypatch.setattr(entitlements, "get_subscription",
                        lambda uid: {"active": False, "expired": True})
    assert entitlements.is_subscriber("x") is False


def test_force_plus_tum_kapilari_acar(monkeypatch):
    """Sadece gelistirme icin; uretimde 0 olmali."""
    monkeypatch.setattr(entitlements, "FORCE_PLUS", True)
    assert entitlements.is_subscriber("kimse") is True


# --------------------------------------------------------------------------
# Ucretli uclar
# --------------------------------------------------------------------------

@uygulama_gerekir
@pytest.mark.parametrize("yol,govde", [
    ("/api/v1/reports/daily", DOGUM),
    ("/api/v1/reports/natal", DOGUM),
    ("/api/v1/reports/bazi", DOGUM),
    ("/api/v1/reports/dyad", {"friend_uid": "arkadas"}),
])
def test_ucretsiz_kullanici_ucretli_uca_giremez(monkeypatch, yol, govde):
    monkeypatch.setattr(entitlements, "is_subscriber", lambda uid: False)

    with TestClient(app) as client:
        response = client.post(yol, json=govde, headers=_basliklar(yol))

    assert response.status_code == entitlements.PAYWALL_STATUS
    assert "Rytho+" in response.json()["detail"]


@uygulama_gerekir
def test_burc_yorumu_ucretsiz_kalir(monkeypatch):
    """Ucretsiz katmanin omurgasi paywall'in arkasina DUSMEMELI."""
    monkeypatch.setattr(entitlements, "is_subscriber", lambda uid: False)

    with TestClient(app) as client:
        response = client.get("/api/v1/reports/horoscope/leo",
                              headers=_basliklar("bedava"))

    assert response.status_code == 200


# --------------------------------------------------------------------------
# Gunluk kotalar
# --------------------------------------------------------------------------

@uygulama_gerekir
def test_sohbet_kotasi_dolunca_paywall(monkeypatch):
    monkeypatch.setattr(entitlements, "is_subscriber", lambda uid: False)

    kullanilan = {"n": 0}

    def sahte_kota(uid, key, limit):
        assert key == "chat"
        kullanilan["n"] += 1
        return kullanilan["n"] <= limit

    monkeypatch.setattr(entitlements, "consume_quota", sahte_kota)
    monkeypatch.setattr("services.gemini_service.chat", lambda h, m: "merhaba")

    with TestClient(app) as client:
        for i in range(entitlements.FREE_CHAT_PER_DAY):
            response = client.post("/api/v1/chat", json={"message": f"selam {i}"},
                                   headers=_basliklar("kota"))
            assert response.status_code == 200, f"{i}. mesaj reddedildi"

        response = client.post("/api/v1/chat", json={"message": "bir tane daha"},
                               headers=_basliklar("kota"))

    assert response.status_code == entitlements.PAYWALL_STATUS
    assert "Rytho+" in response.json()["detail"]


@uygulama_gerekir
def test_abone_sohbette_kotaya_takilmaz(monkeypatch):
    monkeypatch.setattr(entitlements, "is_subscriber", lambda uid: True)
    monkeypatch.setattr(entitlements, "consume_quota",
                        lambda *a: pytest.fail("Abonede kota dusulmemeli"))
    monkeypatch.setattr("services.gemini_service.chat", lambda h, m: "merhaba")

    with TestClient(app) as client:
        for i in range(entitlements.FREE_CHAT_PER_DAY + 3):
            response = client.post("/api/v1/chat", json={"message": f"m{i}"},
                                   headers=_basliklar("abone"))
            assert response.status_code == 200


def test_kota_gun_degisince_sifirlanir(monkeypatch):
    """Sayac dokumandaki tarihe bagli; gun degisince bastan baslar."""
    kayit = {"date": "2020-01-01", "chat": 99}

    class SahteDoc:
        exists = True

        @staticmethod
        def to_dict():
            return kayit

    class SahteRef:
        @staticmethod
        def get():
            return SahteDoc()

        @staticmethod
        def set(data):
            kayit.clear()
            kayit.update(data)

    monkeypatch.setattr(entitlements, "_private_doc", lambda uid, name: SahteRef())

    assert entitlements.consume_quota("u", "chat", 5) is True
    assert kayit["date"] == dt.date.today().isoformat()
    assert kayit["chat"] == 1


# --------------------------------------------------------------------------
# RevenueCat webhook
# --------------------------------------------------------------------------

@uygulama_gerekir
def test_webhook_gizli_anahtarsiz_calismaz(monkeypatch):
    """Anahtar tanimsizken uc acik kalirsa herkes kendine abonelik yazabilirdi."""
    monkeypatch.setattr(config, "REVENUECAT_WEBHOOK_SECRET", None)

    with TestClient(app) as client:
        response = client.post("/api/v1/billing/revenuecat",
                               json={"event": {"type": "RENEWAL", "app_user_id": "u"}})
    assert response.status_code == 503


@uygulama_gerekir
def test_webhook_yanlis_anahtari_reddeder(monkeypatch):
    monkeypatch.setattr(config, "REVENUECAT_WEBHOOK_SECRET", "dogru-anahtar")

    with TestClient(app) as client:
        response = client.post("/api/v1/billing/revenuecat",
                               json={"event": {"type": "RENEWAL", "app_user_id": "u"}},
                               headers={"Authorization": "yanlis-anahtar"})
    assert response.status_code == 401


@uygulama_gerekir
def test_webhook_iptali_erisimi_hemen_kesmez(monkeypatch):
    """RevenueCat'te CANCELLATION 'yenilenmeyecek' demektir, 'bitti' degil.

    Kullanici odedigi donemin sonuna kadar erisimini korumali.
    """
    monkeypatch.setattr(config, "REVENUECAT_WEBHOOK_SECRET", "anahtar")

    yazilan: dict = {}

    class SahteDoc:
        @staticmethod
        def set(data):
            yazilan.update(data)

    class SahteKoleksiyon:
        def document(self, _):
            return self

        def collection(self, _):
            return self

        def set(self, data):
            yazilan.update(data)

    class SahteClient:
        def collection(self, _):
            return SahteKoleksiyon()

    monkeypatch.setattr("api.billing.firestore_client.get_client", lambda: SahteClient())

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/billing/revenuecat",
            json={"event": {"type": "CANCELLATION", "app_user_id": "u",
                            "product_id": "rytho_plus_yearly",
                            "expiration_at_ms": 4102444800000}},
            headers={"Authorization": "anahtar"},
        )

    assert response.status_code == 200
    assert yazilan["active"] is True
    assert yazilan["willRenew"] is False
    assert SahteDoc  # kullanilmayan yardimci uyari vermesin


@uygulama_gerekir
def test_webhook_suresi_dolunca_kapatir(monkeypatch):
    monkeypatch.setattr(config, "REVENUECAT_WEBHOOK_SECRET", "anahtar")

    yazilan: dict = {}

    class SahteKoleksiyon:
        def document(self, _):
            return self

        def collection(self, _):
            return self

        def set(self, data):
            yazilan.update(data)

    class SahteClient:
        def collection(self, _):
            return SahteKoleksiyon()

    monkeypatch.setattr("api.billing.firestore_client.get_client", lambda: SahteClient())

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/billing/revenuecat",
            json={"event": {"type": "EXPIRATION", "app_user_id": "u"}},
            headers={"Authorization": "anahtar"},
        )

    assert response.status_code == 200
    assert yazilan["active"] is False


@uygulama_gerekir
def test_webhook_app_user_id_olmadan_reddeder(monkeypatch):
    monkeypatch.setattr(config, "REVENUECAT_WEBHOOK_SECRET", "anahtar")

    with TestClient(app) as client:
        response = client.post("/api/v1/billing/revenuecat",
                               json={"event": {"type": "RENEWAL"}},
                               headers={"Authorization": "anahtar"})
    assert response.status_code == 400
