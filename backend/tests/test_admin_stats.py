"""Admin istatistikleri (W5): toplama mantığı + uç kapıları.

Değişmezler:
- Abonelik sayımı HAM dokümandan: RYTHO_FORCE_PLUS=1 sayımı DEĞİŞTİRMEZ.
- collect idempotent: çift çalıştırma aynı dokümanı ezer, birikmez.
- /stats ve /live yalnız admin claim ile; /collect scheduler sırrıyla da.
"""
from __future__ import annotations

import datetime as dt

import pytest
from fastapi.testclient import TestClient

from core import config
from services import stats_service

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
# Bellek içi sahte Firestore — stats_service'in kullandığı yüzeyler:
# collection().order_by().limit().start_after().stream(), collection_group()
# .where().stream(), count().get(), document().set/get().
# ---------------------------------------------------------------------------

class _Anlik:
    def __init__(self, doc_id, veri):
        self.id = doc_id
        self._veri = veri
        self.exists = veri is not None

    def to_dict(self):
        return dict(self._veri) if self._veri else None


class _Sorgu:
    def __init__(self, satirlar):
        self._satirlar = list(satirlar)

    def where(self, filter=None):
        alan, islem, deger = filter.field_path, filter.op_string, filter.value
        def uyar(v):
            x = v[1].get(alan)
            if islem == "==":
                return x == deger
            if x is None:
                return False
            if islem == ">":
                return x > deger
            if islem == ">=":
                return x >= deger
            if islem == "<":
                return x < deger
            raise NotImplementedError(islem)
        return _Sorgu([v for v in self._satirlar if uyar(v)])

    def order_by(self, alan, direction="ASCENDING"):
        ters = direction == "DESCENDING"
        return _Sorgu(sorted(self._satirlar, key=lambda v: v[0], reverse=ters))

    def limit(self, n):
        return _Sorgu(self._satirlar[:n])

    def start_after(self, imlec):
        son = imlec["__name__"]
        return _Sorgu([v for v in self._satirlar if v[0] > son])

    def stream(self):
        return [_Anlik(d, v) for d, v in self._satirlar]

    def count(self):
        adet = len(self._satirlar)

        class _Sonuc:
            def get(self):
                class _Deger:
                    value = adet
                return [[_Deger()]]
        return _Sonuc()


class _Dokuman:
    def __init__(self, depo, yol):
        self._depo = depo
        self._yol = yol

    def set(self, veri, merge=False):
        self._depo.yazilan[self._yol] = veri

    def get(self):
        return _Anlik(self._yol[-1], self._depo.yazilan.get(self._yol))


class _Koleksiyon(_Sorgu):
    def __init__(self, depo, ad, satirlar):
        super().__init__(satirlar)
        self._depo = depo
        self._ad = ad

    def document(self, doc_id):
        return _Dokuman(self._depo, (self._ad, doc_id))


class SahteFirestore:
    """veriler: {"users": [(id, dict)...], "cg:private": [...], ...}"""

    def __init__(self, veriler):
        self._veriler = veriler
        self.yazilan = {}

    def collection(self, ad):
        return _Koleksiyon(self, ad, self._veriler.get(ad, []))

    def collection_group(self, ad):
        return _Sorgu(self._veriler.get(f"cg:{ad}", []))


_SIMDI = dt.datetime.now(dt.timezone.utc)
_BUGUN = _SIMDI.date().isoformat()


