"""Admin kota kovası (AD2).

Değişmezler:
- `/api/v1/admin/*` kendi kovasında (`adm:`), sınır ADMIN_LIMIT_PER_MINUTE
  (240): 241. çağrı 429 + Retry-After.
- Admin çağrıları genel (`std:`) kovayı YEMEZ; genel çağrılar admin
  kovasını yemez — aynı Authorization başlığıyla.
- `/api/v1/admin/collect` muaf kalır (admin kovası dolmuşken bile geçer).

Ana uygulama yerine yalın bir FastAPI: middleware'in davranışı uçların
içeriğinden bağımsızdır ve 300 istek kimlik doğrulamasız saniyeler sürer.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from core import ratelimit


def _uygulama() -> FastAPI:
    app = FastAPI()
    app.add_middleware(ratelimit.RateLimitMiddleware)

    @app.get("/api/v1/admin/me")
    def me():
        return {"ok": True}

    @app.post("/api/v1/admin/collect")
    def collect():
        return {"ok": True}

    @app.get("/api/v1/other")
    def other():
        return {"ok": True}

    return app


_BASLIK = {"Authorization": "Bearer kota-testi"}


def test_sabitler():
    assert ratelimit.ADMIN_PREFIX == "/api/v1/admin/"
    assert ratelimit.ADMIN_LIMIT_PER_MINUTE == 240
    assert "/api/v1/admin/collect" in ratelimit.EXEMPT_PATHS


def test_admin_kovasi_241de_dolar_genel_kova_dokunulmaz():
    with TestClient(_uygulama()) as client:
        for i in range(ratelimit.ADMIN_LIMIT_PER_MINUTE):
            assert client.get("/api/v1/admin/me", headers=_BASLIK).status_code == 200, i
        dolu = client.get("/api/v1/admin/me", headers=_BASLIK)
        assert dolu.status_code == 429
        assert int(dolu.headers["Retry-After"]) >= 1
        # Genel kova hiç yenmedi: aynı başlıkla sıradan uç geçer.
        assert client.get("/api/v1/other", headers=_BASLIK).status_code == 200
        # Muaf uç admin kovası doluyken de geçer.
        assert client.post("/api/v1/admin/collect", headers=_BASLIK).status_code == 200


def test_genel_kova_dolunca_admin_kovasi_dokunulmaz():
    with TestClient(_uygulama()) as client:
        for _ in range(ratelimit.DEFAULT_LIMIT_PER_MINUTE):
            assert client.get("/api/v1/other", headers=_BASLIK).status_code == 200
        assert client.get("/api/v1/other", headers=_BASLIK).status_code == 429
        assert client.get("/api/v1/admin/me", headers=_BASLIK).status_code == 200


def test_kova_anahtarlari_onek_tasir():
    with TestClient(_uygulama()) as client:
        client.get("/api/v1/admin/me", headers=_BASLIK)
        client.get("/api/v1/other", headers=_BASLIK)
    # Middleware örneğine ulaş: app.middleware_stack sarmalayıcı zinciri.
    app = client.app
    katman = app.middleware_stack
    while not isinstance(katman, ratelimit.RateLimitMiddleware):
        katman = getattr(katman, "app")
    onekler = sorted(k.split(":")[0] for k in katman._hits)
    assert onekler == ["adm", "std"]
    adm, std = (next(k for k in katman._hits if k.startswith(p + ":"))
                for p in ("adm", "std"))
    assert adm.split(":", 1)[1] == std.split(":", 1)[1]  # aynı özet, ayrı kova
