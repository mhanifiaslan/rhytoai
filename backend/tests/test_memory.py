"""Faz 4 testleri: olgu çıkarımı ve hafızanın prompt'a enjeksiyonu.

Çalıştırma:  .venv\\Scripts\\python.exe -m pytest tests/test_memory.py -q
"""
import json

import pytest

from services import memory_extractor, memory_service, prompt_composer


# --------------------------------------------------------------------------
# Çıkarım tetikleme koşulları (maliyet kontrolü)
# --------------------------------------------------------------------------

def test_kisa_konusmada_cikarim_yapilmaz():
    """Tek "merhaba" turundan olgu çıkarmaya çalışmak boşa LLM çağrısıdır."""
    assert memory_extractor.should_extract([]) is False
    assert memory_extractor.should_extract(
        [{"sender": "USER", "text": "selam"}]) is False


def test_yeterince_uzun_konusmada_cikarim_yapilir():
    gecmis = [
        {"sender": "USER", "text": "selam"},
        {"sender": "AI", "text": "merhaba"},
        {"sender": "USER", "text": "işimden ayrılmayı düşünüyorum"},
    ]
    assert memory_extractor.should_extract(gecmis) is True


def test_ai_turlari_sayilmaz():
    gecmis = [{"sender": "AI", "text": f"cevap {i}"} for i in range(10)]
    assert memory_extractor.should_extract(gecmis) is False


def test_kota_dolduysa_llm_e_gidilmez(monkeypatch):
    """Günlük çıkarım hakkı bitince ek LLM çağrısı yapılmamalı."""
    gecmis = [{"sender": "USER", "text": f"mesaj {i}"} for i in range(4)]
    monkeypatch.setattr(memory_extractor.entitlements, "consume_quota",
                        lambda uid, key, limit: False)
    monkeypatch.setattr(memory_extractor.gemini_service, "extract_json",
                        lambda *a, **k: pytest.fail("kota dolarken LLM çağrılmamalı"))

    assert memory_extractor.extract_and_store("u", gecmis, "son mesaj") is None


# --------------------------------------------------------------------------
# Çıkarım ve şemaya oturtma
# --------------------------------------------------------------------------

def _cikarima_izin_ver(monkeypatch):
    monkeypatch.setattr(memory_extractor.entitlements, "consume_quota",
                        lambda uid, key, limit: True)


def test_cikarilan_olgular_hafizaya_yazilir(monkeypatch):
    _cikarima_izin_ver(monkeypatch)
    gecmis = [{"sender": "USER", "text": f"m{i}"} for i in range(4)]

    yanit = json.dumps({
        "facts": [
            {"category": "work", "key": "work.transition",
             "value": "yeni bir işe geçmeyi tartıyor", "confidence": 0.9},
        ],
        "mood": "kaygılı",
    })
    monkeypatch.setattr(memory_extractor.gemini_service, "extract_json",
                        lambda *a, **k: yanit)

    yazilan: list = []
    monkeypatch.setattr(memory_service, "upsert_facts",
                        lambda uid, facts: yazilan.append(facts) or {"facts": facts})
    ruh: list = []
    monkeypatch.setattr(memory_service, "record_mood",
                        lambda uid, mood, note="": ruh.append(mood))

    memory_extractor.extract_and_store("u", gecmis, "son mesaj")

    assert yazilan and yazilan[0][0]["key"] == "work.transition"
    assert ruh == ["kaygılı"]


def test_bozuk_json_istegi_dusurmez(monkeypatch):
    """Çıkarım en iyi çaba bir zenginleştirmedir; hata sohbeti etkilemez."""
    _cikarima_izin_ver(monkeypatch)
    gecmis = [{"sender": "USER", "text": f"m{i}"} for i in range(4)]
    monkeypatch.setattr(memory_extractor.gemini_service, "extract_json",
                        lambda *a, **k: "{bu json degil")

    assert memory_extractor.extract_and_store("u", gecmis, "x") is None


def test_saglik_kategorisi_sematik_olarak_reddedilir():
    """Sağlık verisi hiç tutulmuyor; model yine de gönderirse şema atar."""
    assert "health" not in memory_service.CATEGORIES
    assert memory_service._normalize_fact(
        {"category": "health", "value": "ilaç kullanıyor"}) is None


def test_konusma_metni_son_mesaji_icerir():
    gecmis = [{"sender": "USER", "text": "ilk"}, {"sender": "AI", "text": "yanit"}]
    metin = memory_extractor._conversation_text(gecmis, "son soru")
    assert "Kullanıcı: ilk" in metin
    assert "Rytho: yanit" in metin
    assert metin.strip().endswith("Kullanıcı: son soru")


