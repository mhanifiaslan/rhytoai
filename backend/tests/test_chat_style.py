"""Sohbet stili testleri: seçici RAG, kısa yanıt, API şeması.

Çalıştırma:  .venv\\Scripts\\python.exe -m pytest tests/test_chat_style.py -q
"""
import pytest
from fastapi.testclient import TestClient

from core import config
from main import app
from services import gemini_service, prompt_composer


@pytest.fixture(autouse=True)
def _kota_sifirla():
    """Aynı süreçte koşan diğer test dosyalarının (test_hardening) kota
    testlerini etkilememek için rate-limit sayaçlarını temizler."""
    yield
    mw = app.middleware_stack
    while mw is not None:
        if hasattr(mw, "_hits"):
            mw._hits.clear()
        mw = getattr(mw, "app", None)


def test_yonlendirici_sezgileri():
    # Selamlaşma / duygu / kısa onay: RAG atlanmalı
    assert not prompt_composer.should_use_rag("selam")
    assert not prompt_composer.should_use_rag("Merhaba, nasılsın?")
    assert not prompt_composer.should_use_rag("bugün biraz keyifsizim")
    assert not prompt_composer.should_use_rag("tamam, teşekkürler")
    # Kadim bilgi soruları: RAG kullanılmalı
    assert prompt_composer.should_use_rag("Merkür retrosu beni nasıl etkiler?")
    assert prompt_composer.should_use_rag("BaZi haritamda Day Master ne anlama geliyor?")
    assert prompt_composer.should_use_rag("Yükselenim Terazi, bu ne demek?")


def test_selamlasmada_rag_cagrilmaz(monkeypatch):
    """Selamlaşma mesajında ne RAG araması ne embedding çağrısı yapılmalı."""
    called = {"rag": False}

    def fake_retrieve(query, top_k=2, **k):
        called["rag"] = True
        return []

    monkeypatch.setattr("api.chat.retrieve_passages", fake_retrieve)
    monkeypatch.setattr(gemini_service, "chat",
                        lambda history, msg, **k: "Selam sana da!")

    with TestClient(app) as client:
        response = client.post("/api/v1/chat", json={"history": [], "message": "selam"})
        assert response.status_code == 200
        assert not called["rag"]


def test_bilgi_sorusunda_rag_cagrilir_ve_kirpilir(monkeypatch):
    """Bilgi sorusunda RAG çağrılır; pasajlar kırpılıp fısıltı olarak eklenir."""
    captured = {}
    long_passage = {"doc": "d", "title": "t", "text": "x" * 2000, "score": 0.9}

    monkeypatch.setattr("api.chat.retrieve_passages",
                        lambda q, top_k=2, **k: [long_passage] * 3)

    def fake_chat(history, msg, **k):
        captured["msg"] = msg
        return "Kısa dostane yanıt."

    monkeypatch.setattr(gemini_service, "chat", fake_chat)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/chat",
            json={"history": [], "message": "Merkür retrosu beni nasıl etkiler?"},
        )
        assert response.status_code == 200

    msg = captured["msg"]
    assert "ARKA PLAN FISILTISI" in msg

    # Kırpmanın ölçüsü PASAJLARIN kendisidir, prompt'un tamamı değil.
    #
    # Bu iddia eskiden `len(msg)` üzerindeydi ve sabit persona etiketleriyle
    # değişken pasaj içeriğini aynı bütçede topluyordu. Sonuç: etiketlere
    # bilinçli olarak bir cümle eklemek (harita fısıltısına "spesifik ol",
    # kaynak fısıltısına "kaynağın ahlaki yargısını aktarma") kırpma testini
    # kırıyordu — oysa kırpma kusursuz çalışıyordu. Test artık yalnızca
    # kendi konusunu ölçüyor.
    pasaj_satirlari = [s for s in msg.splitlines() if s.startswith("- x")]
    assert len(pasaj_satirlari) == 2, "en fazla 2 pasaj eklenmeli"
    for satir in pasaj_satirlari:
        # "- " öneki ve kırpma göstergesi "…" haricinde sınıra uymalı
        assert len(satir) <= prompt_composer.MAX_PASSAGE_CHARS + 4, (
            f"pasaj kırpılmamış: {len(satir)} karakter")


def test_api_semasi_degismedi(monkeypatch):
    """İstek/yanıt şeması korunmalı — istemci sözleşmesi.

    `conversation_id` Revize R4 ile eklendi (sohbet arşivi): istemci dönen
    kimliği izleyip sonraki turlarda geri gönderiyor. Alanın DÜŞMESİ artık
    sözleşme kırılmasıdır; bu test o günden beri üç alanı birden koruyor.
    """
    monkeypatch.setattr(gemini_service, "chat",
                        lambda history, msg, **k: "test yanıtı")

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/chat",
            json={
                "history": [{"sender": "USER", "text": "merhaba"},
                            {"sender": "AI", "text": "selam"}],
                "message": "nasılsın",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert set(body.keys()) == {"status", "reply", "conversation_id"}
        assert body["status"] == "success"
        assert isinstance(body["reply"], str)


@pytest.mark.skipif(not config.GEMINI_API_KEY, reason="GEMINI_API_KEY tanımlı değil")
def test_canli_yanit_kisa_ve_sohbet_havasinda():
    """Canlı Gemini ile tek örnek: yanıt makul kısalıkta ve markdown'sız."""
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/chat",
            json={"history": [], "message": "Merkür retrosu ne demek?"},
        )
        assert response.status_code == 200
        reply = response.json()["reply"]
        assert 0 < len(reply) < 700, f"Yanıt çok uzun ({len(reply)}): {reply[:200]}"
        assert "##" not in reply
        assert "**" not in reply
