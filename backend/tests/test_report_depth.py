"""Revize R8: içerik derinliği.

İki iddia sınanıyor ve ikisi de sessizce bozulabilecek türden:

1. Kişisel günlük okuma bugünün transit-natal kesişimini GÖRÜYOR. Eskiden
   yalnızca genel gökyüzü veriliyordu; satır prompt'tan düşerse hiçbir hata
   çıkmaz, okuma yalnızca jenerikleşir.
2. Rapor RAG sorguları isteğin dilinde kuruluyor. Eski sabit şablonlar
   ("sun sign temperament character") TR korpusta İngilizce arıyordu —
   dönen pasaj alakasızlaşır ama üretim "başarılı" görünürdü.
"""
from __future__ import annotations

import pytest

from services import prompts, report_service, sky_service


@pytest.fixture
def temiz_onbellek(tmp_path, monkeypatch):
    from core import cache, config
    monkeypatch.setattr(config, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(config, "CACHE_BACKEND", "file")
    cache._memory.clear()
    yield
    cache._memory.clear()


def _kur(monkeypatch):
    """Prompt'u ve RAG sorgusunu yakalayan sahte uçlar."""
    kutu: dict[str, str] = {}

    def sahte_generate(prompt, **k):
        kutu["prompt"] = prompt
        return "ok"

    def sahte_rag(query, **k):
        kutu["sorgu"] = query
        return ""

    monkeypatch.setattr(report_service.gemini_service, "generate",
                        sahte_generate)
    # from-import DEĞİL modül niteliği: report_service.retrieve_context
    # adıyla yamalanabilir kalmalı (bkz. wallet'taki aliasing dersi).
    monkeypatch.setattr(report_service, "retrieve_context", sahte_rag)
    monkeypatch.setattr(report_service.memory_service, "memory_context",
                        lambda uid, max_chars=600: "")
    return kutu


def _natal():
    from services import astro_service
    return astro_service.get_natal_chart(
        name="Test", year=1990, month=5, day=12, hour=14, minute=30,
        city="Istanbul", nation="TR",
    )


_BIRTH = dict(name="Test", year=1990, month=5, day=12, hour=14, minute=30,
              city="Istanbul", nation="TR")

_VURUS = {"hits": [{"transit": "Saturn", "natal": "Sun",
                    "aspect": "square", "orb": 0.8}]}


def test_gunluk_okuma_transiti_prompta_koyar(monkeypatch, temiz_onbellek):
    kutu = _kur(monkeypatch)
    monkeypatch.setattr(report_service.chart_context, "transit_facts",
                        lambda birth: _VURUS)

    sky = prompts.localize_sky(
        "tr", sky_service.get_sky_now(include_nasa=False))
    report_service.daily_reading("u-r8-tr", _natal(), sky, lang="tr",
                                 birth=_BIRTH)

    # Yerelleştirilmiş adlarla: "Saturn" değil "Satürn" görünmeli.
    assert prompts.planet_name("tr", "Saturn") in kutu["prompt"]
    assert prompts.aspect_name("tr", "square") in kutu["prompt"]


def test_gunluk_okuma_birthsiz_eski_davranista(monkeypatch, temiz_onbellek):
    """birth verilmezse transit hesabı HİÇ çağrılmaz (eski çağıranlar aynı)."""
    kutu = _kur(monkeypatch)

    def patlama(birth):
        raise AssertionError("birth yokken transit hesaplanmamalı")

    monkeypatch.setattr(report_service.chart_context, "transit_facts",
                        patlama)
    sky = prompts.localize_sky(
        "tr", sky_service.get_sky_now(include_nasa=False))
    sonuc = report_service.daily_reading("u-r8-eski", _natal(), sky,
                                         lang="tr")
    assert sonuc["text"] == "ok"
    assert "{transits}" not in kutu["prompt"]


def test_transit_hesabi_dusunce_okuma_devam_eder(monkeypatch,
                                                 temiz_onbellek):
    """Efemeris düşerse günlük okuma düşmez — transitsiz üretilir."""
    kutu = _kur(monkeypatch)

    def dusen(birth):
        raise RuntimeError("efemeris yok")

    monkeypatch.setattr(report_service.chart_context, "transit_facts", dusen)
    sky = prompts.localize_sky(
        "tr", sky_service.get_sky_now(include_nasa=False))
    sonuc = report_service.daily_reading("u-r8-dusen", _natal(), sky,
                                         lang="tr", birth=_BIRTH)
    assert sonuc["text"] == "ok"
    assert kutu["prompt"]  # prompt yine kuruldu


def test_gunluk_sorgu_istegin_dilinde(monkeypatch, temiz_onbellek):
    kutu = _kur(monkeypatch)
    monkeypatch.setattr(report_service.chart_context, "transit_facts",
                        lambda birth: _VURUS)
    sky = prompts.localize_sky(
        "tr", sky_service.get_sky_now(include_nasa=False))
    report_service.daily_reading("u-r8-sorgu", _natal(), sky, lang="tr",
                                 birth=_BIRTH)

    sorgu = kutu["sorgu"]
    # TR tohumu var, eski İngilizce dolgu yok.
    assert "Mizaç" in sorgu
    assert "temperament" not in sorgu
    assert "interpretation" not in sorgu


def test_natal_sorgu_ingilizce_dolgu_icermez(monkeypatch, temiz_onbellek):
    kutu = _kur(monkeypatch)
    report_service.natal_report("u-r8-natal", _natal(), lang="tr")

    sorgu = kutu["sorgu"]
    assert "sun sign temperament" not in sorgu
    assert "character" not in sorgu
    assert "Mizaç" in sorgu


def test_bazi_promptu_derin_veriyi_tasir(monkeypatch, temiz_onbellek):
    """B6: rapor promptu motorun yeni ürettiklerini gerçekten görüyor.

    Güç hükmü, dayanak dökümü, gizli kökler, Liu Nian ve kapsam beyanı —
    bunlardan biri prompt kurulumundan düşerse hiçbir hata çıkmaz, model
    yalnızca o konuda genelleme yapar. Bu test o sessiz gerilemeyi tutar.
    """
    from services import bazi_service, prompts as prompt_mod
    kutu = _kur(monkeypatch)
    chart = bazi_service.get_bazi_chart(
        1990, 5, 12, 14, 30, city="Istanbul", gender="female")
    report_service.bazi_report("u-b6", chart, lang="tr")

    prompt = kutu["prompt"]
    yerel = prompt_mod.localize_bazi("tr", chart)
    assert "GÜÇ HÜKMÜ" in prompt
    assert yerel["strength"]["verdict_name"] in prompt
    assert "month_command" in prompt          # dayanak dökümü
    assert "→" in prompt                       # gizli kök satırı
    assert str(chart["current_year_pillar"]["year"]) in prompt
    # Kapsam beyanı: kombinasyonlar hesapta yok — model bunu okumalı.
    assert "he/chong" in prompt

    # Sorgu bazi tohumunu taşıyor.
    assert "Dört Sütun" in kutu["sorgu"]
