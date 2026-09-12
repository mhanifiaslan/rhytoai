"""Roller ve kapılar (AD1): owner / support.

Değişmezler:
- `admin:true` + rol yok → owner (geçiş). Bilinmeyen rol admin'de owner'a
  düşer; admin olmayanda yok sayılır (yetki vermez).
- `require_admin` iki rolü de geçirir; `require_owner` yalnız owner'ı —
  403 jenerik ("Yetkisiz."), rol modeli sızmaz.
- DEV_MODE: rol RYTHO_DEV_ROLE'dan, ama yalnız DEV_ADMIN açıkken.
- Owner-only uçlar support token'la 403; `/admin/me` rolü söyler.
- Arama aynası kancası best-effort: fırlatsa da kimlik doğrulama düşmez.
"""
from __future__ import annotations

import asyncio
import sys
import types

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from core import auth, config
from main import app


class _SahteToken:
    credentials = "token"


def _kullanici(monkeypatch, decoded):
    monkeypatch.setattr(auth, "_init_firebase", lambda: True)
    monkeypatch.setattr(auth, "_verify", lambda t: decoded)
    return asyncio.run(auth.get_current_user(
        credentials=_SahteToken(), lang="tr"))


@pytest.fixture(autouse=True)
def ayna_sessiz(monkeypatch):
    """search_mirror.ensure Firestore'a gitmesin — kancanın varlığı ayrı
    testte sınanır."""
    try:
        from services import search_mirror
        monkeypatch.setattr(search_mirror, "ensure", lambda uid, *a, **k: None)
    except ImportError:
        pass


# ---------------------------------------------------------------------------
# Claim → rol
# ---------------------------------------------------------------------------

def test_admin_claim_rolsuz_owner(monkeypatch):
    user = _kullanici(monkeypatch, {"uid": "u", "admin": True})
    assert user.admin is True
    assert user.role == "owner"
    assert auth.require_owner(auth.require_admin(user)) is user


def test_support_rolu(monkeypatch):
    user = _kullanici(monkeypatch, {"uid": "u", "admin": True,
                                    "role": "support"})
    assert user.role == "support"
    assert auth.require_admin(user) is user
    with pytest.raises(HTTPException) as h:
        auth.require_owner(user)
    assert h.value.status_code == 403
    assert h.value.detail == "Yetkisiz."


def test_rol_var_admin_yok_da_gecer(monkeypatch):
    """Claim yalnız `role:'support'` taşıyorsa (admin:true basılmamış)
    panel yine açılır — rol tek başına tanınır; owner kapısı kapalı."""
    user = _kullanici(monkeypatch, {"uid": "u", "role": "support"})
    assert user.admin is False
    assert user.role == "support"
    assert auth.require_admin(user) is user
    with pytest.raises(HTTPException):
        auth.require_owner(user)


def test_bilinmeyen_rol(monkeypatch):
    # admin:true + saçma rol → owner (geçiş kuralı)
    user = _kullanici(monkeypatch, {"uid": "u", "admin": True, "role": "root"})
    assert user.role == "owner"
    # admin yok + saçma rol → rol yok, kapı kapalı
    user = _kullanici(monkeypatch, {"uid": "u", "role": "root"})
    assert user.role is None
    with pytest.raises(HTTPException):
        auth.require_admin(user)


def test_siradan_kullanici_rolsuz(monkeypatch):
    user = _kullanici(monkeypatch, {"uid": "u"})
    assert user.role is None
    assert user.admin is False


# ---------------------------------------------------------------------------
# DEV_MODE
# ---------------------------------------------------------------------------

def test_dev_admin_rolu_env_den(monkeypatch):
    monkeypatch.setattr(config, "DEV_MODE", True)
    monkeypatch.setattr(config, "DEV_ADMIN", True)
    monkeypatch.setattr(config, "DEV_ADMIN_ROLE", "support")
    monkeypatch.setattr(auth, "_init_firebase", lambda: False)
    user = asyncio.run(auth.get_current_user(credentials=None, lang="tr"))
    assert user.role == "support"
    monkeypatch.setattr(config, "DEV_ADMIN_ROLE", "sacma")
    user = asyncio.run(auth.get_current_user(credentials=None, lang="tr"))
    assert user.role == "owner"


