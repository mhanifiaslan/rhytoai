"""Faz 3 testleri: dil çözümleme, dile göre persona/prompt ve önbellek ayrımı.

Çalıştırma:  .venv\\Scripts\\python.exe -m pytest tests/test_i18n.py -q
"""
import datetime as dt

import pytest
from fastapi.testclient import TestClient

from core import cache, config, i18n
from services import prompt_composer, prompts, report_service

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

SAHTE_GOKYUZU = {
    "moon_phase": {"name": "Full Moon", "emoji": "🌕", "illumination": 98},
    "retrogrades": ["Mercury"],
    "aspects": [{"p1": "Sun", "p2": "Saturn", "aspect": "square"}],
}


@pytest.fixture(autouse=True)
def temiz_onbellek(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(config, "CACHE_BACKEND", "file")
    cache._memory.clear()
    yield
    cache._memory.clear()


# --------------------------------------------------------------------------
# Accept-Language çözümleme
# --------------------------------------------------------------------------

@pytest.mark.parametrize("baslik,beklenen", [
    (None, "tr"),
    ("", "tr"),
    ("tr", "tr"),
    ("en", "en"),
    ("en-US", "en"),            # bölgesel varyant ana dile katlanır
    ("en-GB,en;q=0.9", "en"),
    ("de", "tr"),               # desteklenmeyen dil varsayılana düşer
    ("de,en;q=0.8", "en"),      # ilk desteklenen dil seçilir
    ("tr;q=0.3,en;q=0.9", "en"),  # ağırlık sırası dikkate alınır
    ("bozuk;q=abc", "tr"),      # hatalı q sessizce yok sayılır
])
def test_dil_cozumleme(baslik, beklenen):
    assert i18n.resolve_language(baslik) == beklenen


def test_desteklenen_diller_ve_varsayilan_tutarli():
    assert i18n.DEFAULT in i18n.SUPPORTED
    # Her desteklenen dilin prompt modülü olmalı
    for kod in i18n.SUPPORTED:
        modul = prompts.get(kod)
        assert modul.SYSTEM_INSTRUCTION
        assert modul.CHAT_SYSTEM_INSTRUCTION
        assert len(modul.SIGN_NAMES) == 12


# --------------------------------------------------------------------------
# Persona ve şablonlar dile göre değişir
# --------------------------------------------------------------------------

def test_personalar_ayri_metinler():
    tr = prompts.get("tr")
    en = prompts.get("en")
    assert tr.SYSTEM_INSTRUCTION != en.SYSTEM_INSTRUCTION
    # İngilizce persona İngilizce olmalı, çeviri artığı taşımamalı
    assert "NO FLATTERY" in en.SYSTEM_INSTRUCTION
    assert "POHPOHLAMA" not in en.SYSTEM_INSTRUCTION
    assert "POHPOHLAMA YOK" in tr.SYSTEM_INSTRUCTION


def test_her_iki_dilde_ayni_yasaklar_var():
    """Dürüstlük ve yasak alan kuralları dile göre gevşemez."""
    tr, en = prompts.get("tr"), prompts.get("en")
    for anahtar in ("hamile", "ölüm", "hukuki"):
        assert anahtar in tr.SYSTEM_INSTRUCTION.lower()
    for anahtar in ("pregnancy", "death", "legal advice"):
        assert anahtar in en.SYSTEM_INSTRUCTION.lower()


def test_burc_adlari_dile_gore():
    assert prompts.sign_name("tr", "leo") == "Aslan"
    assert prompts.sign_name("en", "leo") == "Leo"
    assert prompts.sign_name("de", "leo") == "Aslan"  # varsayılana düşer


def test_taninmayan_dil_varsayilan_modul():
    assert prompts.get("de") is prompts.get("tr")
    assert prompts.get(None) is prompts.get("tr")


# --------------------------------------------------------------------------
# Önbellek dile göre ayrışır — en kritik davranış
# --------------------------------------------------------------------------

def test_burc_onbellek_anahtari_dili_icerir():
    """Dil anahtara girmezse İngilizce kullanıcı Türkçe yorumu görür."""
    tr = report_service.horoscope_cache_key("leo", "daily", "2026-07-29", "tr")
    en = report_service.horoscope_cache_key("leo", "daily", "2026-07-29", "en")
    assert tr != en


def test_turkce_onbellek_ingilizce_istegi_karsilamaz(monkeypatch):
    """Türkçe üretilmiş yorum, İngilizce isteğe servis edilmemeli."""
    bucket = report_service._horoscope_bucket("daily", dt.date.today())
    cache.set(report_service.horoscope_cache_key("leo", "daily", bucket, "tr"),
              "Türkçe yorum.", ttl_seconds=600)

    uretilen: list[str] = []

    def sahte_generate(prompt, **k):
        uretilen.append(k.get("lang") or "?")
        return "English reading."

    monkeypatch.setattr(report_service.gemini_service, "generate", sahte_generate)
    monkeypatch.setattr(report_service, "retrieve_context", lambda *a, **k: "")

    sonuc = report_service.horoscope_reading("leo", "daily", SAHTE_GOKYUZU,
                                             lang="en")

    assert sonuc["cached"] is False, "Türkçe önbellek İngilizceye servis edildi"
    assert sonuc["text"] == "English reading."
    assert uretilen == ["en"], "üretim İngilizce persona ile yapılmalı"


def test_gunluk_okuma_onbellegi_dile_gore_ayrisir(monkeypatch):
    monkeypatch.setattr(report_service, "retrieve_context", lambda *a, **k: "")
    monkeypatch.setattr(report_service.memory_service, "memory_context",
                        lambda uid, max_chars=600: "")
    monkeypatch.setattr(report_service.gemini_service, "generate",
                        lambda prompt, **k: f"reading-{k.get('lang')}")

    natal = {"sun_sign": "Leo", "moon_sign": "Aries", "ascendant": "Libra"}
    tr = report_service.daily_reading("u1", natal, SAHTE_GOKYUZU, lang="tr")
    en = report_service.daily_reading("u1", natal, SAHTE_GOKYUZU, lang="en")

    assert tr["text"] == "reading-tr"
    assert en["text"] == "reading-en", "aynı kullanıcı için diller karıştı"


# --------------------------------------------------------------------------
# Prompt şablonları dile göre doldurulur
# --------------------------------------------------------------------------

def test_ingilizce_burc_promptu_ingilizce(monkeypatch):
    yakalanan: dict[str, str] = {}

    def sahte_generate(prompt, **k):
        yakalanan["prompt"] = prompt
        return "ok"

    monkeypatch.setattr(report_service.gemini_service, "generate", sahte_generate)
    monkeypatch.setattr(report_service, "retrieve_context", lambda *a, **k: "")

    report_service.horoscope_reading("leo", "weekly", SAHTE_GOKYUZU, lang="en")

    prompt = yakalanan["prompt"]
    assert "TASK:" in prompt
    assert "Leo" in prompt
    assert "GÖREV" not in prompt, "İngilizce prompt'a Türkçe sızdı"


@uygulama_gerekir
def test_sohbet_gokyuzu_ozeti_dile_gore(monkeypatch):
    """Gökyüzü bloğu prompt'a giriyor; Türkçe etiketler İngilizce prompt'un
    içinde kalırsa model iki dil arasında sallanır."""
    from api import chat as chat_api

    monkeypatch.setattr(chat_api, "get_sky_now", lambda: SAHTE_GOKYUZU)

    tr = chat_api._sky_summary("tr")
    en = chat_api._sky_summary("en")

    assert "Ay evresi" in tr and "Retro gezegenler" in tr
    assert "Moon phase" in en and "Retrograde planets" in en
    assert "Ay evresi" not in en, "İngilizce gökyüzü özetine Türkçe sızdı"


def test_sohbet_gokyuzu_bos_retro_etiketi_dile_gore(monkeypatch):
    from api import chat as chat_api

    monkeypatch.setattr(chat_api, "get_sky_now",
                        lambda: {**SAHTE_GOKYUZU, "retrogrades": []})

    assert "yok" in chat_api._sky_summary("tr")
    assert "none" in chat_api._sky_summary("en")


def test_fisilti_etiketleri_dile_gore():
    tr = prompt_composer.compose_chat_message(
        "selam", [], chart="- Güneş: Aslan", lang="tr")
    en = prompt_composer.compose_chat_message(
        "hello", [], chart="- Sun: Leo", lang="en")

    assert "KULLANICININ HARİTASI" in tr
    assert "THE READER'S CHART" in en
    assert "KULLANICININ MESAJI: selam" in tr
    assert "THE READER'S MESSAGE: hello" in en


# --------------------------------------------------------------------------
# Uç davranışı
# --------------------------------------------------------------------------

@uygulama_gerekir
def test_burc_ucu_dili_yansitir(monkeypatch):
    monkeypatch.setattr(report_service.gemini_service, "generate",
                        lambda prompt, **k: f"reading in {k.get('lang')}")
    monkeypatch.setattr(report_service, "retrieve_context", lambda *a, **k: "")

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/reports/horoscope/leo",
            headers={"Authorization": "Bearer test-en",
                     "Accept-Language": "en-US,en;q=0.9"},
        )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["lang"] == "en"
    assert data["sign_name"] == "Leo"
    assert data["reading"] == "reading in en"