def _ornek_veri():
    return {
        "users": [
            ("u1", {"onboardingCompleted": True, "createdAt": _SIMDI,
                    "lastSeenDaily": _BUGUN, "streakCount": 5,
                    "language": "tr", "fcmToken": "t"}),
            ("u2", {"onboardingCompleted": True, "streakCount": 0,
                    "language": "en"}),
            ("u3", {"streakCount": 12, "language": "tr"}),  # onboarded değil
        ],
        "cg:private": [
            ("subscription", {"active": True,
                              "expiresAt": _SIMDI + dt.timedelta(days=10),
                              "productId": "rytho_plus_monthly",
                              "store": "PLAY_STORE", "isTrial": True,
                              "willRenew": False}),
            ("subscription", {"active": False,
                              "expiresAt": _SIMDI + dt.timedelta(days=5)}),
            ("subscription", {"active": True,
                              "expiresAt": _SIMDI - dt.timedelta(days=1)}),
            ("wallet", {"allowance": 100}),  # active alanı yok — eşleşmez
        ],
        "revenueEvents": [
            ("e1", {"eventType": "INITIAL_PURCHASE", "price": 4.99,
                    "currency": "TRY", "priceInPurchasedCurrency": 169.99,
                    "productId": "rytho_plus_monthly", "at": _SIMDI}),
            ("e2", {"eventType": "NON_RENEWING_PURCHASE", "price": 1.99,
                    "currency": "USD", "priceInPurchasedCurrency": 1.99,
                    "productId": "rytho_tokens_small", "at": _SIMDI}),
            ("e3", {"eventType": "REFUND", "price": 1.99, "currency": "USD",
                    "productId": "rytho_tokens_small", "at": _SIMDI}),
        ],
        "cg:friends": [
            ("f1", {"status": "accepted"}), ("f2", {"status": "accepted"}),
            ("f3", {"status": "incoming"}),
        ],
        "reports": [], "aiCache": [("c1", {})],
        "cg:conversations": [("k1", {})], "usernames": [("ad1", {})],
    }


@pytest.fixture()
def sahte(monkeypatch):
    depo = SahteFirestore(_ornek_veri())
    monkeypatch.setattr(
        "services.stats_service.firestore_client.get_client", lambda: depo)
    # Eşik memo'su süreç içi (PBZ): önceki testin değeri sızmasın.
    from core import app_gate
    app_gate.reset_memo()
    yield depo
    app_gate.reset_memo()


def test_toplama_sayilari(sahte, monkeypatch):
    # FORCE_PLUS istatistiği ZEHİRLEYEMEZ: toplayıcı ham dokümana bakar.
    monkeypatch.setattr("core.entitlements.FORCE_PLUS", True)
    d = stats_service.collect()

    assert d["users"]["total"] == 3
    assert d["users"]["onboarded"] == 2
    assert d["users"]["newToday"] == 1
    assert d["users"]["dau"] == 1
    assert d["users"]["streakBuckets"] == {"0": 1, "1-3": 0, "4-7": 1, "8+": 1}
    assert d["users"]["byLanguage"] == {"tr": 2, "en": 1}
    # Aktif abone 1: pasif ve süresi geçmiş olanlar ile wallet dokümanı
    # (active alanı yok) SAYILMAZ — FORCE_PLUS açıkken bile.
    assert d["subs"]["active"] == 1
    assert d["subs"]["trial"] == 1
    assert d["subs"]["cancelledButActive"] == 1
    # Gelir: 4.99 + 1.99 - 1.99 (iade)
    assert d["revenue"]["grossToday"] == pytest.approx(4.99)
    assert d["revenue"]["packSalesToday"] == {"rytho_tokens_small": 1}
    assert d["revenue"]["refundsToday"] == 1
    assert d["social"]["friendships"] == 1  # 2 doküman / 2