def test_dev_admin_kapaliyken_rol_yok(monkeypatch):
    monkeypatch.setattr(config, "DEV_MODE", True)
    monkeypatch.setattr(config, "DEV_ADMIN", False)
    monkeypatch.setattr(config, "DEV_ADMIN_ROLE", "owner")
    monkeypatch.setattr(auth, "_init_firebase", lambda: False)
    user = asyncio.run(auth.get_current_user(credentials=None, lang="tr"))
    assert user.role is None
    with pytest.raises(HTTPException):
        auth.require_admin(user)


# ---------------------------------------------------------------------------
# Arama aynası kancası
# ---------------------------------------------------------------------------

def test_ayna_kancasi_cagrilir_ve_hatasi_yutulur(monkeypatch):
    cagrilan: list = []
    sahte = types.ModuleType("services.search_mirror")

    def ensure(uid, profil=None):
        cagrilan.append(uid)
        raise RuntimeError("Firestore yok")
    sahte.ensure = ensure
    monkeypatch.setitem(sys.modules, "services.search_mirror", sahte)
    import services
    monkeypatch.setattr(services, "search_mirror", sahte, raising=False)
    user = _kullanici(monkeypatch, {"uid": "u7"})
    assert user.uid == "u7"
    assert cagrilan == ["u7"]


# ---------------------------------------------------------------------------
# Uç katmanı: owner-only liste + /me
# ---------------------------------------------------------------------------

OWNER_ONLY = [
    ("DELETE", "/api/v1/admin/users/u1", {"confirm": "SIL", "reason": "test-x"}),
    ("POST", "/api/v1/admin/users/u1/disable", {"disabled": True, "reason": "test-x"}),
    ("POST", "/api/v1/admin/min-build", {"min_build": 0, "reason": "test-x"}),
    ("POST", "/api/v1/admin/partners", {"name": "Ortak"}),
    ("PATCH", "/api/v1/admin/partners/p1", {"active": False}),
    ("POST", "/api/v1/admin/partners/p1/codes", {}),
    ("POST", "/api/v1/admin/partners/p1/payouts", {"amount": 1}),
    ("GET", "/api/v1/admin/users/export.csv", None),
    ("GET", "/api/v1/admin/revenue/export.csv", None),
    ("POST", "/api/v1/admin/economics/recompute",
     {"from": "2026-09-01", "to": "2026-09-02"}),
    ("POST", "/api/v1/admin/config/notice", {"text": "x", "level": "info"}),
]


@pytest.fixture()
def destek(monkeypatch):
    monkeypatch.setattr(config, "DEV_MODE", True)
    monkeypatch.setattr(config, "DEV_ADMIN", True)
    monkeypatch.setattr(config, "DEV_ADMIN_ROLE", "support")


@pytest.mark.parametrize("metot,yol,govde", OWNER_ONLY,
                         ids=[f"{m} {y}" for m, y, _ in OWNER_ONLY])
def test_owner_only_uclar_destege_403(destek, metot, yol, govde):
    with TestClient(app) as client:
        yanit = client.request(metot, yol, json=govde)
    assert yanit.status_code == 403, yol
    assert yanit.json()["detail"] == "Yetkisiz."


def test_collect_destege_403(destek, monkeypatch):
    from services import stats_service
    cagrilan: list = []
    monkeypatch.setattr(stats_service, "collect",
                        lambda tarih=None: cagrilan.append(tarih) or
                        {"date": "2026-09-12", "durationMs": 1})
    monkeypatch.setattr(config, "NOTIFY_SCHEDULER_SECRET", "")
    with TestClient(app) as client:
        # DEV_MODE: bozuk Bearer dev-user'a düşer → DEV_ADMIN + support.
        yanit = client.post("/api/v1/admin/collect",
                            headers={"Authorization": "Bearer rol-testi"})
    assert yanit.status_code == 403
    assert cagrilan == []


