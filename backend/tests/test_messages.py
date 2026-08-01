"""Hata yolunun dili ve ham istisna sızıntısı.

Faz 3'te uç YANITLARI iki dile taşındı ama HATA yolu Türkçe kalmıştı.
İstemci sunucunun `detail` alanını doğrudan ekrana bastığı için (bkz.
apps/mobile/lib/core/api.dart, friendlyError) İngilizce kullanan biri kilitli
bir ekrana geldiğinde Türkçe metin görüyordu.

İkinci kusur: uçlar `detail=str(e)` döndürüyordu, yani Python istisna metni
kullanıcıya gösteriliyor ve sunucunun iç yapısı dışarı sızıyordu.

Çalıştırma:  .venv\\Scripts\\python.exe -m pytest tests/test_messages.py -q
"""
import pytest
from fastapi.testclient import TestClient

from core import config, entitlements, i18n
from core.messages import _MESSAGES, text

try:
    from main import app
    _APP_IMPORT_ERROR = None
except Exception as exc:  # pragma: no cover
    app = None
    _APP_IMPORT_ERROR = str(exc)

uygulama_gerekir = pytest.mark.skipif(
    _APP_IMPORT_ERROR is not None,
    reason=f"FastAPI uygulaması içe aktarılamadı: {_APP_IMPORT_ERROR}",
)


# --------------------------------------------------------------------------
# Mesaj tablosu
# --------------------------------------------------------------------------

def test_her_mesaj_her_dilde_var():
    """Eksik çeviri sessizce Türkçeye düşer; tabloda hiç olmaması daha iyidir."""
    for anahtar, çeviriler in _MESSAGES.items():
        for kod in i18n.SUPPORTED:
            assert çeviriler.get(kod), f"{anahtar} -> {kod} eksik"


def test_ceviriler_birbirinden_farkli():
    """Kopyala-yapıştır artığı: aynı metnin iki dile de yazılması."""
    for anahtar, çeviriler in _MESSAGES.items():
        assert çeviriler["tr"] != çeviriler["en"], f"{anahtar} çevrilmemiş"


def test_dil_secimi():
    assert text("auth_required", "en") == _MESSAGES["auth_required"]["en"]
    assert text("auth_required", "tr") == _MESSAGES["auth_required"]["tr"]
    # Desteklenmeyen dil varsayılana düşer — istek patlamaz
    assert text("auth_required", "de") == _MESSAGES["auth_required"]["tr"]


def test_yedek_anahtar():
    """Yeni bir kilitli özellik eklendiğinde metni yoksa genel metne düşmeli."""
    sonuç = text("paywall.henuz_yok", "en", fallback="paywall.default")
    assert sonuç == _MESSAGES["paywall.default"]["en"]


def test_bilinmeyen_anahtar_bos_donmez():
    """Boş string, kullanıcıya boş bir hata kutusu göstermek olurdu."""
    assert text("boyle_bir_anahtar_yok", "en")


def test_kota_metnine_limit_yerlesir():
    assert "5" in text("quota.chat", "en", limit=5)
    assert "5" in text("quota.chat", "tr", limit=5)


def test_her_ozellik_icin_paywall_metni_var():
    """require_plus ile korunan her özellik adının bir metni olmalı."""
    for özellik in ("personal_daily", "natal_report", "dyad", "synastry", "bazi"):
        assert f"paywall.{özellik}" in _MESSAGES


# --------------------------------------------------------------------------
# Uç davranışı: hata metni kullanıcının dilinde
# --------------------------------------------------------------------------

@uygulama_gerekir
def test_paywall_metni_dile_gore(monkeypatch):
    monkeypatch.setattr(entitlements, "is_subscriber", lambda uid: False)

    with TestClient(app) as client:
        tr = client.post("/api/v1/reports/dyad", json={"friend_uid": "x"},
                         headers={"Authorization": "Bearer t1"})
        en = client.post("/api/v1/reports/dyad", json={"friend_uid": "x"},
                         headers={"Authorization": "Bearer t2",
                                  "Accept-Language": "en-US,en;q=0.9"})

    assert tr.status_code == entitlements.PAYWALL_STATUS
    assert en.status_code == entitlements.PAYWALL_STATUS
    assert "Rytho+" in tr.json()["detail"]
    assert "abonel" in tr.json()["detail"].lower()
    assert "part of Rytho+" in en.json()["detail"]


@uygulama_gerekir
def test_kota_metni_dile_gore(monkeypatch):
    monkeypatch.setattr(entitlements, "is_subscriber", lambda uid: False)
    monkeypatch.setattr(entitlements, "consume_quota", lambda *a: False)

    with TestClient(app) as client:
        en = client.post("/api/v1/chat", json={"message": "hello"},
                         headers={"Authorization": "Bearer t3",
                                  "Accept-Language": "en"})

    assert en.status_code == entitlements.PAYWALL_STATUS
    detay = en.json()["detail"]
    assert "Rytho+" in detay
    assert "sohbet" not in detay.lower(), "İngilizce isteğe Türkçe metin döndü"


@uygulama_gerekir
def test_kimlik_hatasi_dile_gore(monkeypatch):
    """401 metni de kullanıcıya gösteriliyor."""
    monkeypatch.setattr(config, "DEV_MODE", False)

    with TestClient(app) as client:
        tr = client.get("/api/v1/reports/horoscope/leo")
        en = client.get("/api/v1/reports/horoscope/leo",
                        headers={"Accept-Language": "en"})

    assert tr.status_code == 401
    assert en.status_code == 401
    assert "signed in" in en.json()["detail"]
    assert "oturum" in tr.json()["detail"].lower()


# --------------------------------------------------------------------------
# Ham istisna sızıntısı
# --------------------------------------------------------------------------

@uygulama_gerekir
def test_istisna_metni_kullaniciya_sizmaz(monkeypatch):
    """Kullanıcı "KeyError: 'sun'" değil, anlaşılır bir metin görmeli."""
    from services import astro_service

    def patla(**kwargs):
        raise KeyError("gizli_ic_alan")

    monkeypatch.setattr(astro_service, "get_natal_chart", patla)
    monkeypatch.setattr(entitlements, "is_subscriber", lambda uid: True)

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post(
            "/api/v1/reports/daily",
            json={"year": 1990, "month": 5, "day": 12},
            headers={"Authorization": "Bearer t4", "Accept-Language": "en"},
        )

    assert response.status_code == 500
    detay = response.json()["detail"]
    assert "gizli_ic_alan" not in detay
    assert "KeyError" not in detay
    assert detay == _MESSAGES["internal"]["en"]
