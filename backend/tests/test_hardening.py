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


def test_llm_kotasi_dakikada_10():
    with TestClient(app) as client:
        # Var olmayan uç bile kotaya sayılır (yönlendirme öncesi middleware)
        for _ in range(10):
            response = client.post("/api/v1/reports/olmayan-uc")
            assert response.status_code != 429
        response = client.post("/api/v1/reports/olmayan-uc")
        assert response.status_code == 429
        assert "Retry-After" in response.headers
        assert "dakika" in response.json()["detail"]


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
