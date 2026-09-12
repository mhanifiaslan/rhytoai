"""CSV dışa aktarım (AD9): owner, ön-izli, mahremiyet çizgisi.

Değişmezler:
- `users_csv_rows`: `_iter_users` sayfaları bellekte süzülür (plan,
  language, platform, disabled yalnız True, activeSince); `fcmToken` ve
  doğum verisi satırda YOKTUR; `hasPush` bool.
- `GET /admin/users/export.csv`: BOM + sabit sütun başlığı,
  `Content-Disposition: attachment; filename="rytho-kullanicilar-YYYYMMDD.csv"`;
  gövdede token/doğum tarihi geçmez; iz `export.users` intent → done + rows.
- `GET /admin/revenue/export.csv?days&env`: yalnız seçili environment.
- İz yazılamazsa 503 ve akış BAŞLAMAZ; support 403.
"""
from __future__ import annotations

import csv
import datetime as dt
import io

import pytest
from fastapi.testclient import TestClient

from core import config
from core import firestore as firestore_client
from services import admin_service
from main import app
from test_admin_audit import SahteFirestore

_SIMDI = dt.datetime.now(dt.timezone.utc)


@pytest.fixture()
def depo(monkeypatch):
    sahte = SahteFirestore({
        "users/u1": {"displayName": "Ayşe", "email": "ayse@ornek.com",
                     "username": "ayse", "plan": "plus", "language": "tr",
                     "platform": "android", "appBuild": 38,
                     "createdAt": _SIMDI, "lastSeenDaily": "2026-09-10",
                     "streakCount": 4, "fcmToken": "GIZLI-TOKEN",
                     "birthDate": "1990-01-01", "birthTime": "04:30",
                     "onboardingCompleted": True},
        "users/u2": {"displayName": "Erkan", "email": "erkan@ornek.com",
                     "plan": "free", "language": "en", "platform": "ios",
                     "createdAt": _SIMDI - dt.timedelta(days=3),
                     "lastSeenDaily": "2026-08-01", "authDisabled": True},
        "users/u3": {"displayName": "Eski", "email": "eski@ornek.com",
                     "createdAt": _SIMDI - dt.timedelta(days=30)},
        "revenueEvents/e1": {"uid": "u1", "eventType": "INITIAL_PURCHASE",
                             "monetary": True, "price": 4.99,
                             "productId": "rytho_plus_monthly",
                             "store": "PLAY_STORE", "currency": "TRY",
                             "priceInPurchasedCurrency": 149.99,
                             "countryCode": "TR", "isTrial": False,
                             "environment": "PRODUCTION",
                             "at": _SIMDI - dt.timedelta(days=1)},
        "revenueEvents/e2": {"uid": "u2", "eventType": "TEST",
                             "monetary": True, "price": 1.0,
                             "environment": "SANDBOX", "at": _SIMDI},
        "revenueEvents/e3": {"uid": "u1", "eventType": "RENEWAL",
                             "monetary": True, "price": 4.99,
                             "environment": "PRODUCTION",
                             "at": _SIMDI - dt.timedelta(days=60)},
    })
    monkeypatch.setattr(firestore_client, "get_client", lambda: sahte)
    monkeypatch.setattr(config, "DEV_MODE", True)
    monkeypatch.setattr(config, "DEV_ADMIN", True)
    monkeypatch.setattr(config, "DEV_ADMIN_ROLE", "owner")
    return sahte


# ---------------------------------------------------------------------------
# Servis
# ---------------------------------------------------------------------------

def test_users_rows_sutunlar_ve_mahremiyet(depo):
    satirlar = list(admin_service.users_csv_rows())
    assert [s["uid"] for s in satirlar] == ["u1", "u2", "u3"]
    ayse = satirlar[0]
    assert set(ayse) == set(admin_service.USERS_CSV_COLUMNS)
    assert ayse["hasPush"] is True
    assert satirlar[1]["hasPush"] is False
    assert ayse["createdAt"] == _SIMDI.isoformat()
    duz = str(satirlar)
    assert "GIZLI-TOKEN" not in duz
    assert "1990-01-01" not in duz
    assert "04:30" not in duz
    assert "fcmToken" not in admin_service.USERS_CSV_COLUMNS
    assert not any("birth" in s.lower() for s in admin_service.USERS_CSV_COLUMNS)


def test_users_rows_suzgecler(depo):
    ids = lambda **k: [s["uid"] for s in admin_service.users_csv_rows(**k)]
    assert ids(plan="plus") == ["u1"]
    assert ids(language="en") == ["u2"]
    assert ids(platform="android") == ["u1"]
    # disabled yalnız True süzer; False/None = süzgeç yok.
    assert ids(disabled=True) == ["u2"]
    assert ids(disabled=False) == ["u1", "u2", "u3"]
    assert ids(active_since="2026-09-01") == ["u1"]
    assert ids(plan="free", disabled=True) == ["u2"]


