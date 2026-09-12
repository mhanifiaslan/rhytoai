"""Admin kullanıcı uçlarının bekçileri (AP-turu).

Değişmezler:
- Uçlar admin claim'siz 403 (varlık sızdırmayan jenerik mesaj zaten
  require_admin'de).
- Liste satırı ve 360, fcmToken DEĞERİNİ asla döndürmez (hasPush bool).
- 360 sohbet/hafıza/günlük İÇERİĞİ taşımaz — yalnız sayılar.
- Elle kredi: gerekçesiz/pozitif-olmayan tutar 422; başarılı yol defteri
  VE denetim izini birlikte yazar.
"""
from __future__ import annotations

import datetime as dt

import pytest
from fastapi.testclient import TestClient

from core import config
from services import admin_service, search_mirror

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


from _sahte_firestore import SahteFirestore  # noqa: E402


_SIMDI = dt.datetime.now(dt.timezone.utc)


@pytest.fixture()
def depo(monkeypatch):
    sahte = SahteFirestore()
    sahte.docs.update({
        "users/u1": {"displayName": "Ayşe", "email": "ayse@ornek.com",
                     "username": "ayse", "sunSign": "leo",
                     **search_mirror.compute({"displayName": "Ayşe",
                                              "email": "ayse@ornek.com",
                                              "username": "ayse"}),
                     "createdAt": _SIMDI, "lastSeenDaily": "2026-08-29",
                     "streakCount": 4, "language": "tr",
                     "timezone": "Europe/Istanbul", "platform": "android",
                     "onboardingCompleted": True, "fcmToken": "GIZLI-TOKEN",
                     "birthDate": "1990-01-01"},
        "users/u2": {"displayName": "Erkan", "email": "erkan@ornek.com",
                     "createdAt": _SIMDI - dt.timedelta(days=3),
                     **search_mirror.compute({"displayName": "Erkan",
                                              "email": "erkan@ornek.com"})},
        "users/u1/private/subscription": {"active": True,
                                          "productId": "rytho_plus_monthly"},
        "users/u1/private/notifications": {"dailyLastSent": "2026-08-29",
                                           "dailyTheme": "inner",
                                           "dailyBody": "GIZLI GOVDE"},
        "users/u1/private/wallet/ledger/l1": {"type": "debit",
                                              "feature": "chat", "amount": 1,
                                              "at": _SIMDI},
        "users/u1/conversations/c1": {"messageCount": 3},
        "users/u1/conversations/c1/messages/m1": {"text": "GIZLI MESAJ"},
        "users/u1/friends/f1": {"status": "accepted"},
        "revenueEvents/e1": {"uid": "u1", "eventType": "INITIAL_PURCHASE",
                             "price": 4.99, "at": _SIMDI},
    })
    monkeypatch.setattr(
        "services.admin_service.firestore_client.get_client", lambda: sahte)
    monkeypatch.setattr(admin_service.wallet, "get_wallet",
                        lambda uid: {"allowance": 0, "purchased": 30,
                                     "monthly_allowance": 300,
                                     "allowance_resets_at": None,
                                     "costs": {}})
    return sahte


def test_liste_sekli_ve_token_sizmaz(depo):
    sonuc = admin_service.list_users()
    assert sonuc["mode"] == "filter" and sonuc["nextCursor"] is None
    satirlar = sonuc["users"]
    assert len(satirlar) == 2
    ayse = next(s for s in satirlar if s["uid"] == "u1")
    assert ayse["hasPush"] is True
    assert "fcmToken" not in ayse
    assert ayse["platform"] == "android"
    # createdAt desc: u1 (bugün) önce
    assert satirlar[0]["uid"] == "u1"


def test_liste_onek_aramasi(depo):
    """Arama modu: ayna alanında önek (AD4) — tam tarama yok."""
    sonuc = admin_service.list_users(q="Erk", alan="ad")
    assert sonuc["mode"] == "search"
    assert [s["uid"] for s in sonuc["users"]] == ["u2"]
    assert admin_service.list_users(q="yok")["users"] == []


def test_360_sekli_mahremiyet_cizgisi(depo):
    detay = admin_service.user_360("u1")
    assert detay is not None
    assert detay["profile"]["hasPush"] is True
    assert "fcmToken" not in detay["profile"]
    assert detay["subscription"]["productId"] == "rytho_plus_monthly"
    assert detay["counts"]["conversations"] == 1
    assert detay["counts"]["friends"] == 1
    assert detay["ledger"][0]["type"] == "debit"
    assert detay["revenueEvents"][0]["eventType"] == "INITIAL_PURCHASE"
    # Bildirim META'sı: gövde metni DÖNMEZ, LastSent/tema döner.
    assert detay["notifications"]["dailyLastSent"] == "2026-08-29"
    assert "dailyBody" not in detay["notifications"]
    # İçerik hiçbir anahtarda yok.
    duz = str(detay)
    assert "GIZLI MESAJ" not in duz
    assert "GIZLI GOVDE" not in duz
    assert "GIZLI-TOKEN" not in duz