@uygulama_gerekir
def test_baslik_yoksa_turkce(monkeypatch):
    monkeypatch.setattr(report_service.gemini_service, "generate",
                        lambda prompt, **k: f"yorum {k.get('lang')}")
    monkeypatch.setattr(report_service, "retrieve_context", lambda *a, **k: "")

    with TestClient(app) as client:
        response = client.get("/api/v1/reports/horoscope/virgo",
                              headers={"Authorization": "Bearer test-tr"})

    data = response.json()["data"]
    assert data["lang"] == "tr"
    assert data["sign_name"] == "Başak"


# --------------------------------------------------------------------------
# Tüm rapor türleri dile göre üretilir
# --------------------------------------------------------------------------

def test_tum_sablonlar_iki_dilde_var():
    """Bir şablon yalnızca bir dilde tanımlıysa o dilde AttributeError alırız."""
    zorunlu = [
        "SYSTEM_INSTRUCTION", "CHAT_SYSTEM_INSTRUCTION",
        "HOROSCOPE", "HOROSCOPE_FALLBACK", "DAILY", "DAILY_FALLBACK",
        "DYAD", "DYAD_FALLBACK", "NATAL", "NATAL_FALLBACK",
        "BAZI", "BAZI_FALLBACK", "ICHING", "ICHING_TRANSFORMED",
        "SYNASTRY", "SYNASTRY_FALLBACK", "MEMORY_BLOCK",
        "WHISPER_RAG", "WHISPER_MEMORY", "WHISPER_CHART", "WHISPER_SKY",
        "SKY_MOON", "SKY_RETROS", "SKY_ASPECTS",
        "USER_MESSAGE_LABEL", "NONE_LABEL", "NO_ASPECTS",
        "SIGN_NAMES", "PERIOD_NAMES", "PERIOD_LENGTHS",
    ]
    for kod in i18n.SUPPORTED:
        modul = prompts.get(kod)
        for ad in zorunlu:
            assert hasattr(modul, ad), f"{kod} dilinde {ad} eksik"