def test_revenue_rows_env_ve_pencere(depo):
    uretim = list(admin_service.revenue_csv_rows(days=30, env="PRODUCTION"))
    assert [s["id"] for s in uretim] == ["e1"]   # e3 pencere dışı, e2 sandbox
    assert set(uretim[0]) == set(admin_service.REVENUE_CSV_COLUMNS)
    assert uretim[0]["countryCode"] == "TR"
    assert uretim[0]["partnerId"] == ""
    genis = list(admin_service.revenue_csv_rows(days=90, env="PRODUCTION"))
    assert [s["id"] for s in genis] == ["e1", "e3"]  # at DESC
    assert [s["id"] for s in admin_service.revenue_csv_rows(env="SANDBOX")] == ["e2"]


# ---------------------------------------------------------------------------
# Uçlar
# ---------------------------------------------------------------------------

def _csv_oku(metin: str) -> list[dict]:
    assert metin.startswith("﻿")
    return list(csv.DictReader(io.StringIO(metin.lstrip("﻿"))))


def test_users_export_ucu(depo):
    with TestClient(app) as client:
        yanit = client.get("/api/v1/admin/users/export.csv?plan=plus")
    assert yanit.status_code == 200
    assert yanit.headers["content-type"].startswith("text/csv")
    gun = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")
    assert yanit.headers["content-disposition"] == (
        f'attachment; filename="rytho-kullanicilar-{gun}.csv"')
    metin = yanit.content.decode("utf-8")
    satirlar = _csv_oku(metin)
    assert metin.lstrip("﻿").split("\r\n")[0] == ",".join(
        admin_service.USERS_CSV_COLUMNS)
    assert [s["uid"] for s in satirlar] == ["u1"]
    assert satirlar[0]["hasPush"] == "True"
    assert satirlar[0]["displayName"] == "Ayşe"
    assert "GIZLI-TOKEN" not in metin
    assert "1990-01-01" not in metin

    izler = depo.izler()
    assert len(izler) == 1
    assert izler[0]["action"] == "export.users"
    assert izler[0]["phase"] == "done"
    assert izler[0]["rows"] == 1
    assert izler[0]["params"]["filters"]["plan"] == "plus"


def test_users_export_sema_422(depo):
    with TestClient(app) as client:
        assert client.get("/api/v1/admin/users/export.csv?plan=gold").status_code == 422
        assert client.get("/api/v1/admin/users/export.csv?activeSince=dun").status_code == 422
        assert client.get("/api/v1/admin/users/export.csv?disabled=belki").status_code == 422
    assert depo.izler() == []


def test_revenue_export_ucu(depo):
    with TestClient(app) as client:
        yanit = client.get("/api/v1/admin/revenue/export.csv?days=90&env=SANDBOX")
    assert yanit.status_code == 200
    gun = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")
    assert yanit.headers["content-disposition"] == (
        f'attachment; filename="rytho-gelir-sandbox-{gun}.csv"')
    satirlar = _csv_oku(yanit.content.decode("utf-8"))
    assert [s["id"] for s in satirlar] == ["e2"]
    assert list(satirlar[0]) == list(admin_service.REVENUE_CSV_COLUMNS)
    izler = depo.izler()
    assert [i["action"] for i in izler] == ["export.revenue"]
    assert izler[0]["params"] == {"days": 90, "env": "SANDBOX"}
    assert izler[0]["phase"] == "done"


def test_export_iz_yazilamazsa_503(depo):
    depo.kirik_koleksiyonlar.add("adminAudit")
    with TestClient(app) as client:
        k = client.get("/api/v1/admin/users/export.csv")
        g = client.get("/api/v1/admin/revenue/export.csv")
    assert k.status_code == 503
    assert g.status_code == 503
    assert "GIZLI" not in k.text
    assert k.json()["detail"] == "Denetim izi yazılamadı; işlem yapılmadı."


def test_export_destege_403(depo, monkeypatch):
    monkeypatch.setattr(config, "DEV_ADMIN_ROLE", "support")
    with TestClient(app) as client:
        assert client.get("/api/v1/admin/users/export.csv").status_code == 403
        assert client.get("/api/v1/admin/revenue/export.csv").status_code == 403
    assert depo.izler() == []


def test_export_firestore_yokken_500(depo, monkeypatch):
    monkeypatch.setattr(firestore_client, "get_client", lambda: None)
    with TestClient(app) as client:
        assert client.get("/api/v1/admin/users/export.csv").status_code == 500
