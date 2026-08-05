"""Batı astrolojisi motoru altın vektörleri (T0).

Bu dosyadan önce astroloji tarafında TEK BİR değer testi yoktu: kerykeion
yükseltmesi, ev sistemi varsayılanının değişmesi ya da ayanamsa kayması
hiçbir test kırmadan üretime çıkardı. BaZi/İ Ching'deki kural buraya da
geliyor: **her altın değer motordan bağımsız bir kaynakla doğrulanır ve
kaynak, vektörün yanına yorum olarak yazılır.**

Kaynak seçimi bilinçli: gezegen boylamları konumdan bağımsızdır, bu yüzden
vektörler YAYINLANMIŞ astronomik olaylardan alındı (ekinoks/gündönümü
zamanları, tutulma konumu, büyük kavuşum, retro dönemi) — bunlar USNO/NASA
almanak verileridir ve astroloji sitelerinden bile bağımsızdır. Yükselen/ev
altın vektörü ise şehir+saat ister; astro.com/astro-seek'ten ELLE okunmuş
çift kaynak onayı beklediği için bu dosyada yapısal değişmezlerle sınırlı
tutuldu (bkz. sınıf yorumu).
"""
from __future__ import annotations

import pytest

from services import astro_service


def _harita(y, m, d, hh, mm, city="Londra"):
    return astro_service.get_natal_chart(
        "test", y, m, d, hh, mm, city)


def _nokta(chart, ad):
    for p in chart["points"]:
        if p["name"].lower() == ad.lower():
            return p
    raise AssertionError(f"nokta yok: {ad}")


class TestGunesBoylami:
    """Güneş boylamı — mevsim dönümleri almanak vektörleri.

    Kaynak: USNO/NASA yayınlanmış ekinoks-gündönümü zamanları. O anda
    Güneş'in tropikal boylamı TANIM GEREĞİ 0°/90°'dir — motordan bağımsız
    en güçlü çapa.
    """

    def test_ilkbahar_ekinoksu_2000(self):
        # 2000-03-20 07:35 UTC (USNO). Londra o tarihte GMT (DST 26 Mart'ta
        # başladı) → yerel = UTC. Dakika çözünürlüğünde geçiş anının hangi
        # TARAFINDA kaldığımız belirsizdir; ölçüt burç adı değil, 0° Koç
        # noktasına yay-dakika uzaklığıdır (sınırın iki komşusu da meşru).
        chart = _harita(2000, 3, 20, 7, 35)
        gunes = _nokta(chart, "Sun")
        assert gunes["sign"] in ("Pis", "Ari")
        uzaklik = min(abs(gunes["abs_position"] - 0.0),
                      abs(gunes["abs_position"] - 360.0))
        assert uzaklik < 0.05

    def test_yaz_gundonumu_2016(self):
        # 2016-06-20 22:34 UTC (USNO). Londra BST (UTC+1) → yerel 23:34.
        chart = _harita(2016, 6, 20, 23, 34)
        gunes = _nokta(chart, "Sun")
        assert gunes["sign"] in ("Gem", "Can")
        assert abs(gunes["abs_position"] - 90.0) < 0.05