def test_360_bilinmeyen_kullanici_none(depo):
    assert admin_service.user_360("yok") is None


# ---------------------------------------------------------------------------
# Uç katmanı
# ---------------------------------------------------------------------------

@uygulama_gerekir
def test_ucler_claim_ister(monkeypatch):
    monkeypatch.setattr(config, "DEV_MODE", True)
    monkeypatch.setattr(config, "DEV_ADMIN", False)
    with TestClient(app) as client:
        for yol in ("/api/v1/admin/users", "/api/v1/admin/users/u1",
                    "/api/v1/admin/usage", "/api/v1/admin/notify-runs",
                    "/api/v1/admin/audit", "/api/v1/admin/economics"):
            assert client.get(yol).status_code == 403, yol
        assert client.post("/api/v1/admin/users/u1/credit",
                           json={"amount": 5, "reason": "test"}
                           ).status_code == 403
        assert client.post("/api/v1/admin/users/u1/disable",
                           json={"disabled": True, "reason": "test"}
                           ).status_code == 403
        assert client.request("DELETE", "/api/v1/admin/users/u1",
                              json={"confirm": "SIL", "reason": "test"}
                              ).status_code == 403


@uygulama_gerekir
def test_kredi_dogrulama_422(monkeypatch, depo):
    monkeypatch.setattr(config, "DEV_MODE", True)
    monkeypatch.setattr(config, "DEV_ADMIN", True)
    with TestClient(app) as client:
        # Gerekçesiz → 422 (zorunlu alan).
        r1 = client.post("/api/v1/admin/users/u1/credit",
                         json={"amount": 5})
        # Sıfır/negatif tutar → 422 (gt=0).
        r2 = client.post("/api/v1/admin/users/u1/credit",
                         json={"amount": 0, "reason": "sebep var"})
    assert r1.status_code == 422
    assert r2.status_code == 422


@uygulama_gerekir
def test_kredi_basarili_defter_ve_audit(monkeypatch, depo):
    monkeypatch.setattr(config, "DEV_MODE", True)
    monkeypatch.setattr(config, "DEV_ADMIN", True)

    verilen: list = []
    monkeypatch.setattr(admin_service.wallet, "credit_admin",
                        lambda uid, amount, reason, admin_uid:
                        verilen.append((uid, amount, reason, admin_uid)))
    # Denetim izi api.admin'in kendi istemcisiyle yazılır.
    monkeypatch.setattr("api.admin.firestore_client.get_client",
                        lambda: depo)

    with TestClient(app) as client:
        yanit = client.post("/api/v1/admin/users/u1/credit",
                            json={"amount": 50,
                                  "reason": "paket gelmedi, telafi"})

    assert yanit.status_code == 200
    assert verilen == [("u1", 50, "paket gelmedi, telafi", "dev-user")]
    izler = [v for k, v in depo.docs.items() if k.startswith("adminAudit/")]
    assert len(izler) == 1
    assert izler[0]["action"] == "user.credit"
    assert izler[0]["targetUid"] == "u1"
    assert izler[0]["params"]["reason"] == "paket gelmedi, telafi"


# ---------------------------------------------------------------------------
# Yönetim eylemleri (AP2): devre dışı bırak + sil emniyetleri
# ---------------------------------------------------------------------------

class _SahteFbAuth:
    def __init__(self):
        self.guncellenen = []
        self.revoke_edilen = []

    def update_user(self, uid, disabled=None):
        self.guncellenen.append((uid, disabled))

    def revoke_refresh_tokens(self, uid):
        self.revoke_edilen.append(uid)

    class _K:
        disabled = False

    def get_user(self, uid):
        return self._K()


