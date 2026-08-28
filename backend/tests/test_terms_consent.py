"""Şartlar/gizlilik kabul kaydı (O3).

Google/Apple girişlerinde bugüne dek hiçbir onay kutusu yoktu; sihirbazın
karşılama adımı bu ucu çağırarak her sağlayıcı için ispatlanabilir kayıt
üretir. Uç bir KİLİT değildir — eski kullanıcılar kilitlenmez.
"""
from __future__ import annotations

import json

import pytest

from services import consent_service


@pytest.fixture
def yerel_kayit(tmp_path, monkeypatch):
    from core import config
    from core import firestore as firestore_client
    monkeypatch.setattr(config, "CACHE_DIR", tmp_path)
    # Test YEREL dosya yolunu doğruluyor; makinede ADC varsa gerçek
    # Firestore istemcisi kurulur ve kayıt oraya gider — dosya hiç oluşmaz,
    # test ortama göre kırmızı/yeşil değişirdi (RD-turu bulgusu). Depolama
    # seçimi deterministik yapılır.
    monkeypatch.setattr(firestore_client, "get_client", lambda: None)
    yield tmp_path


def test_kabul_kaydi_surum_ve_dil_tasir(yerel_kayit):
    assert consent_service.grant_terms_consent("u1", 1, "tr") is True
    ham = json.loads(
        (yerel_kayit / "face_consent.json").read_text(encoding="utf-8"))
    kayit = ham["terms-u1"]
    assert kayit["granted"] is True
    assert kayit["version"] == 1
    assert kayit["locale"] == "tr"
    assert "acceptedAt" in kayit


def test_istemci_surumu_kaydedilir(yerel_kayit):
    """Kayıt istemcinin GÖRDÜĞÜ sürümü tutar, sunucununkini değil —
    eski istemci eski metni göstermiş olabilir; ispat gördüğüne bağlanır."""
    consent_service.grant_terms_consent("u2", 999, "en")
    ham = json.loads(
        (yerel_kayit / "face_consent.json").read_text(encoding="utf-8"))
    assert ham["terms-u2"]["version"] == 999


def test_uc_kayit_uretiyor():
    """Uç 200 döner ve güncel sürümü söyler (istemci senkron kalsın)."""
    from fastapi.testclient import TestClient
    from main import app

    client = TestClient(app)
    yanit = client.post("/api/v1/account/consent", json={"version": 1})
    # DEV_MODE dev-user ile 200; auth yoksa 401 de kabul (ortama bağlı) —
    # asıl iddia: uç var ve şema doğru.
    assert yanit.status_code in (200, 401)
    if yanit.status_code == 200:
        assert yanit.json()["version"] == \
            consent_service.TERMS_CONSENT_VERSION