# --------------------------------------------------------------------------
# Prompt'a enjeksiyon
# --------------------------------------------------------------------------

def test_hafiza_yoksa_mesaj_degismez():
    assert prompt_composer.compose_chat_message("selam", [], memory="") == "selam"


def test_hafiza_fisilti_olarak_eklenir():
    sonuc = prompt_composer.compose_chat_message(
        "bugün nasıl geçer", [], memory="- (work) yeni işe geçmeyi tartıyor")

    assert "yeni işe geçmeyi tartıyor" in sonuc
    assert "KULLANICININ MESAJI: bugün nasıl geçer" in sonuc
    # Modele hafızayı ilan etmemesi söylenmeli; aksi halde kullanıcıya
    # "hakkında tuttuğum notlar" okumak gibi olur.
    assert "ilan ETME" in sonuc or "ilan etme" in sonuc.lower()


def test_hafiza_ve_pasajlar_birlikte_eklenir():
    sonuc = prompt_composer.compose_chat_message(
        "merkür retrosu ne yapar",
        [{"text": "Merkür retrosu iletişimde yavaşlama getirir."}],
        memory="- (work) yeni işe geçmeyi tartıyor",
    )
    assert "ARKA PLAN FISILTISI" in sonuc
    assert "HATIRLADIKLARIN" in sonuc
    assert sonuc.rstrip().endswith("KULLANICININ MESAJI: merkür retrosu ne yapar")


def test_hafiza_celisirse_son_soylenen_gecerli():
    """Hafıza eskiyebilir; model kullanıcının son sözünü esas almalı."""
    sonuc = prompt_composer.compose_chat_message(
        "artık o işte değilim", [], memory="- (work) X şirketinde çalışıyor")
    assert "SON söylediği" in sonuc


# --------------------------------------------------------------------------
# Harita ve gökyüzü enjeksiyonu
# --------------------------------------------------------------------------

def test_harita_ozeti_turetilmis_alanlari_alir():
    from services.profile_service import chart_summary

    ozet = chart_summary({
        "sunSign": "Kova ♒", "moonSign": "Aslan ♌", "ascendant": "Terazi ♎",
        "mizac": "Demevi", "wuXingElement": "Ateş",
    })
    assert "Kova" in ozet and "Aslan" in ozet and "Terazi" in ozet
    assert "Demevi" in ozet and "Ateş" in ozet


def test_harita_ozetine_ham_dogum_verisi_girmez():
    """Modelin doğum tarihini/saatini/şehrini bilmesine gerek yok."""
    from services.profile_service import chart_summary

    ozet = chart_summary({
        "sunSign": "Kova", "birthDate": "1985-02-03",
        "birthTime": "04:15", "birthCity": "Bursa",
    })
    for hassas in ("1985-02-03", "04:15", "Bursa"):
        assert hassas not in ozet, f"ham doğum verisi sızdı: {hassas}"


def test_bos_profil_bos_ozet():
    from services.profile_service import chart_summary
    assert chart_summary(None) == ""
    assert chart_summary({}) == ""


def test_harita_sohbet_baglamina_eklenir():
    sonuc = prompt_composer.compose_chat_message(
        "bugün nasılım", [], chart="- Güneş: Kova, Ay: Aslan")

    assert "KULLANICININ HARİTASI" in sonuc
    assert "Kova" in sonuc
    # Modele konum uydurmaması söylenmeli
    assert "uydurma" in sonuc


def test_gokyuzu_sohbet_baglamina_eklenir():
    sonuc = prompt_composer.compose_chat_message(
        "ne var ne yok", [], sky="- Ay evresi: Dolunay")
    assert "BUGÜNÜN GERÇEK GÖKYÜZÜ" in sonuc
    assert "Dolunay" in sonuc


def test_persona_verilmeyen_konumu_uydurmayi_yasaklar():
    from services import gemini_service
    assert "uydurma" in gemini_service.CHAT_SYSTEM_INSTRUCTION


def test_bos_hafiza_bloku_baslik_yazmaz():
    """Boş bir "kullanıcı hakkında" başlığı modeli uydurmaya davet eder."""
    from services.report_service import _memory_block
    assert _memory_block("") == ""
    assert _memory_block("   ") == ""
    assert "ÖNCEDEN BİLDİKLERİN" in _memory_block("- (goal) maraton koşmak istiyor")