@uygulama_gerekir
def test_disable_akisi_ve_kendini_koruma(monkeypatch, depo):
    monkeypatch.setattr(config, "DEV_MODE", True)
    monkeypatch.setattr(config, "DEV_ADMIN", True)
    sahte_auth = _SahteFbAuth()
    import firebase_admin
    monkeypatch.setattr(firebase_admin, "auth", sahte_auth, raising=False)
    import sys
    monkeypatch.setitem(sys.modules, "firebase_admin.auth", sahte_auth)
    monkeypatch.setattr("api.admin.firestore_client.get_client",
                        lambda: depo)

    with TestClient(app) as client:
        tamam = client.post("/api/v1/admin/users/u1/disable",
                            json={"disabled": True, "reason": "kotu kullanim"})
        kendisi = client.post("/api/v1/admin/users/dev-user/disable",
                              json={"disabled": True, "reason": "x-y-z"})
        gerekcesiz = client.post("/api/v1/admin/users/u1/disable",
                                 json={"disabled": True})

    assert tamam.status_code == 200
    assert sahte_auth.guncellenen == [("u1", True)]
    assert sahte_auth.revoke_edilen == ["u1"]
    assert kendisi.status_code == 400
    assert gerekcesiz.status_code == 422
    izler = [v for k, v in depo.docs.items() if k.startswith("adminAudit/")]
    assert [i["action"] for i in izler] == ["user.disable"]


@uygulama_gerekir
def test_silme_emniyetleri_ve_akisi(monkeypatch, depo):
    monkeypatch.setattr(config, "DEV_MODE", True)
    monkeypatch.setattr(config, "DEV_ADMIN", True)
    monkeypatch.setattr("api.admin.firestore_client.get_client",
                        lambda: depo)

    silinen = []
    from services import account_service
    monkeypatch.setattr(account_service, "delete_account",
                        lambda uid: silinen.append(uid) or
                        type("R", (), {"__dict__": {"ok": True}})())

    with TestClient(app) as client:
        onaysiz = client.request("DELETE", "/api/v1/admin/users/u1",
                                 json={"confirm": "sil", "reason": "test-sil"})
        kendisi = client.request("DELETE", "/api/v1/admin/users/dev-user",
                                 json={"confirm": "SIL", "reason": "test-sil"})
        tamam = client.request("DELETE", "/api/v1/admin/users/u1",
                               json={"confirm": "SIL", "reason": "test-sil"})

    assert onaysiz.status_code == 400
    assert kendisi.status_code == 400
    assert tamam.status_code == 200
    assert silinen == ["u1"]
    izler = [v for k, v in depo.docs.items() if k.startswith("adminAudit/")]
    assert [i["action"] for i in izler] == ["user.delete"]
    assert izler[0]["params"]["email"] == "ayse@ornek.com"


def test_economics_marj_matematigi(depo, monkeypatch):
    """Kâr = gelir × 0,85 − AI maliyeti; iade negatif; paylaşımlı üretim
    kullanıcıya yazılmaz ama toplamda görünür — kaynak adminEconomics
    rollup'ı (AD7), canlı tarama YOK (usageEvents/revenueEvents boş olsa
    da sonuç aynı)."""
    monkeypatch.setattr(admin_service.cache, "get", lambda k: None)
    monkeypatch.setattr(admin_service.cache, "set", lambda *a, **k: None)
    depo.docs["adminEconomics/2026-09-11"] = {
        "date": "2026-09-11",
        "users": {"u1": {"r": 4.99, "rs": 0, "c": 0.05, "n": 1, "t": 3}},
        "others": {"r": 0, "rs": 0, "c": 0, "n": 0, "t": 0},
        "shared": {"c": 0.01, "n": 1}, "count": 1}
    depo.docs["adminEconomics/2026-09-12"] = {
        "date": "2026-09-12",
        "users": {"u1": {"r": -1.0, "rs": 2.5, "c": 0, "n": 0, "t": 0}},
        "others": {"r": 0, "rs": 0, "c": 0, "n": 0, "t": 0},
        "shared": {"c": 0, "n": 0}, "count": 1}

    sonuc = admin_service.economics(days=30, env="PRODUCTION")

    u1 = next(s for s in sonuc["users"] if s["uid"] == "u1")
    assert u1["displayName"] == "Ayşe"          # get_all ile ad
    assert u1["revenueUsd"] == pytest.approx(3.99)   # 4.99 − 1.00 iade
    assert u1["sandboxUsd"] == pytest.approx(2.5)
    assert u1["aiCostUsd"] == pytest.approx(0.05)
    assert u1["marginUsd"] == pytest.approx(3.99 * 0.85 - 0.05)
    assert sonuc["totals"]["sharedAiCostUsd"] == pytest.approx(0.01)
    assert sonuc["totals"]["aiCostUsd"] == pytest.approx(0.06)
    assert sonuc["coverage"] == {"daysFound": 2, "oldest": "2026-09-11"}
    # Hareketsiz kullanıcı rollup'ta yok → satır da yok (top-N tablosu).
    assert all(s["uid"] != "u2" for s in sonuc["users"])
