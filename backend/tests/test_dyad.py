"""Faz 5 testleri: günlük ikili dinamik (dyad) ucu.

Çalıştırma:  .venv\\Scripts\\python.exe -m pytest tests/test_dyad.py -q
"""
import datetime as dt

import pytest
from fastapi.testclient import TestClient

from core import cache, config, entitlements
from services import profile_service, report_service

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

SAHTE_GOKYUZU = {
    "moon_phase": {"name": "Dolunay", "emoji": "🌕", "illumination": 97},
    "retrogrades": ["Merkür"],
    "aspects": [],
}

SAHTE_SINASTRI = {
    "person1": {"name": "Ada", "sun": {"sign_tr": "Aslan"}, "moon": {"sign_tr": "Yay"}},
    "person2": {"name": "Deniz", "sun": {"sign_tr": "Terazi"}, "moon": {"sign_tr": "Balık"}},
    "relationship_score": {"score": 74, "description": "yüksek"},
    "aspects": [
        {"p1_tr": "Venüs", "p2_tr": "Mars", "aspect_tr": "Üçgen", "orbit": 2.1},
    ],
}

# İstemcinin göndereceği tipik profil (ham doğum verisi dahil)
PROFIL_A = {
    "displayName": "Ada", "birthDate": "1994-08-11", "birthTime": "09:30",
    "birthCity": "Izmir", "sunSign": "Aslan",
}
PROFIL_B = {
    "displayName": "Deniz", "birthDate": "1991-10-02", "birthTime": "21:05",
    "birthCity": "Ankara", "sunSign": "Terazi",
}


