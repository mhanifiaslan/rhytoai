"""Tahmin katmanı altın vektörleri (T1+).

Efemeris T0'da DIŞ almanak çapalarına bağlandı (ekinoks/kavuşum/tutulma);
buradaki testler çözücüleri TANIMLARINA karşı doğrular: solar return anı,
tanımı gereği Güneş'in natal boylamına döndüğü andır — iki taraf da aynı
(dışarıdan çapalanmış) efemerisi kullandığı için bu bileşim geçerli bir
doğrulamadır.
"""
from __future__ import annotations

import datetime as dt

from services import astro_service, predict_service


def _natal_gunes(y, m, d, hh, mm, city="Istanbul"):
    chart = astro_service.get_natal_chart("t", y, m, d, hh, mm, city)
    for p in chart["points"]:
        if p["name"] == "Sun":
            return p["abs_position"]
    raise AssertionError("Güneş yok")


class TestSolarReturn:
    def test_donus_ani_tanimi(self):
        """SR anında Güneş boylamı == natal Güneş boylamı (çözücü tanımı)."""
        natal_boylam = _natal_gunes(1990, 5, 12, 14, 30)
        sr = predict_service.solar_return(
            "t", 1990, 5, 12, 14, 30, "Istanbul", target_year=2025)
        an = dt.datetime.fromisoformat(sr["return_at_utc"])
        # Dönüş anındaki Güneş'i motorla yeniden hesapla. Motor YEREL saat
        # bekler: Londra Mayıs'ta BST'dedir (UTC+1) — UTC saatini çevirmeden
        # geçirmek tam 1 saatlik (≈0.04°) kaymaya yol açıyordu.
        from zoneinfo import ZoneInfo
        yerel = an.astimezone(ZoneInfo("Europe/London"))
        sr_gunes = _natal_gunes(yerel.year, yerel.month, yerel.day,
                                yerel.hour, yerel.minute, city="Londra")
        fark = abs(sr_gunes - natal_boylam)
        fark = min(fark, 360 - fark)
        # Dakika yuvarlaması Güneş'te en fazla ~0.0007°/dk → bol pay.
        assert fark < 0.02

    def test_aktif_gecmiste_sonraki_gelecekte(self):
        sr = predict_service.solar_return(
            "t", 1990, 5, 12, 14, 30, "Istanbul")
        simdi = dt.datetime.now(dt.timezone.utc)
        aktif = dt.datetime.fromisoformat(sr["return_at_utc"])
        assert aktif <= simdi
        # Sonraki dönüş aktiften ~1 yıl sonra (365 ± 2 gün).
        sonraki = dt.datetime.fromisoformat(sr["next_return_at_local"])
        gun_fark = (sonraki.replace(tzinfo=None)
                    - aktif.replace(tzinfo=None)).days
        assert 363 <= gun_fark <= 367

    def test_saatsizlik_asc_uretmez_ve_beyan_tasir(self):
        """Dürüstlük değişmezi: saat yoksa SR ASC/ev alanları HİÇ yok."""
        sr = predict_service.solar_return(
            "t", 1990, 5, 12, 12, 0, "Istanbul", hour_known=False)
        assert "sr_ascendant" not in sr
        assert "sr_sun_house" not in sr
        assert "sr_hour_unknown" in sr["disclosures"]

    def test_hedef_yil_secimi(self):
        sr = predict_service.solar_return(
            "t", 1990, 5, 12, 14, 30, "Istanbul", target_year=2020)
        assert sr["return_at_utc"].startswith("2020-05-1")

    def test_cozulmeyen_sehir_beyani(self):
        sr = predict_service.solar_return(
            "t", 1990, 5, 12, 14, 30, "BilinmeyenKoy", target_year=2025)
        assert "geo_fallback_city" in sr["disclosures"]