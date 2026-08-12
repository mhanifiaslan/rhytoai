"""Açılış yapılandırması ucu (F3 — zorunlu güncelleme kapısı).

Uç kimliksizdir (giriş ekranından önce çağrılır) ve FAIL-OPEN felsefesiyle
yaşar: env yoksa/bozuksa 0 döner, kimse kilitlenmez. Yanlış yazılmış bir
değişkenin tüm kullanıcıları kilitlemesi, kapının önleyeceği her sorundan
daha kötü olurdu.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from core import config
from core.config import _int_env
from main import app


def test_varsayilan_sifir_kimse_engellenmez():
    with TestClient(app) as client:
        yanit = client.get("/api/v1/config/app")
    assert yanit.status_code == 200
    veri = yanit.json()["data"]
    assert isinstance(veri["min_build"], int)


def test_esik_env_degerini_yansitir(monkeypatch):
    monkeypatch.setattr(config, "MIN_APP_BUILD", 7)
    with TestClient(app) as client:
        yanit = client.get("/api/v1/config/app")
    assert yanit.json()["data"]["min_build"] == 7


def test_kimlik_istemez():
    """Authorization başlıksız 200 — kapı giriş ekranından önce çalışır."""
    with TestClient(app) as client:
        yanit = client.get("/api/v1/config/app")
    assert yanit.status_code == 200


def test_bozuk_env_varsayilana_duser(monkeypatch):
    monkeypatch.setenv("RYTHO_TEST_INT", "abc")
    assert _int_env("RYTHO_TEST_INT", 0) == 0
    monkeypatch.setenv("RYTHO_TEST_INT", "42")
    assert _int_env("RYTHO_TEST_INT", 0) == 42
    monkeypatch.delenv("RYTHO_TEST_INT")
    assert _int_env("RYTHO_TEST_INT", 5) == 5
