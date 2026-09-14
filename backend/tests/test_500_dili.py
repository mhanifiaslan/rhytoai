"""Global 500 yanıtının DİLİ — İngilizce testçi Türkçe hata görmemeli.

Kapalı test denetiminde (2026-09-14) bulundu: `main.py`'deki
`@app.exception_handler(Exception)` `detail` metnini elle, Türkçe sabit
olarak yazıyordu. Çevirisi `core/messages.py` içinde ZATEN vardı ama
çağrılmıyordu. Sonuç: uygulamanın her yeri İngilizceyken beklenmedik bir
sunucu hatasında ekrana tek bir Türkçe cümle düşüyordu.

Bu dosya iki şeyi sabitler: metin dile göre değişiyor ve hiçbir dilde
ham istisna ayrıntısı sızmıyor.
"""
from __future__ import annotations

import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient

try:
    from main import app
    _HATA = None
except Exception as exc:  # pragma: no cover
    app = None
    _HATA = str(exc)

pytestmark = pytest.mark.skipif(
    _HATA is not None, reason=f"FastAPI uygulamasi ice aktarilamadi: {_HATA}")

_GIZLI = "gizli_ic_detay_42"


@pytest.fixture(scope="module", autouse=True)
def _patlayan_uc():
    """Yalnız bu dosya için kasten patlayan bir uç ekler."""
    router = APIRouter()

    @router.get("/__test__/patla")
    def patla():
        raise RuntimeError(_GIZLI)

    app.include_router(router)
    yield
    app.router.routes = [r for r in app.router.routes
                         if getattr(r, "path", "") != "/__test__/patla"]


def _cagir(accept_language: str | None):
    with TestClient(app, raise_server_exceptions=False) as client:
        basliklar = ({"Accept-Language": accept_language}
                     if accept_language else {})
        return client.get("/__test__/patla", headers=basliklar)


@pytest.mark.parametrize("dil,beklenen_parca,istenmeyen", [
    ("tr", "Lütfen", "Something went wrong"),
    ("en-US,en;q=0.9", None, "kozmik"),
])
def test_500_metni_istek_diline_uyar(dil, beklenen_parca, istenmeyen):
    y = _cagir(dil)
    assert y.status_code == 500
    detay = y.json()["detail"]
    assert detay, "500 yanıtı boş detail dönmemeli"
    assert istenmeyen.lower() not in detay.lower(), (
        f"{dil} isteğine diğer dilin metni döndü: {detay!r}")
    if beklenen_parca:
        assert beklenen_parca in detay, f"Türkçe metin beklenmişti: {detay!r}"


def test_ingilizce_yanitta_turkce_harf_yok():
    detay = _cagir("en").json()["detail"]
    for harf in ("ş", "ğ", "ı", "ç", "ö", "ü", "İ"):
        assert harf not in detay, f"İngilizce 500 metninde Türkçe harf: {harf}"


@pytest.mark.parametrize("dil", ["tr", "en", None])
def test_ham_istisna_hicbir_dilde_sizmaz(dil):
    y = _cagir(dil)
    assert _GIZLI not in y.text
    assert "Traceback" not in y.text