def test_toplama_ap_ekleri(sahte, monkeypatch):
    """AP-turu: jeton akışı (debit ledger), AI kullanımı (usageEvents),
    bildirim koşuları (notifyRuns) ve platform kırılımı dokümana girer."""
    sahte._veriler["cg:ledger"] = [
        ("l1", {"type": "debit", "feature": "chat", "amount": 1,
                "at": _SIMDI}),
        ("l2", {"type": "debit", "feature": "natal", "amount": 5,
                "at": _SIMDI}),
        ("l3", {"type": "credit", "productId": "rytho_tokens_small",
                "amount": 100, "at": _SIMDI}),
        # Dün kalan kayıt gün dilimine GİRMEZ.
        ("l0", {"type": "debit", "feature": "chat", "amount": 9,
                "at": _SIMDI - dt.timedelta(days=2)}),
    ]
    sahte._veriler["usageEvents"] = [
        ("u1", {"day": _BUGUN, "feature": "chat", "estCostUsd": 0.002}),
        ("u2", {"day": _BUGUN, "feature": "natal", "estCostUsd": 0.0033}),
        ("u3", {"day": "2020-01-01", "feature": "chat",
                "estCostUsd": 9.9}),  # başka gün — girmez
    ]
    sahte.yazilan[("notifyRuns", f"{_BUGUN}-daily")] = {
        "sent": 4, "failed": 1, "skipped": {"sessiz-saat": 2, "tercih": 1}}

    d = stats_service.collect()

    assert d["tokens"]["spentToday"] == {"chat": 1, "natal": 5}
    assert d["tokens"]["spentTotalToday"] == 6
    assert d["tokens"]["creditedToday"] == 100
    assert d["ai"]["callsToday"] == 2
    assert d["ai"]["estCostToday"] == pytest.approx(0.0053)
    assert d["ai"]["byFeature"] == {"chat": 1, "natal": 1}
    assert d["notify"]["daily"] == {"sent": 4, "failed": 1,
                                    "skippedTotal": 3}
    assert d["users"]["byPlatform"] == {"bilinmiyor": 3}


def test_toplama_surum_kirilimi(sahte, monkeypatch):
    """PBZ: `appBuild` aynasından sürüm kırılımı. Alanı olmayan ≤34
    istemciler 'unknown', eşiğin altındakiler AYRI sayılır — ek count()
    sorgusu yok, tek geçişten türetilir."""
    sahte._veriler["users"] = [
        ("u1", {"appBuild": 35}),
        ("u2", {"appBuild": 36}),
        ("u3", {"appBuild": 36}),
        ("u4", {"displayName": "başlıksız eski istemci"}),
        ("u5", {"appBuild": "bozuk"}),  # bozuk değer de bilinmiyor
    ]
    monkeypatch.setattr(stats_service.app_gate, "current_min_build",
                        lambda: 36)

    d = stats_service.collect()

    assert d["builds"] == {"byBuild": {"35": 1, "36": 2}, "min": 36,
                           "belowMin": 1, "unknown": 2}


def test_toplama_esik_kapaliyken_altinda_sifir(sahte, monkeypatch):
    sahte._veriler["users"] = [("u1", {"appBuild": 35})]
    monkeypatch.setattr(stats_service.app_gate, "current_min_build",
                        lambda: 0)
    d = stats_service.collect()
    assert d["builds"]["belowMin"] == 0
    assert d["builds"]["min"] == 0


def test_toplama_idempotent(sahte):
    stats_service.collect()
    stats_service.collect()
    # Tek doküman, ezilmiş — birikme yok.
    yollar = [y for y in sahte.yazilan if y[0] == "adminStats"]
    assert len(yollar) == 1
    assert sahte.yazilan[yollar[0]]["users"]["total"] == 3


@uygulama_gerekir
def test_stats_ucu_claim_ister(monkeypatch):
    monkeypatch.setattr(config, "DEV_MODE", True)
    monkeypatch.setattr(config, "DEV_ADMIN", False)
    with TestClient(app) as client:
        yanit = client.get("/api/v1/admin/stats")
    assert yanit.status_code == 403


@uygulama_gerekir
def test_collect_scheduler_sirriyla_gecer(sahte, monkeypatch):
    monkeypatch.setattr(config, "DEV_MODE", True)
    monkeypatch.setattr(config, "DEV_ADMIN", False)
    monkeypatch.setattr(config, "NOTIFY_SCHEDULER_SECRET", "sir")
    with TestClient(app) as client:
        red = client.post("/api/v1/admin/collect")
        kabul = client.post("/api/v1/admin/collect",
                            headers={"Authorization": "sir"})
    assert red.status_code == 403
    assert kabul.status_code == 200
    assert kabul.json()["status"] == "ok"


@uygulama_gerekir
def test_collect_dev_admin_bayragiyla_da_gecer(sahte, monkeypatch):
    monkeypatch.setattr(config, "DEV_MODE", True)
    monkeypatch.setattr(config, "DEV_ADMIN", True)
    with TestClient(app) as client:
        yanit = client.post("/api/v1/admin/collect")
    assert yanit.status_code == 200