class TestYayinlanmisOlaylar:
    """Konumdan bağımsız gezegen vektörleri — yayınlanmış gök olayları."""

    def test_buyuk_kavusum_2020(self):
        # Jüpiter-Satürn büyük kavuşumu: 2020-12-21 ~18:20 UTC, her ikisi
        # ~0°29' Kova (yayınlanmış: NASA/gözlemevleri; 0.1° ayrıklık).
        # Londra GMT → yerel 18:20.
        chart = _harita(2020, 12, 21, 18, 20)
        jup, sat = _nokta(chart, "Jupiter"), _nokta(chart, "Saturn")
        assert jup["sign"] == "Aqu" and sat["sign"] == "Aqu"
        assert abs(jup["abs_position"] - sat["abs_position"]) < 0.2
        assert abs(jup["position"] - 0.49) < 0.2  # 0°29' ≈ 0.49°
        # Açı listesi kavuşumu görmeli, orb ~0.1°.
        kavusum = [a for a in chart["aspects"]
                   if {a["p1"], a["p2"]} == {"Jupiter", "Saturn"}]
        assert kavusum and kavusum[0]["aspect"] == "conjunction"
        assert kavusum[0]["orbit"] < 0.2

    def test_ay_tutulmasi_2019_ay_konumu(self):
        # Tam Ay tutulması 2019-01-21, maksimum 05:12 UTC; Ay ~0°52' Aslan,
        # Güneş karşısında ~0°52' Kova (yayınlanmış tutulma verisi).
        chart = _harita(2019, 1, 21, 5, 12)
        ay, gunes = _nokta(chart, "Moon"), _nokta(chart, "Sun")
        assert ay["sign"] == "Leo" and gunes["sign"] == "Aqu"
        assert abs(ay["position"] - 0.87) < 0.3   # 0°52' ≈ 0.87°
        assert abs(gunes["position"] - 0.87) < 0.3
        # Tutulma = tam karşıtlık.
        fark = abs(ay["abs_position"] - gunes["abs_position"])
        assert abs(fark - 180.0) < 0.3

    def test_merkur_retro_2023(self):
        # Merkür retrosu 2023-08-23 → 2023-09-15 (yayınlanmış dönem).
        # Dönemin ortası retro, sonrası direkt olmalı.
        retro = _nokta(_harita(2023, 9, 1, 12, 0), "Mercury")
        direkt = _nokta(_harita(2023, 9, 20, 12, 0), "Mercury")
        assert retro["retrograde"] is True
        assert direkt["retrograde"] is False
        # T0: hız alanı artık taşınıyor — retro'da negatif olmalı.
        assert retro["speed"] is not None and retro["speed"] < 0
        assert direkt["speed"] is not None and direkt["speed"] > 0


class TestYapisalDegismezler:
    """Ev/Yükselen yapısal kuralları.

    Derece-altın-vektörü BİLEREK yok: ASC şehir+saat ister ve bağımsız çift
    kaynak (astro.com + astro-seek) ELLE okunarak dondurulmalı — otomatik
    erişim iki sitenin de şartlarına aykırı. Elle okuma yapıldığında buraya
    vektör eklenecek; o güne dek yapısal değişmezler nöbet tutuyor.
    """

    def test_on_iki_ev_ve_yukselen(self):
        chart = _harita(1990, 5, 12, 14, 30, city="Istanbul")
        assert len(chart["houses"]) == 12
        # Yükselen == 1. ev ucu.
        assert chart["asc"]["sign"] == chart["houses"][0]["sign"]
        # Ev uçları çember üzerinde artan sırada döner (mod 360).
        uclar = [h["abs_position"] for h in chart["houses"]]
        donus = sum(1 for i in range(12)
                    if uclar[i] > uclar[(i + 1) % 12])
        assert donus == 1  # tek sarma noktası

    def test_t0_alanlari_tasiniyor(self):
        """Bedeli ödenmiş alanlar artık atılmıyor: declination/speed/movement."""
        chart = _harita(1990, 5, 12, 14, 30, city="Istanbul")
        gunes = _nokta(chart, "Sun")
        assert gunes["declination"] is not None
        assert -24.0 < gunes["declination"] < 24.0  # Güneş her zaman bu bantta
        assert gunes["speed"] is not None
        if chart["aspects"]:
            assert "movement" in chart["aspects"][0]

    def test_beyan_yoksa_bos_liste(self):
        chart = _harita(1990, 5, 12, 14, 30, city="Istanbul")
        assert chart["disclosures"] == []

    def test_cozulmeyen_sehir_beyan_uretir(self):
        """T0'ın ana kapanışı: sessiz İstanbul düşüşü artık BEYAN taşıyor."""
        chart = _harita(1990, 5, 12, 14, 30, city="HiçbirYerKasabası")
        assert "geo_fallback_city" in chart["disclosures"]


class TestEfemerisVerisi:
    def test_se1_dosyalari_yerinde(self):
        """sepl/semo imaja girmezse Moshier'e sessiz düşüş geri gelir."""
        from core.ephemeris import EPHE_DIR
        adlar = {p.name for p in EPHE_DIR.glob("*.se1")}
        assert {"sepl_18.se1", "semo_18.se1"} <= adlar
        for p in EPHE_DIR.glob("*.se1"):
            assert p.read_bytes()[:8] == b"SWISSEPH"