def test_collect_owner_gecer(monkeypatch):
    monkeypatch.setattr(config, "DEV_MODE", True)
    monkeypatch.setattr(config, "DEV_ADMIN", True)
    monkeypatch.setattr(config, "DEV_ADMIN_ROLE", "owner")
    monkeypatch.setattr(config, "NOTIFY_SCHEDULER_SECRET", "")
    from core import firestore as firestore_client
    monkeypatch.setattr(firestore_client, "get_client", lambda: None)
    from services import stats_service
    monkeypatch.setattr(stats_service, "collect",
                        lambda tarih=None: {"date": "2026-09-12",
                                            "durationMs": 1})
    with TestClient(app) as client:
        yanit = client.post("/api/v1/admin/collect",
                            headers={"Authorization": "Bearer rol-testi-o"})
    assert yanit.status_code == 200
    assert yanit.json()["date"] == "2026-09-12"


def test_me_rolu_soyler(monkeypatch):
    monkeypatch.setattr(config, "DEV_MODE", True)
    monkeypatch.setattr(config, "DEV_ADMIN", True)
    for rol in ("support", "owner"):
        monkeypatch.setattr(config, "DEV_ADMIN_ROLE", rol)
        with TestClient(app) as client:
            yanit = client.get("/api/v1/admin/me")
        assert yanit.status_code == 200
        assert yanit.json() == {"status": "ok", "uid": "dev-user",
                                "email": None, "role": rol}


def test_me_claimsiz_403(monkeypatch):
    monkeypatch.setattr(config, "DEV_MODE", True)
    monkeypatch.setattr(config, "DEV_ADMIN", False)
    with TestClient(app) as client:
        assert client.get("/api/v1/admin/me").status_code == 403


def test_destek_okur_ve_sinirli_yazar(destek, monkeypatch):
    """Support: liste/360/partners okur, kredi + cihaz kilidi + auth-link
    yazar (hepsi izli, iz best-effort)."""
    from core import firestore as firestore_client
    monkeypatch.setattr(firestore_client, "get_client", lambda: None)
    from services import admin_service, partner_service
    monkeypatch.setattr(partner_service, "list_partners", lambda: [])
    monkeypatch.setattr(admin_service, "list_users",
                        lambda **k: {"users": [], "nextCursor": None,
                                     "mode": "filter"}, raising=False)
    from core import device, wallet
    monkeypatch.setattr(device, "force_release", lambda uid: True)
    monkeypatch.setattr(wallet, "credit_admin", lambda *a: None)
    monkeypatch.setattr(wallet, "get_wallet", lambda uid: {"purchased": 5})

    class _Hesap:
        email = "ayse@ornek.com"

    sahte_auth = types.SimpleNamespace(
        get_user=lambda uid: _Hesap(),
        generate_email_verification_link=lambda e: f"https://v/{e}",
        generate_password_reset_link=lambda e: f"https://r/{e}")
    import firebase_admin
    monkeypatch.setattr(firebase_admin, "auth", sahte_auth, raising=False)
    monkeypatch.setitem(sys.modules, "firebase_admin.auth", sahte_auth)

    with TestClient(app) as client:
        assert client.get("/api/v1/admin/partners").status_code == 200
        assert client.get("/api/v1/admin/users?q=ay&alan=eposta").status_code == 200
        assert client.post("/api/v1/admin/users/u1/device/release").status_code == 200
        assert client.post("/api/v1/admin/users/u1/credit",
                           json={"amount": 5, "reason": "telafi"}).status_code == 200
        link = client.post("/api/v1/admin/users/u1/auth-link",
                           json={"kind": "reset"})
        assert link.status_code == 200
        assert link.json()["link"] == "https://r/ayse@ornek.com"
        assert client.post("/api/v1/admin/users/u1/auth-link",
                           json={"kind": "sacma"}).status_code == 422
