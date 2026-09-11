"""Açılış yapılandırması ucu (F3 → PBZ zorunlu güncelleme kapısı).

Uç kimliksizdir (giriş ekranından önce çağrılır) ve FAIL-OPEN sözleşmesiyle
yaşar: eşik okuması fırlatırsa 0 döner, kimse BU UÇ yüzünden kilitlenmez.
Asıl zorlama artık sunucuda (core/app_gate, 426).

Eşik kaynağı `app_gate.current_min_build()` = max(env, config/app.minBuild),
60 s memo. Testler o kaynağı patch'ler ve memo'yu sıfırlar —
`config.MIN_APP_BUILD`'i tek başına patch'lemek yetmez (uç env'i doğrudan
okumuyor; eski test sessizce anlamsızlaşırdı).
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from core import app_gate, config
from core.config import _int_env
from main import app


class _Anlik:
    def __init__(self, veri):
        self._veri = veri
        self.exists = veri is not None

    def to_dict(self):
        return dict(self._veri) if self._veri else {}


class _SahteFirestore:
    """Yalnız config/app dokümanı."""

    def __init__(self, dokuman):
        self._dokuman = dokuman

    def collection(self, ad):
        return self

    def document(self, ad):
        return self

    def get(self):
        return _Anlik(self._dokuman)


@pytest.fixture(autouse=True)
def hermetik(monkeypatch):
    """Firestore YOK, env 0 — makinede ADC varsa gerçek doküman okunurdu
    (RD-turu dersi). Her test kaynağı kendi kurar."""
    app_gate.reset_memo()
    monkeypatch.setattr(app_gate.firestore_client, "get_client", lambda: None)
    monkeypatch.setattr(config, "MIN_APP_BUILD", 0)
    yield
    app_gate.reset_memo()


def test_varsayilan_sifir_kimse_engellenmez():
    with TestClient(app) as client:
        yanit = client.get("/api/v1/config/app")
    assert yanit.status_code == 200
    assert yanit.json()["data"]["min_build"] == 0


def test_esik_env_tabanini_yansitir(monkeypatch):
    monkeypatch.setattr(config, "MIN_APP_BUILD", 7)
    with TestClient(app) as client:
        yanit = client.get("/api/v1/config/app")
    assert yanit.json()["data"]["min_build"] == 7


def test_esik_dokumandan_gelir(monkeypatch):
    """Sıcak anahtar: panelin yazdığı config/app.minBuild env'siz de görünür."""
    monkeypatch.setattr(app_gate.firestore_client, "get_client",
                        lambda: _SahteFirestore({"minBuild": 42}))
    with TestClient(app) as client:
        yanit = client.get("/api/v1/config/app")
    assert yanit.json()["data"]["min_build"] == 42


def test_kimlik_istemez():
    """Authorization başlıksız 200 — kapı giriş ekranından önce çalışır."""
    with TestClient(app) as client:
        yanit = client.get("/api/v1/config/app")
    assert yanit.status_code == 200


def test_kilitli_istemci_de_esigi_okur(monkeypatch):
    """Kapıdan muaf: eski build bile eşiği öğrenebilmeli (426 değil 200)."""
    monkeypatch.setattr(app_gate.firestore_client, "get_client",
                        lambda: _SahteFirestore({"minBuild": 35}))
    with TestClient(app) as client:
        yanit = client.get("/api/v1/config/app",
                           headers={"X-App-Build": "34"})
    assert yanit.status_code == 200
    assert yanit.json()["data"]["min_build"] == 35


def test_no_store():
    """Ara önbellekler eşiği bayatlatmasın."""
    with TestClient(app) as client:
        yanit = client.get("/api/v1/config/app")
    assert yanit.headers["Cache-Control"] == "no-store"


def test_kota_muaf():
    """Kimliksiz uç NAT arkasında tek IP kovasını paylaşır; 429 istemcide
    'eşik okunamadı' sayılırdı. Genel kota 60/dk — 70 istek de 429 vermez."""
    with TestClient(app) as client:
        for i in range(70):
            yanit = client.get("/api/v1/config/app")
            assert yanit.status_code == 200, f"{i}. istekte {yanit.status_code}"


def test_okuma_firlatirsa_sifir_fail_open(monkeypatch):
    """Sözleşme: app_gate patlasa bile uç 0 döner, kimse kilitlenmez."""
    def patla():
        raise RuntimeError("beklenmeyen")

    monkeypatch.setattr(app_gate, "current_min_build", patla)
    with TestClient(app) as client:
        yanit = client.get("/api/v1/config/app")
    assert yanit.status_code == 200
    assert yanit.json()["data"]["min_build"] == 0


def test_bozuk_env_varsayilana_duser(monkeypatch):
    monkeypatch.setenv("RYTHO_TEST_INT", "abc")
    assert _int_env("RYTHO_TEST_INT", 0) == 0
    monkeypatch.setenv("RYTHO_TEST_INT", "42")
    assert _int_env("RYTHO_TEST_INT", 0) == 42
    monkeypatch.delenv("RYTHO_TEST_INT")
    assert _int_env("RYTHO_TEST_INT", 5) == 5
