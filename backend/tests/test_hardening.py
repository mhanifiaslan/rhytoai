"""Faz 4 sertleştirme testleri: kota, güvenlik başlıkları, global hata yakalama.

Çalıştırma:  .venv\\Scripts\\python.exe -m pytest tests/test_hardening.py -q
"""
from fastapi.testclient import TestClient

from main import app


def test_kok_ucu_ve_guvenlik_basliklari():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert "Strict-Transport-Security" in response.headers


# Kota anahtarı Authorization başlığının özeti; her testin KENDİ başlığını
# vermesi kovaları ayırır. Ortak başlıkla koşan testler birbirinin kotasını
# yer ve sıraya bağlı sahte kırılmalar üretirdi (app modül düzeyinde tekil).
def _baslik(ad: str) -> dict[str, str]:
    return {"Authorization": f"Bearer kota-testi-{ad}"}


def test_llm_kotasi_dakikada_20():
    with TestClient(app) as client:
        # Var olmayan uç bile kotaya sayılır (yönlendirme öncesi middleware)
        for _ in range(20):
            response = client.post("/api/v1/reports/olmayan-uc",
                                   headers=_baslik("llm"))
            assert response.status_code != 429
        response = client.post("/api/v1/reports/olmayan-uc",
                               headers=_baslik("llm"))
        assert response.status_code == 429
        assert "Retry-After" in response.headers
        assert "dakika" in response.json()["detail"]


def test_sohbet_silme_sikici_kotaya_GIRMEZ():
    """KL-turu canlı bulgusu: `DELETE /chat/conversations/{id}` saf Firestore
    silmesidir ama önek eşleşmesi yüzünden LLM kotasını yiyordu — kullanıcı
    sohbet listesinde 10 konuyu silince 429 görüyordu."""
    with TestClient(app) as client:
        for i in range(25):  # eski kuralda 11.'de düşerdi
            response = client.delete(f"/api/v1/chat/conversations/k{i}",
                                     headers=_baslik("silme"))
            assert response.status_code != 429, f"{i}. silmede kota yandı"


def test_okuma_uclari_sikici_kotaya_GIRMEZ():
    """Durum/okuma uçları üretim yapmaz; önbellekten dönen rapor okumaları
    da jeton düşürmez. İkisi de genel kotada (60) olmalı."""
    with TestClient(app) as client:
        for _ in range(25):
            response = client.get("/api/v1/reports/iching/status",
                                  headers=_baslik("okuma"))
            assert response.status_code != 429


def test_genel_kota_yerinde_duruyor():
    """Gevşetme yalnız SINIFLANDIRMADA: genel kota (60/dk) hâlâ zorlanıyor."""
    with TestClient(app) as client:
        for _ in range(60):
            response = client.get("/api/v1/astrology/olmayan-uc",
                                  headers=_baslik("genel"))
            assert response.status_code != 429
        response = client.get("/api/v1/astrology/olmayan-uc",
                              headers=_baslik("genel"))
        assert response.status_code == 429


def test_global_hata_yakalayici_iz_sizdirmaz():
    @app.get("/_test_patlama")
    def _boom():
        raise RuntimeError("gizli ic detay")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/_test_patlama")
        assert response.status_code == 500
        body = response.json()
        assert body["status"] == "error"
        assert "gizli ic detay" not in response.text
        assert "Traceback" not in response.text
