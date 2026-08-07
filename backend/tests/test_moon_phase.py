"""Ay evresi ve aydınlanma doğruluğu (D1).

Neden ayrı dosya: aydınlanma uzun süre LİNEER bir yaklaşımla hesaplandı
((1 - |açı-180|/180)) ve kimse fark etmedi çünkü sayı "makul" görünüyordu.
Kullanıcı başka kaynaklarla kıyaslayınca ortaya çıktı: 30 günlük ölçümde
ortalama 6.7, en fazla 10.5 puan sapma. Sessizce yanlış olan sayı,
testsiz kalırsa yeniden sessizce yanlış olur.

Çapa DIŞARIDAN: `swe.pheno_ut` Swiss Ephemeris'in kendi fenomen hesabıdır
(aydınlanan kesir, faz açısı, elongasyon) ve bizim boylam aritmetiğimizden
bağımsız yoldan gelir — T0'daki altın vektör disiplininin aynısı.
"""
from __future__ import annotations

import datetime as dt

import swisseph as swe

from services import sky_service


def _jd(an: dt.datetime) -> float:
    return swe.julday(an.year, an.month, an.day,
                      an.hour + an.minute / 60 + an.second / 3600)


def _referans(jd: float) -> float:
    """Aydınlanan kesir, yüzde — swisseph'in kendi hesabı."""
    return swe.pheno_ut(jd, swe.MOON, swe.FLG_SWIEPH)[1] * 100


class TestAydinlanma:
    def test_referansa_yakin_bir_ay_boyunca(self):
        """Bir ay boyunca 6 saatlik adımlarla sapma < 1 puan.

        Eski lineer formül bu taramada ortalama 6.7 puan sapıyordu; eşik
        bilinçli olarak dar (1 puan) — yuvarlama dışında pay bırakmıyor.
        """
        bas = dt.datetime(2026, 8, 7, tzinfo=dt.timezone.utc)
        for i in range(120):
            jd = _jd(bas + dt.timedelta(hours=6 * i))
            uygulama = sky_service._moon_phase(jd)["illumination"]
            assert abs(uygulama - _referans(jd)) < 1.0

    def test_lineer_formul_regresyonu(self):
        """Lineer formülün EN ÇOK saptığı an: %78 değil %89 olmalı."""
        jd = _jd(dt.datetime(2026, 8, 24, 18, 0, tzinfo=dt.timezone.utc))
        assert sky_service._moon_phase(jd)["illumination"] == 89

    def test_dolunay_ve_yeniay_ucları(self):
        """Evrenin uçlarında aydınlanma da uçta olmalı."""
        bas = dt.datetime(2026, 8, 1, tzinfo=dt.timezone.utc)
        anlar = [bas + dt.timedelta(hours=3 * i) for i in range(260)]
        evreler = [(a, sky_service._moon_phase(_jd(a))) for a in anlar]
        dolunay = [e for _, e in evreler if e["key"] == "full_moon"]
        yeniay = [e for _, e in evreler if e["key"] == "new_moon"]
        assert dolunay and yeniay
        assert max(e["illumination"] for e in dolunay) >= 99
        assert min(e["illumination"] for e in yeniay) <= 1


class TestEvreAdi:
    """Evre ADI boylam farkından çıkar ve D1'de DEĞİŞMEDİ — bu testler
    aydınlanma düzeltmesinin adı bozmadığını sabitler.
    """

    def test_acidan_evreye_esleme(self):
        bas = dt.datetime(2026, 8, 1, tzinfo=dt.timezone.utc)
        for i in range(200):
            evre = sky_service._moon_phase(_jd(bas + dt.timedelta(hours=4 * i)))
            aci = evre["angle"]
            assert 0 <= evre["illumination"] <= 100
            # Dönen açı 0.1°'ye yuvarlı; sınırın hemen dibindeki örnekte
            # yuvarlama, açıyı komşu dilime taşıyabilir (motor yuvarlanmamış
            # değerle karar veriyor). Sınıflandırma iddiası orada değil,
            # dilimin İÇİNDE sınanır.
            if any(abs(aci - limit) < 0.2
                   for limit, _, _ in sky_service._MOON_PHASES):
                continue
            beklenen = next(k for limit, k, _ in sky_service._MOON_PHASES
                            if aci < limit)
            assert evre["key"] == beklenen

    def test_yuk_as_of_tasiyor(self):
        """Oran ANA bağlı; yük hangi ana ait olduğunu söylemeli."""
        sky = sky_service.get_sky_now(include_nasa=False)
        moon = sky["moon_phase"]
        assert moon["as_of_utc"] == sky["timestamp_utc"]
        # ISO ve UTC — mobil bunu yerel saate çeviriyor.
        assert dt.datetime.fromisoformat(moon["as_of_utc"]).tzinfo is not None
