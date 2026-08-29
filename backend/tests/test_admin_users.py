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
from services import admin_service

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


# ---------------------------------------------------------------------------
# Genel bellek içi sahte Firestore: yol -> veri; alt koleksiyon + sorgu
# ---------------------------------------------------------------------------

class _Anlik:
    def __init__(self, doc_id, veri):
        self.id = doc_id
        self._veri = veri
        self.exists = veri is not None

    def to_dict(self):
        return dict(self._veri) if self._veri else None


class _Dokuman:
    def __init__(self, depo, yol):
        self._depo = depo
        self._yol = yol

    def get(self, transaction=None):
        return _Anlik(self._yol.rsplit("/", 1)[-1],
                      self._depo.docs.get(self._yol))

    def set(self, veri, merge=False):
        mevcut = dict(self._depo.docs.get(self._yol) or {}) if merge else {}
        mevcut.update(veri)
        self._depo.docs[self._yol] = mevcut

    def collection(self, ad):
        return _Koleksiyon(self._depo, f"{self._yol}/{ad}")


class _Koleksiyon:
    _oto = 0

    def __init__(self, depo, yol, satirlar=None, ters=False, n=None):
        self._depo = depo
        self._yol = yol
        self._satirlar = satirlar
        self._ters = ters
        self._n = n

    def document(self, ad=None):
        if ad is None:
            _Koleksiyon._oto += 1
            ad = f"oto-{_Koleksiyon._oto}"
        return _Dokuman(self._depo, f"{self._yol}/{ad}")

    def _cek(self):
        if self._satirlar is not None:
            return self._satirlar
        onek = self._yol + "/"
        return [(k[len(onek):], v) for k, v in self._depo.docs.items()
                if k.startswith(onek) and "/" not in k[len(onek):]]

    def where(self, filter=None):
        alan, islem, deger = (filter.field_path, filter.op_string,
                              filter.value)

        def uyar(v):
            x = v[1].get(alan)
            if islem == "==":
                return x == deger
            if x is None:
                return False
            if islem == ">=":
                return x >= deger
            if islem == "<":
                return x < deger
            raise NotImplementedError(islem)
        return _Koleksiyon(self._depo, self._yol,
                           [v for v in self._cek() if uyar(v)],
                           self._ters, self._n)

    def order_by(self, alan, direction="ASCENDING"):
        satirlar = sorted(
            self._cek(),
            key=(lambda v: v[0]) if alan == "__name__" else
                (lambda v: getattr(v[1].get(alan), "timestamp", lambda: 0)()),
            reverse=(direction == "DESCENDING"))
        return _Koleksiyon(self._depo, self._yol, satirlar, n=self._n)

    def limit(self, n):
        return _Koleksiyon(self._depo, self._yol, self._cek()[:n])

    def start_after(self, imlec):
        son = imlec["__name__"]
        return _Koleksiyon(self._depo, self._yol,
                           [v for v in self._cek() if v[0] > son])

    def stream(self):
        return [_Anlik(d, v) for d, v in self._cek()]

    def count(self):
        adet = len(self._cek())

        class _Sonuc:
            def get(self):
                class _Deger:
                    value = adet
                return [[_Deger()]]
        return _Sonuc()


class SahteFirestore:
    def __init__(self):
        self.docs: dict[str, dict] = {}

    def collection(self, ad):
        return _Koleksiyon(self, ad)


_SIMDI = dt.datetime.now(dt.timezone.utc)


@pytest.fixture()
def depo(monkeypatch):
    sahte = SahteFirestore()
    sahte.docs.update({
        "users/u1": {"displayName": "Ayşe", "email": "ayse@ornek.com",
                     "username": "ayse", "sunSign": "leo",
                     "createdAt": _SIMDI, "lastSeenDaily": "2026-08-29",
                     "streakCount": 4, "language": "tr",
                     "timezone": "Europe/Istanbul", "platform": "android",
                     "onboardingCompleted": True, "fcmToken": "GIZLI-TOKEN",
                     "birthDate": "1990-01-01"},
        "users/u2": {"displayName": "Erkan", "email": "erkan@ornek.com",
                     "createdAt": _SIMDI - dt.timedelta(days=3)},
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
    satirlar = admin_service.list_users()
    assert len(satirlar) == 2
    ayse = next(s for s in satirlar if s["uid"] == "u1")
    assert ayse["hasPush"] is True
    assert "fcmToken" not in ayse
    assert ayse["platform"] == "android"
    # createdAt desc: u1 (bugün) önce
    assert satirlar[0]["uid"] == "u1"


def test_liste_onek_aramasi(depo):
    assert [s["uid"] for s in admin_service.list_users(query="erk")] == ["u2"]
    assert admin_service.list_users(query="yok") == []


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


def test_economics_marj_matematigi(depo):
    """Kâr = gelir × 0,85 − AI maliyeti; iade negatif; paylaşımlı üretim
    kullanıcıya yazılmaz ama toplamda görünür."""
    depo.docs["usageEvents/x1"] = {"uid": "u1", "estCostUsd": 0.05,
                                   "at": _SIMDI}
    depo.docs["usageEvents/x2"] = {"uid": None, "estCostUsd": 0.01,
                                   "at": _SIMDI}
    depo.docs["revenueEvents/e2"] = {"uid": "u1", "eventType": "REFUND",
                                     "price": 1.0, "at": _SIMDI}

    sonuc = admin_service.economics(days=30)

    u1 = next(s for s in sonuc["users"] if s["uid"] == "u1")
    assert u1["revenueUsd"] == pytest.approx(3.99)   # 4.99 − 1.00 iade
    assert u1["aiCostUsd"] == pytest.approx(0.05)
    assert u1["marginUsd"] == pytest.approx(3.99 * 0.85 - 0.05)
    assert sonuc["totals"]["sharedAiCostUsd"] == pytest.approx(0.01)
    assert sonuc["totals"]["aiCostUsd"] == pytest.approx(0.06)
    # Hareketsiz kullanıcı da satır alır (tam liste).
    assert any(s["uid"] == "u2" and s["revenueUsd"] == 0
               for s in sonuc["users"])