def test_sinastri_promptuna_uyum_skoru_girmez(monkeypatch):
    """Skor hesaplanıyor ama prompt'a girmemeli: ilişkiyi tek sayıya indirgemek
    ikili dinamikte de yasak, sinastride de olmamalı."""
    yakalanan: dict[str, str] = {}
    monkeypatch.setattr(report_service.gemini_service, "generate",
                        lambda prompt, **k: yakalanan.update(p=prompt) or "ok")
    monkeypatch.setattr(report_service, "retrieve_context", lambda *a, **k: "")

    sinastri = {
        "person1": {"name": "Ada", "sun": {"sign_tr": "Leo"},
                    "moon": {"sign_tr": "Aries"}},
        "person2": {"name": "Deniz", "sun": {"sign_tr": "Libra"},
                    "moon": {"sign_tr": "Pisces"}},
        "relationship_score": {"score": 74, "description": "high"},
        "aspects": [],
    }
    report_service.synastry_report("u", sinastri, lang="en")

    assert "74" not in yakalanan["p"]
    assert "compatibility score" in yakalanan["p"].lower()


def test_natal_ve_bazi_onbellegi_dile_gore_ayrisir(monkeypatch):
    uretilen: list[str] = []
    monkeypatch.setattr(report_service.gemini_service, "generate",
                        lambda prompt, **k: uretilen.append(k.get("lang")) or "x")
    monkeypatch.setattr(report_service, "retrieve_context", lambda *a, **k: "")

    natal = {"sun_sign": "Leo", "moon_sign": "Aries", "ascendant": "Libra",
             "points": [], "aspects": []}
    report_service.natal_report("u", natal, lang="tr")
    report_service.natal_report("u", natal, lang="en")

    # İki ayrı üretim olmalı; tek anahtar olsaydı ikincisi önbellekten gelirdi
    assert uretilen == ["tr", "en"]
