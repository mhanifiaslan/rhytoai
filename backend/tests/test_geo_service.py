"""Gazetteer çözümleme doğruluğu (O1).

Eski elle yazılmış sözlük 81 TR ilinden yalnız 33'ünü tanıyordu ve
"münih" gibi anahtarlar normalize hatasıyla hiç erişilemiyordu — kimse
fark etmedi çünkü düşüş sessizdi (İstanbul + beyan). Bu testler yeni
GeoNames tabanlı gazetteer'in üç sözünü sabitler: 81 ilin tamamı,
Türkçe egzonimler ve eski sözlüğün TÜM anahtarları (geriye uyumluluk).
"""
from __future__ import annotations

import pytest

from services import geo_service
from scripts.build_gazetteer import _ESKI_ANAHTARLAR, _TR_ILLERI


class TestTurkiye:
    def test_81_ilin_tamami_cozuluyor(self):
        for il in _TR_ILLERI:
            loc = geo_service.resolve_city(il, "TR")
            assert not loc.fallback, f"il çözülemedi: {il}"
            assert loc.tz_str == "Europe/Istanbul", il

    def test_il_adi_farkli_merkezler(self):
        """Kocaeli/Sakarya/Hatay il adıyla aranınca merkeze gitmeli."""
        kocaeli = geo_service.resolve_city("Kocaeli", "TR")
        izmit = geo_service.resolve_city("İzmit", "TR")
        assert not kocaeli.fallback
        assert (kocaeli.lat, kocaeli.lng) == (izmit.lat, izmit.lng)

    def test_turkce_karakter_varyantlari(self):
        for yazim in ("Şanlıurfa", "sanliurfa", "ŞANLIURFA", "Sanliurfa"):
            loc = geo_service.resolve_city(yazim)
            assert not loc.fallback, yazim
            assert abs(loc.lat - 37.16) < 0.2, yazim


class TestDunya:
    def test_egzonimler(self):
        """Türkçe dış-ad her zaman çözülür (build garanti tablosu)."""
        beklenen = {
            "münih": "DE", "brüksel": "BE", "zürih": "CH", "kahire": "EG",
            "moskova": "RU", "pekin": "CN", "atina": "GR", "viyana": "AT",
            "londra": "GB", "bakü": "AZ", "tahran": "IR",
        }
        for ad, ulke in beklenen.items():
            loc = geo_service.resolve_city(ad)
            assert not loc.fallback, ad
            assert loc.nation == ulke, ad

    def test_eski_gazetteer_anahtarlari_regresyonsuz(self):
        """Bugüne kadar çözülen HİÇBİR ad çözülmez hâle gelmemeli."""
        for ad in _ESKI_ANAHTARLAR:
            loc = geo_service.resolve_city(ad)
            assert not loc.fallback, f"eski anahtar düştü: {ad}"

    def test_ayni_ad_ulke_filtresi(self):
        """Tripoli LB/LY: nation verilirse o ülke kazanır."""
        lb = geo_service.resolve_city("Tripoli", "LB")
        ly = geo_service.resolve_city("Tripoli", "LY")
        assert not lb.fallback and not ly.fallback
        assert lb.tz_str != ly.tz_str

    def test_yanlis_ulke_dogru_sehri_golgelemez(self):
        """Ülkede eşleşme yoksa filtre yok sayılır — ad kazanır."""
        loc = geo_service.resolve_city("Paris", "TR")
        assert not loc.fallback
        assert abs(loc.lat - 48.85) < 0.5  # Paris FR; TR'de Paris yok


class TestFallback:
    def test_bilinmeyen_yer_istanbul_beyanli(self):
        """Serbest metin kabulünün sunucu yarısı: düşüş sessiz değil."""
        loc = geo_service.resolve_city("OlmayanBirKoyAdi123")
        assert loc.fallback is True
        assert (round(loc.lat, 2), round(loc.lng, 2)) == (41.01, 28.98)
        assert loc.tz_str == "Europe/Istanbul"

    def test_fallback_kullanici_yazimini_korur(self):
        loc = geo_service.resolve_city("HiçbirYerKasabası")
        assert loc.city == "HiçbirYerKasabası"


def test_veri_dosyasi_meta_tasiyor():
    """Veri dosyası kaynağını ve tarihini söylemeli (CC-BY atıf zinciri)."""
    import json
    veri = json.loads(
        geo_service._GAZETTEER_PATH.read_text(encoding="utf-8"))
    assert "GeoNames" in veri["meta"]["source"]
    assert veri["meta"]["count"] == len(veri["cities"])
    assert veri["meta"]["count"] > 30000
