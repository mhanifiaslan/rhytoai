"""Faz 1 testleri: paylaşımlı önbellek, burç yorumu kovaları ve /horoscope ucu.

Çalıştırma:  .venv\\Scripts\\python.exe -m pytest tests/test_horoscope.py -q
"""
import datetime as dt

import pytest
from fastapi.testclient import TestClient

from core import cache, config
from services import memory_service, report_service

# Uygulamanın tamamı kerykeion -> pyswisseph zincirine bağlı; pyswisseph'in
# derlenmiş hazır paketi her ortamda bulunmuyor (ör. Windows + Python 3.12).
# Önbellek, tarih kovası ve hafıza testleri bu zincire ihtiyaç duymadığı için
# yalnızca uç testleri atlanır.
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


@pytest.fixture(autouse=True)
def temiz_onbellek(tmp_path, monkeypatch):
    """Her test izole bir önbellek dizini ve boş bellek katmanıyla başlar."""
    monkeypatch.setattr(config, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(config, "CACHE_BACKEND", "file")
    cache._memory.clear()
    yield
    cache._memory.clear()


# --------------------------------------------------------------------------
# Tarih kovaları
# --------------------------------------------------------------------------

def test_gunluk_kova_tarihi_izler():
    gun = dt.date(2026, 7, 28)
    assert report_service._horoscope_bucket("daily", gun) == "2026-07-28"


def test_aylik_kova_ay_bazinda():
    assert report_service._horoscope_bucket("monthly", dt.date(2026, 7, 1)) == "2026-07"
    assert report_service._horoscope_bucket("monthly", dt.date(2026, 7, 31)) == "2026-07"


def test_haftalik_kova_iso_yil_sinirinda_bolunmez():
    """29 Aralık 2025 (Pazartesi) ile 1 Ocak 2026 aynı ISO haftasındadır.

    Naif bir '%Y-%W' biçimi burada iki farklı kova üretir ve yıl sınırında
    haftalık yorum aynı hafta içinde iki kez LLM'e giderdi.
    """
    pazartesi = report_service._horoscope_bucket("weekly", dt.date(2025, 12, 29))
    persembe = report_service._horoscope_bucket("weekly", dt.date(2026, 1, 1))
    assert pazartesi == persembe == "2026-W01"


def test_haftalik_kova_farkli_haftalari_ayirir():
    bu_hafta = report_service._horoscope_bucket("weekly", dt.date(2026, 7, 28))
    gelecek_hafta = report_service._horoscope_bucket("weekly", dt.date(2026, 8, 4))
    assert bu_hafta != gelecek_hafta


# --------------------------------------------------------------------------
# Önbellek katmanı
# --------------------------------------------------------------------------

def test_onbellek_yazip_okur():
    cache.set("test-anahtar", "kozmik deger", ttl_seconds=60)
    assert cache.get("test-anahtar") == "kozmik deger"


def test_suresi_dolmus_kayit_donmez():
    cache.set("eski-anahtar", "bayat", ttl_seconds=-1)
    assert cache.get("eski-anahtar") is None


def test_kalici_katmandan_bellege_yuklenir():
    """Bellek temizlense de kalıcı katmandan okunabilmeli (instance yeniden başlatma)."""
    cache.set("kalici-anahtar", "deger", ttl_seconds=60)
    cache._memory.clear()
    assert cache.get("kalici-anahtar") == "deger"


def test_bellek_katmani_sinirli_buyur():
    for i in range(cache._MEMORY_MAX_ENTRIES + 50):
        cache.set(f"anahtar-{i}", i, ttl_seconds=60)
    assert len(cache._memory) <= cache._MEMORY_MAX_ENTRIES


def test_kalici_katman_hatasi_istegi_dusurmez(monkeypatch):
    def patla(*args, **kwargs):
        raise RuntimeError("firestore erisilemiyor")

    monkeypatch.setattr(cache, "_persistent_set", patla)
    monkeypatch.setattr(cache, "_persistent_get", patla)

    cache.set("dayanikli", "deger", ttl_seconds=60)
    # Bellek katmanı yine de çalışır
    assert cache.get("dayanikli") == "deger"
    cache._memory.clear()
    # Kalıcı katman patlasa bile None döner, istisna fırlatmaz
    assert cache.get("dayanikli") is None


# --------------------------------------------------------------------------
# /reports/horoscope ucu
# --------------------------------------------------------------------------

def _client_basliklari(etiket: str) -> dict:
    """Her teste ayrı kota kovası verir (ratelimit anahtarı Authorization özetidir)."""
    return {"Authorization": f"Bearer test-{etiket}"}


@uygulama_gerekir
def test_horoscope_ucu_yorum_dondurur():
    with TestClient(app) as client:
        response = client.get("/api/v1/reports/horoscope/leo",
                              headers=_client_basliklari("leo"))
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["sign"] == "leo"
    assert data["sign_tr"] == "Aslan"
    assert data["period"] == "daily"
    assert data["reading"]
    assert data["generated_for"] == dt.date.today().isoformat()


@uygulama_gerekir
def test_horoscope_ucu_gecersiz_burcu_reddeder():
    with TestClient(app) as client:
        response = client.get("/api/v1/reports/horoscope/yilan",
                              headers=_client_basliklari("yilan"))
    assert response.status_code == 422


@uygulama_gerekir
def test_horoscope_ucu_gecersiz_donemi_reddeder():
    with TestClient(app) as client:
        response = client.get("/api/v1/reports/horoscope/aries?period=yillik",
                              headers=_client_basliklari("yillik"))
    assert response.status_code == 422


@uygulama_gerekir
def test_horoscope_onbellekten_okur():
    """Önbellek anahtarı kullanıcıdan bağımsız kurulmalı: önceden yazılan yorum
    doğrudan servis edilmeli, LLM'e gidilmemeli."""
    bucket = report_service._horoscope_bucket("weekly", dt.date.today())
    cache.set(report_service.horoscope_cache_key("pisces", "weekly", bucket, "tr"),
              "Önceden üretilmiş yorum.", ttl_seconds=600)

    with TestClient(app) as client:
        response = client.get("/api/v1/reports/horoscope/pisces?period=weekly",
                              headers=_client_basliklari("pisces"))

    data = response.json()["data"]
    assert data["cached"] is True
    assert data["reading"] == "Önceden üretilmiş yorum."
    assert data["sign_tr"] == "Balık"


@uygulama_gerekir
def test_horoscope_ucu_llm_cokerse_ayakta_kalir(monkeypatch):
    """LLM erişilemez olduğunda uç 500 vermez, yedek metinle 200 döner."""
    monkeypatch.setattr(report_service.gemini_service, "generate",
                        lambda prompt, **k: "")

    with TestClient(app) as client:
        response = client.get("/api/v1/reports/horoscope/scorpio?period=monthly",
                              headers=_client_basliklari("scorpio"))

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["fallback"] is True
    assert "Akrep" in data["reading"]


# --------------------------------------------------------------------------
# horoscope_reading — uç swisseph'e bağlı olduğu için servis seviyesinde
# doğrulanır (önbellek anahtarı, TTL, fallback davranışı).
# --------------------------------------------------------------------------

SAHTE_GOKYUZU = {
    "moon_phase": {"name": "Dolunay", "emoji": "🌕", "illumination": 98},
    "retrogrades": ["Merkür"],
    "aspects": [{"p1": "Güneş", "p2": "Satürn", "aspect": "kare"}],
}


def test_horoscope_reading_onbellekten_okur():
    """Anahtar (burç, dönem, tarih kovası) ile kurulmalı — kullanıcı içermemeli."""
    bucket = report_service._horoscope_bucket("daily", dt.date.today())
    cache.set(report_service.horoscope_cache_key("leo", "daily", bucket, "tr"),
              "Hazır yorum.", ttl_seconds=600)

    sonuc = report_service.horoscope_reading("leo", "daily", SAHTE_GOKYUZU)

    assert sonuc["cached"] is True
    assert sonuc["text"] == "Hazır yorum."
    assert sonuc["generated_for"] == bucket


def test_horoscope_onbellek_isabetinde_rag_ve_llm_calismaz(monkeypatch):
    """Önbellek isabeti en sık yoldur; o yolda ne RAG araması ne LLM çağrısı
    yapılmalı. Aksi halde her istek boşuna embedding maliyeti üretir."""
    bucket = report_service._horoscope_bucket("daily", dt.date.today())
    cache.set(report_service.horoscope_cache_key("taurus", "daily", bucket, "tr"),
              "Hazır yorum.", ttl_seconds=600)

    rag_cagrildi: list[int] = []
    monkeypatch.setattr(report_service, "retrieve_context",
                        lambda *a, **k: rag_cagrildi.append(1) or "")
    monkeypatch.setattr(report_service.gemini_service, "generate",
                        lambda prompt, **k: pytest.fail("Önbellek isabetinde LLM'e gidilmemeli"))

    sonuc = report_service.horoscope_reading("taurus", "daily", SAHTE_GOKYUZU)

    assert sonuc["cached"] is True
    assert sonuc["generated_for"] == bucket
    assert rag_cagrildi == []


def test_horoscope_reading_ayni_donemde_tek_uretim():
    """İki farklı 'kullanıcı' aynı dönemde aynı önbellek girdisini paylaşır."""
    report_service.horoscope_reading("virgo", "weekly", SAHTE_GOKYUZU)
    cache.set(
        report_service.horoscope_cache_key(
            "virgo", "weekly",
            report_service._horoscope_bucket("weekly", dt.date.today()), "tr"),
        "Haftalık yorum.", ttl_seconds=600)

    ikinci = report_service.horoscope_reading("virgo", "weekly", SAHTE_GOKYUZU)
    assert ikinci["cached"] is True
    assert ikinci["text"] == "Haftalık yorum."


def test_horoscope_reading_llm_yanit_vermezse_fallback(monkeypatch):
    """LLM boş dönerse (anahtar yok, kota doldu, servis hatası) uç yine de
    anlamlı bir metin vermeli ve bu metin önbelleğe yazılmamalı."""
    monkeypatch.setattr(report_service.gemini_service, "generate", lambda prompt, **k: "")

    sonuc = report_service.horoscope_reading("aries", "daily", SAHTE_GOKYUZU)
    assert sonuc["fallback"] is True
    assert sonuc["cached"] is False
    assert "Koç" in sonuc["text"]

    # Yedek metin kalıcı hale gelmemeli: sonraki denemede yeniden üretilebilsin.
    bucket = report_service._horoscope_bucket("daily", dt.date.today())
    assert cache.get(
        report_service.horoscope_cache_key("aries", "daily", bucket, "tr")) is None


def test_horoscope_ttl_donem_suresiyle_hizali():
    """TTL'in tek görevi eski kayıtların birikmesini önlemek; kova süresinden
    kısa olursa aynı dönem içinde ikinci kez LLM'e gidilir."""
    assert report_service._HOROSCOPE_TTL["daily"] == 24 * 3600
    assert report_service._HOROSCOPE_TTL["weekly"] == 7 * 24 * 3600
    assert report_service._HOROSCOPE_TTL["monthly"] >= 31 * 24 * 3600


# --------------------------------------------------------------------------
# Kullanıcı hafızası şeması
# --------------------------------------------------------------------------

def test_hafiza_taninmayan_kategoriyi_atar():
    assert memory_service._normalize_fact(
        {"category": "saglik", "value": "bir sey"}) is None
    assert memory_service._normalize_fact(
        {"category": "work", "value": ""}) is None


def test_hafiza_olguyu_semaya_oturtur():
    fact = memory_service._normalize_fact({
        "category": "WORK",
        "key": "work.transition",
        "value": "x" * 500,
        "confidence": 5,
    })
    assert fact["category"] == "work"
    assert len(fact["value"]) == memory_service.MAX_FACT_CHARS
    assert fact["confidence"] == 1.0


def test_hafiza_sinir_asiminda_dusuk_guvenliyi_duser():
    facts = [
        {"key": f"k{i}", "category": "goal", "value": f"v{i}",
         "confidence": i / 100, "updatedAt": None}
        for i in range(memory_service.MAX_FACTS + 10)
    ]
    kalan = memory_service._prune_facts(facts)
    assert len(kalan) == memory_service.MAX_FACTS
    # En düşük güvenli olgular elenmiş olmalı
    assert all(f["confidence"] > 0.05 for f in kalan)


def test_firestore_yokken_hafiza_bos_doner(monkeypatch):
    monkeypatch.setattr(memory_service.firestore_client, "get_client", lambda: None)
    memory = memory_service.get_memory("olmayan-kullanici")
    assert memory["facts"] == []
    assert memory["moodTrail"] == []
    # Yazma denemesi de sessizce yok sayılmalı
    memory_service.record_mood("olmayan-kullanici", "kaygılı")
