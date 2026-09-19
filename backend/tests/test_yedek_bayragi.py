"""gz-2 bekçisi: üretilmemiş YORUM, rapor gibi dönmez.

Gemini kotası dolunca ``_cached_generate`` yedek metni döndürüyor ve harcanan
jetonu iade ediyor. Bu bayrak uçlarda DÜŞÜYORDU (yalnız /horoscope ve /dyad
taşıyordu): kullanıcı üç cümlelik jenerik paragrafı ürün sanıyor, jeton
iadesini de öğrenmiyor ve istemcideki ``report_generated`` sayacı "üretildi"
diyordu.

Üç katman ayrı ayrı sınanır, çünkü üç ayrı kusur:
  1. ``_cached_generate`` ``refunded`` bayrağını ÜRETİYOR mu — ve jeton
     harcanmayan uçta (günlük okuma) YALAN SÖYLEMİYOR mu.
  2. Uçlar bu iki bayrağı yanıt gövdesinde TAŞIYOR mu.
  3. Üretim hatası yığın izi ile mi loglanıyor — yedek metin artık kullanıcıya
     "ürünü göremedin" demek olduğu için kotayı (429) ağır hatadan ayırmak
     gerekiyor.

Çalıştırma:  .venv\\Scripts\\python.exe -m pytest tests/test_yedek_bayragi.py -q
"""
from __future__ import annotations

import datetime as dt
import logging

import pytest
from fastapi.testclient import TestClient

from core import entitlements, wallet
from core.auth import AuthUser, get_current_user
from services import report_service

try:
    from main import app
    _APP_IMPORT_ERROR = None
except Exception as exc:  # pragma: no cover - ortama bağlı
    app = None
    _APP_IMPORT_ERROR = str(exc)

uygulama_gerekir = pytest.mark.skipif(
    _APP_IMPORT_ERROR is not None,
    reason=f"FastAPI uygulaması içe aktarılamadı: {_APP_IMPORT_ERROR}",
)

DOGUM = {"name": "Ada", "year": 1994, "month": 8, "day": 11,
         "hour": 9, "minute": 30, "city": "Izmir"}

ORANLAR = {"jawToCheek": 0.80, "mouthToFaceWidth": 0.41,
           "eyeSpacing": 0.45, "symmetry": 0.98,
           "upperThird": 0.33, "middleThird": 0.33, "lowerThird": 0.34,
           "widthToHeight": 0.70, "lipFullness": 0.05}

#: Yedek metne düşen üretimin taklidi: gerçek ``_cached_generate``'in döndüğü
#: sözlük şekli. Uçların bayrağı TAŞIYIP taşımadığını ölçmek için yeterli.
YEDEK_YANIT = {"text": "Üç cümlelik hazır paragraf.", "cached": False,
               "fallback": True, "refunded": True}
YEDEK_IADESIZ = {"text": "Üç cümlelik hazır paragraf.", "cached": False,
                 "fallback": True, "refunded": False}
GERCEK_YANIT = {"text": "Gerçek rapor.", "cached": False}


# ---------------------------------------------------------------------------
# 1. Katman: `_cached_generate` bayrağı ÜRETİYOR
# ---------------------------------------------------------------------------