@pytest.fixture(autouse=True)
def temiz_onbellek(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(config, "CACHE_BACKEND", "file")
    cache._memory.clear()
    yield
    cache._memory.clear()


# --------------------------------------------------------------------------
# Önbellek anahtarı
# --------------------------------------------------------------------------

def test_dyad_anahtari_cift_sirasindan_bagimsiz():
    """İki arkadaş aynı günü aynı metinle görmeli — anahtar simetrik olmalı."""
    gun = dt.date(2026, 7, 28)
    assert (report_service.dyad_cache_key("uid-a", "uid-b", gun)
            == report_service.dyad_cache_key("uid-b", "uid-a", gun))


def test_dyad_anahtari_gune_gore_degisir():
    assert (report_service.dyad_cache_key("a", "b", dt.date(2026, 7, 28))
            != report_service.dyad_cache_key("a", "b", dt.date(2026, 7, 29)))


def test_dyad_onbellekten_okur():
    anahtar = report_service.dyad_cache_key("a", "b", dt.date.today())
    cache.set(anahtar, "Hazır ikili okuma.", ttl_seconds=600)

    sonuc = report_service.dyad_reading("b", "a", "Ada", "Deniz",
                                        SAHTE_SINASTRI, SAHTE_GOKYUZU)
    assert sonuc["cached"] is True
    assert sonuc["text"] == "Hazır ikili okuma."


def test_dyad_onbellek_isabetinde_rag_ve_llm_calismaz(monkeypatch):
    anahtar = report_service.dyad_cache_key("a", "b", dt.date.today())
    cache.set(anahtar, "Hazır.", ttl_seconds=600)

    rag_cagrildi: list[int] = []
    monkeypatch.setattr(report_service, "retrieve_context",
                        lambda *a, **k: rag_cagrildi.append(1) or "")
    monkeypatch.setattr(report_service.gemini_service, "generate",
                        lambda prompt, **k: pytest.fail("Önbellek isabetinde LLM'e gidilmemeli"))

    report_service.dyad_reading("a", "b", "Ada", "Deniz",
                                SAHTE_SINASTRI, SAHTE_GOKYUZU)
    assert rag_cagrildi == []


# --------------------------------------------------------------------------
# İçerik kuralları
# --------------------------------------------------------------------------

def test_dyad_prompta_uyum_skoru_girmez(monkeypatch):
    """Kalıcı uyum skoru ürün kararıyla yasak; sinastri skoru prompt'a sızmamalı."""
    yakalanan: dict[str, str] = {}

    def sahte_generate(prompt: str, **k) -> str:
        yakalanan["prompt"] = prompt
        return "üretilmiş metin"

    monkeypatch.setattr(report_service.gemini_service, "generate", sahte_generate)
    report_service.dyad_reading("a", "b", "Ada", "Deniz",
                                SAHTE_SINASTRI, SAHTE_GOKYUZU)

    prompt = yakalanan["prompt"]
    assert "74" not in prompt
    assert "UYUM SKORU" not in prompt
    # Prompt modele skoru açıkça yasaklamalı
    assert "puan" in prompt.lower()


def test_dyad_llm_yanit_vermezse_fallback(monkeypatch):
    monkeypatch.setattr(report_service.gemini_service, "generate", lambda p, **k: "")
    sonuc = report_service.dyad_reading("a", "b", "Ada", "Deniz",
                                        SAHTE_SINASTRI, SAHTE_GOKYUZU)
    assert sonuc["fallback"] is True
    assert "Ada" in sonuc["text"] and "Deniz" in sonuc["text"]
    # Yedek metin önbelleğe yazılmamalı
    assert cache.get(report_service.dyad_cache_key("a", "b", dt.date.today())) is None


# --------------------------------------------------------------------------
# Profil dönüşümü
# --------------------------------------------------------------------------

def test_birth_kwargs_istemciyle_ayni_donusumu_yapar():
    kwargs = profile_service.birth_kwargs(PROFIL_A)
    assert kwargs["year"] == 1994 and kwargs["month"] == 8 and kwargs["day"] == 11
    assert kwargs["hour"] == 9 and kwargs["minute"] == 30
    assert kwargs["city"] == "Izmir"
    assert kwargs["name"] == "Ada"


def test_birth_kwargs_bozuk_veride_varsayilana_duser():
    kwargs = profile_service.birth_kwargs({"birthDate": "bozuk", "birthTime": "x"})
    assert kwargs["year"] == 2000 and kwargs["hour"] == 12
    assert kwargs["name"] == "Gezgin"


def test_firestore_yokken_arkadaslik_dogrulanamaz(monkeypatch):
    monkeypatch.setattr(profile_service.firestore_client, "get_client", lambda: None)
    assert profile_service.are_friends("a", "b") is False
    assert profile_service.get_profile("a") is None


def test_are_friends_cift_tarafli_dogrular(monkeypatch):
    """H2: tek taraflı 'accepted' arkadaşlık SAYILMAZ.

    Saldırgan yalnız kendi ağacına accepted yazabildiği için, tek taraflı
    kayıt dyad/dürtme tetiklememeli. Gerçek arkadaşlıkta iki taraf da
    accepted'tır."""
    # Sözde Firestore: {owner: {other: status}}
    dunya: dict[str, dict[str, str]] = {}

    def sahte_status(owner, other):
        return dunya.get(owner, {}).get(other)

    monkeypatch.setattr(profile_service, "_friend_status", sahte_status)

    # Tek taraflı (saldırgan S kendi ağacına V=accepted yazdı): SAYILMAZ.
    dunya["S"] = {"V": "accepted"}
    assert profile_service.are_friends("S", "V") is False

    # Karşı taraf da accepted (gerçek kabul): sayılır.
    dunya["V"] = {"S": "accepted"}
    assert profile_service.are_friends("S", "V") is True

    # Bir taraf 'incoming' (kabul edilmemiş davet): sayılmaz.
    dunya["V"]["S"] = "incoming"
    assert profile_service.are_friends("S", "V") is False


# --------------------------------------------------------------------------
# Uç davranışı
# --------------------------------------------------------------------------

def _basliklar(etiket: str) -> dict:
    return {"Authorization": f"Bearer test-{etiket}"}


@pytest.fixture
def abone(monkeypatch):
    """İkili dinamik Rytho+ içindedir; bu dosyadaki uç testleri abonelik
    kapısının ARKASINDAKİ davranışı ölçer. Kapının kendisi
    tests/test_entitlements.py'de test edilir."""
    monkeypatch.setattr(entitlements, "is_subscriber", lambda uid: True)


@uygulama_gerekir
def test_dyad_ucu_kendinle_okumayi_reddeder(abone, monkeypatch):
    from api import reports as reports_api

    with TestClient(app) as client:
        response = client.post("/api/v1/reports/dyad",
                               json={"friend_uid": "dev-user"},
                               headers=_basliklar("self"))
    assert response.status_code == 400
    assert reports_api  # modül yüklendi


@uygulama_gerekir
def test_dyad_ucu_arkadas_olmayani_reddeder(abone, monkeypatch):
    from api import reports as reports_api

    monkeypatch.setattr(reports_api.profile_service, "are_friends",
                        lambda a, b: False)

    with TestClient(app) as client:
        response = client.post("/api/v1/reports/dyad",
                               json={"friend_uid": "yabanci-uid"},
                               headers=_basliklar("stranger"))
    assert response.status_code == 403


@uygulama_gerekir
def test_dyad_ucu_ham_dogum_verisi_sizdirmaz(abone, monkeypatch):
    """Yanıt yalnızca türetilmiş alanlar içermeli; doğum tarihi/saati/şehri asla."""
    from api import reports as reports_api

    monkeypatch.setattr(reports_api.profile_service, "are_friends", lambda a, b: True)
    monkeypatch.setattr(reports_api.profile_service, "get_profile",
                        lambda uid: PROFIL_B if uid == "arkadas-uid" else PROFIL_A)
    monkeypatch.setattr(reports_api.astro_service, "get_synastry",
                        lambda p1, p2: SAHTE_SINASTRI)
    monkeypatch.setattr(reports_api, "get_sky_now", lambda: SAHTE_GOKYUZU)
    monkeypatch.setattr(report_service.gemini_service, "generate",
                        lambda prompt, **k: "İkinizin bugünkü ritmi.")

    with TestClient(app) as client:
        response = client.post("/api/v1/reports/dyad",
                               json={"friend_uid": "arkadas-uid"},
                               headers=_basliklar("ok"))

    assert response.status_code == 200
    govde = response.text
    for hassas in ("1991-10-02", "21:05", "Ankara", "1994-08-11", "09:30", "Izmir"):
        assert hassas not in govde, f"Ham doğum verisi sızdı: {hassas}"

    data = response.json()["data"]
    assert data["reading"] == "İkinizin bugünkü ritmi."
    assert data["friend_sun_sign"] == "Terazi"
    assert data["generated_for"] == dt.date.today().isoformat()
