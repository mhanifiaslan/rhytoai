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

class TestSinirDurumlari:
    """R2-D1: kenar durum bekcileri — analiz maddesi 29 (hesap dogrulugu).

    Bunlar deger vektoru degil YAPISAL bekciler: kenar girdide motor ne
    coker ne sessizce sacmalar (12 ev, boylam araligi, burc uretimi).
    Dis capali DEGER vektoru eklemek astro.com'dan ELLE okuma ister (T0
    kurali: otomatik erisim yasak); o dogrulama kapali test doneminde
    altin vektor olarak eklenecek.
    """

    def _yapisal(self, chart):
        assert len(chart["houses"]) == 12
        for p in chart["points"]:
            assert 0.0 <= p["abs_position"] < 360.0
        assert chart["sun_sign"]
        return chart

    def test_gece_yarisi_dogumu(self):
        self._yapisal(_harita(1990, 1, 1, 0, 0))

    def test_ogle_dogumu(self):
        self._yapisal(_harita(1990, 1, 1, 12, 0))

    def test_dst_ileri_alinan_var_olmayan_saat(self):
        # Avrupa DST baslangici 2021-03-28: Londra'da 01:00-02:00 arasi
        # YOKTUR (saat ileri alinir). Motor bu saati cokertmemeli.
        self._yapisal(_harita(2021, 3, 28, 1, 30))

    def test_dst_geri_alinan_belirsiz_saat(self):
        # 2021-10-31 01:30 Londra'da IKI KEZ yasanir (belirsiz saat);
        # motor deterministik bir secim yapip harita uretmeli.
        self._yapisal(_harita(2021, 10, 31, 1, 30))

    def test_kutup_dairesi_enlemi(self):
        # Tromso 69.6N: Placidus ev sistemi kutup dairesinin ustunde
        # tanimsiz kalabilir; motor coker ya da bos ev dondururse bu test
        # yakalar (kullanici tabaninda Iskandinav dogumlari olacak).
        self._yapisal(_harita(1985, 12, 21, 12, 0, city="Tromso"))

    def test_kutup_ici_asiri_enlem(self):
        # Longyearbyen 78.2N — en sert durum: kutup gecesi + Placidus.
        self._yapisal(_harita(1990, 6, 21, 12, 0, city="Longyearbyen"))

    def test_1900_oncesi_tarih(self):
        # Efemeris dosyalari 1800'leri kapsamali (se1 paketleme bekcisiyle
        # birlikte calisir); tarihsel saat dilimi IANA'dan cozulur.
        self._yapisal(_harita(1885, 7, 14, 6, 30, city="Istanbul"))

    def test_artik_yil_29_subat(self):
        self._yapisal(_harita(2000, 2, 29, 18, 45, city="Ankara"))


class TestDagilimSozlesmesi:
    """R5-1/R5-2: arayuzun dayandigi alanlar.

    Kisilik ekrani eskiden yuzdeleri ISTEMCIDE uretiyordu (30 + 10*sayim) ve
    Ay dugumlerini sayip Yukselen'i disarida birakiyordu. Artik tek dogruluk
    kaynagi bu alanlar; sozlesme kirilirsa ekran sessizce bosalir.
    """

    def _harita(self):
        return _harita(1990, 5, 12, 14, 30, city="Istanbul")

    def test_uyeler_sayimla_tutarli(self):
        c = self._harita()
        for alan, uye_alani in (("element_distribution", "element_members"),
                                ("modality_distribution", "modality_members")):
            sayim, uyeler = c[alan], c[uye_alani]
            assert set(sayim) == set(uyeler)
            for anahtar, adet in sayim.items():
                assert len(uyeler[anahtar]) == adet, (alan, anahtar)

    def test_kanonik_kume_sekiz_nokta(self):
        """Geleneksel yedili + Yukselen — Kiron/Lilith/dugumler GIRMEZ."""
        c = self._harita()
        assert c["balance_set"] == [
            "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
            "Ascendant"]
        assert sum(c["element_distribution"].values()) == 8
        assert sum(c["modality_distribution"].values()) == 8
        tum_uyeler = [u for liste in c["element_members"].values()
                      for u in liste]
        assert "Ascendant" in tum_uyeler
        for disarida in ("Chiron", "Mean_Lilith", "True_North_Lunar_Node"):
            assert disarida not in tum_uyeler

    def test_saat_bilinmiyorsa_yukselen_ve_ev_yok(self):
        """Noon ASC 'senin yükselenin' diye dönmez; evler boştur."""
        c = astro_service.get_natal_chart(
            "test", 1990, 5, 12, 12, 0, "Istanbul", hour_known=False)
        assert c["hour_known"] is False
        assert c["ascendant"] is None
        assert c["asc"] is None
        assert c["houses"] == []
        assert "natal_hour_unknown" in c["disclosures"]
        assert "Ascendant" not in c["balance_set"]
        assert sum(c["element_distribution"].values()) == 7
        gunes = _nokta(c, "Sun")
        assert gunes["house_no"] is None
        assert gunes["house"] is None
        assert not any(a["p1"] in ("Ascendant", "Medium_Coeli")
                       or a["p2"] in ("Ascendant", "Medium_Coeli")
                       for a in c["aspects"])

    def test_ev_numarasi_dondurulur(self):
        """R5-2: kerykeion metni ("Fifth_House") her istemcide ayri ayri
        cozulmesin diye sayi olarak da gelir."""
        c = self._harita()
        gunes = _nokta(c, "Sun")
        assert isinstance(gunes["house_no"], int)
        assert 1 <= gunes["house_no"] <= 12