@pytest.fixture()
def llm_dustu(monkeypatch, tmp_path):
    """Gemini hiç metin üretmiyor; önbellek de izole."""
    from core import cache, config
    monkeypatch.setattr(config, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(config, "CACHE_BACKEND", "file")
    cache._memory.clear()
    monkeypatch.setattr(report_service.gemini_service, "generate",
                        lambda prompt, **k: "")
    yield
    cache._memory.clear()


def test_iade_edilen_jeton_yanitta_SOYLENIR(llm_dustu):
    iadeler: list[str] = []
    sonuc = report_service._cached_generate(
        "gz2-iadeli", "istem", "YEDEK METİN",
        refund=lambda: bool(iadeler.append("natal")) or True)

    assert sonuc["fallback"] is True
    assert sonuc["refunded"] is True, "istemci bunu kullanıcıya söyleyecek"
    assert iadeler == ["natal"], "iade gerçekten yapılmalı"


def test_jeton_harcamayan_ucta_iade_CUMLESI_KURULMAZ(llm_dustu):
    """Günlük okuma jeton harcamaz: "jetonun iade edildi" demek YALAN olurdu.

    Bayrak bu yüzden istemcide sabitlenemez; üretim yerinden gelmek zorunda.
    """
    sonuc = report_service._cached_generate("gz2-iadesiz", "istem", "YEDEK")

    assert sonuc["fallback"] is True
    assert sonuc["refunded"] is False


def test_basarili_uretimde_fallback_bayragi_HIC_YOK(monkeypatch, tmp_path):
    """Yoksa her rapor istemcide hataya dönerdi."""
    from core import cache, config
    monkeypatch.setattr(config, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(config, "CACHE_BACKEND", "file")
    cache._memory.clear()
    monkeypatch.setattr(report_service.gemini_service, "generate",
                        lambda prompt, **k: "Gerçek metin.")
    monkeypatch.setattr(report_service.fact_guard, "enforce",
                        lambda t, p, **k: (t, True))

    sonuc = report_service._cached_generate("gz2-basarili", "istem", "YEDEK")

    assert sonuc.get("fallback", False) is False
    assert sonuc.get("refunded", False) is False


# ---------------------------------------------------------------------------
# 2. Katman: UÇLAR bayrağı TAŞIYOR
# ---------------------------------------------------------------------------

@pytest.fixture()
def abone(monkeypatch):
    """Ücretli abone; cihaz kilidi ve cüzdan devre dışı.

    Testin konusu jeton bakiyesi ya da harita hesabı değil, yanıtın
    DÜRÜSTLÜĞÜ: uç, üretimden gelen bayrağı gövdeye taşıyor mu?
    """
    from core import device
    app.dependency_overrides[get_current_user] = lambda: AuthUser(
        uid="gz2", email="a@b.c", admin=False, auth_time=1000)
    monkeypatch.setattr(entitlements, "FORCE_PLUS", False)
    monkeypatch.setattr(entitlements, "is_subscriber", lambda uid: True)
    monkeypatch.setattr(entitlements, "user_local_date",
                        lambda uid: dt.date(2026, 9, 18))
    monkeypatch.setattr(device, "enforce_single_device",
                        lambda *a, **k: None)
    monkeypatch.setattr(wallet, "spender", lambda uid, ozellik, **k: None)
    monkeypatch.setattr(wallet, "refund_spend",
                        lambda uid, ozellik: True)
    yield
    app.dependency_overrides.clear()


@pytest.fixture()
def harita_sahte(monkeypatch):
    """Efemeris ve yerelleştirme devre dışı: uç yalnız sözlük kuruyor."""
    from api import reports
    harita = {"sun_sign": "Leo", "moon_sign": "Aries", "ascendant": "Libra",
              "planets": {}}
    monkeypatch.setattr(reports.astro_service, "get_natal_chart",
                        lambda **k: harita)
    monkeypatch.setattr(reports.astro_service, "subject_kwargs", lambda d: {})
    monkeypatch.setattr(reports, "get_bazi_chart", lambda **k: {"pillars": {}})
    monkeypatch.setattr(reports, "get_sky_now",
                        lambda: {"moon_phase": None, "retrogrades": []})
    monkeypatch.setattr(reports.prompts, "localize_sky",
                        lambda lang, sky: {"moon_phase": None,
                                           "retrogrades": []})
    monkeypatch.setattr(reports.prompts, "localize_chart",
                        lambda lang, c: c)
    monkeypatch.setattr(reports.prompts, "localize_bazi", lambda lang, c: c)
    return reports


@uygulama_gerekir
def test_natal_ucu_bayraklari_TASIR(abone, harita_sahte, monkeypatch):
    monkeypatch.setattr(harita_sahte.report_service, "natal_report",
                        lambda *a, **k: YEDEK_YANIT)

    with TestClient(app) as client:
        yanit = client.post("/api/v1/reports/natal", json=DOGUM)

    assert yanit.status_code == 200, yanit.text
    veri = yanit.json()["data"]
    assert veri["fallback"] is True, "yedek metin rapor gibi döndü"
    assert veri["refunded"] is True, "jeton iadesi söylenmedi"


@uygulama_gerekir
def test_bazi_ucu_bayraklari_HARITAYLA_BIRLIKTE_tasir(abone, harita_sahte,
                                                     monkeypatch):
    """BaZi'de bayrak haritayı GÖTÜRMEZ, ona eşlik eder.

    Harita deterministik hesap ve ücreti ödendi; eksik olan yalnız yorum.
    Sekme bu iki bayrağa bakıp haritayı çiziyor, yorumun yerine dürüst cümleyi
    koyuyor — bu yüzden `chart` yanıtta DURMAK ZORUNDA.
    """
    monkeypatch.setattr(harita_sahte.report_service, "bazi_report",
                        lambda *a, **k: YEDEK_YANIT)

    with TestClient(app) as client:
        yanit = client.post("/api/v1/reports/bazi", json=DOGUM)

    assert yanit.status_code == 200, yanit.text
    veri = yanit.json()["data"]
    assert veri["fallback"] is True
    assert veri["refunded"] is True
    assert veri["chart"] is not None, "ölçülmüş harita yanıttan düştü"


@uygulama_gerekir
def test_gunluk_okuma_bayragi_tasir_ama_IADE_YOK(abone, harita_sahte,
                                                 monkeypatch):
    """Günlük okuma jeton harcamaz; istemci iade cümlesini KURMAYACAK."""
    monkeypatch.setattr(harita_sahte.report_service, "daily_reading",
                        lambda *a, **k: YEDEK_IADESIZ)

    with TestClient(app) as client:
        yanit = client.post("/api/v1/reports/daily", json=DOGUM)

    assert yanit.status_code == 200, yanit.text
    veri = yanit.json()["data"]
    assert veri["fallback"] is True
    assert veri["refunded"] is False


@uygulama_gerekir
def test_firaset_ucu_bayraklari_TASIR(abone, monkeypatch):
    from api import face_reading
    monkeypatch.setattr(face_reading.consent_service, "has_face_consent",
                        lambda uid: True)
    monkeypatch.setattr(face_reading.profile_service, "get_profile",
                        lambda uid: {})
    monkeypatch.setattr(face_reading.chart_context, "chart_whisper",
                        lambda *a, **k: None)
    monkeypatch.setattr(face_reading.report_service, "firasa_report",
                        lambda *a, **k: YEDEK_YANIT)

    with TestClient(app) as client:
        yanit = client.post("/api/v1/face/reading", json=ORANLAR)

    assert yanit.status_code == 200, yanit.text
    govde = yanit.json()
    assert govde["fallback"] is True
    assert govde["refunded"] is True


@uygulama_gerekir
def test_gercek_rapor_bayraksiz_doner(abone, harita_sahte, monkeypatch):
    """Bayrak yoksa `False` gelmeli; aksi halde her rapor hataya dönerdi."""
    monkeypatch.setattr(harita_sahte.report_service, "natal_report",
                        lambda *a, **k: GERCEK_YANIT)

    with TestClient(app) as client:
        yanit = client.post("/api/v1/reports/natal", json=DOGUM)

    veri = yanit.json()["data"]
    assert veri["fallback"] is False
    assert veri["refunded"] is False


# ---------------------------------------------------------------------------
# 3. Katman: üretim hatası YIĞIN İZİYLE loglanır
# ---------------------------------------------------------------------------

class _Patlayan:
    """Kotası dolmuş istemci taklidi."""

    class models:
        @staticmethod
        def generate_content(*a, **k):
            raise RuntimeError("429 RESOURCE_EXHAUSTED")


def test_uretim_hatasi_YIGIN_IZIYLE_loglanir(monkeypatch, caplog):
    """Yedek metin artık kullanıcıya "ürünü göremedin" demek (gz-2).

    Kotayı (429) ağır hatadan ayırmak için yığın izi ŞART; `logger.warning`
    onu taşımaz ve bu satır artık bir ÜRÜN kaybının tek izi.
    """
    from services import gemini_service
    monkeypatch.setattr(gemini_service, "_get_client", lambda: _Patlayan())
    with caplog.at_level(logging.WARNING, logger=gemini_service.__name__):
        assert gemini_service.generate("istem") is None
    kayitlar = [r for r in caplog.records
                if "Gemini üretim hatası" in r.getMessage()]
    assert kayitlar, "üretim hatası hiç loglanmadı"
    assert kayitlar[0].exc_info is not None, (
        "logger.warning yığın izi taşımaz; kota ile ağır hata ayırt edilemez")
