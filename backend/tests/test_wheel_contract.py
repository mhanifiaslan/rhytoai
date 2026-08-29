"""Harita İnceleme (HI-turu) veri sözleşmeleri.

Çark üç kaynaktan beslenir (natal / transits / synastry) ve üçü de HA1
sözleşmesine uyar: KARARLI anahtarlar (İngilizce ad, küçük-harf açı türü)
asla üzerine yazılmaz; çeviri ``*_local`` alanlarına EKLENİR. Mobil çark
uçları adla, renk/stili anahtarla çözer — sözleşme bozulursa açı ağı
SESSİZCE boş çizilir (canlıda aylarca fark edilmeyen gökyüzü hatası).

Calistirma:  .venv\\Scripts\\python.exe -m pytest tests/test_wheel_contract.py -q
"""
from __future__ import annotations

import pytest

from services import astro_service, prompts

DOGUM_SAATLI = {"name": "A", "year": 1990, "month": 3, "day": 15,
                "hour": 14, "minute": 30, "city": "Istanbul",
                "nation": None, "hour_known": True}
DOGUM_SAATSIZ = {"name": "B", "year": 1992, "month": 7, "day": 2,
                 "hour": 12, "minute": 0, "city": "Izmir",
                 "nation": None, "hour_known": False}


@pytest.fixture(scope="module")
def sinastri():
    return astro_service.get_synastry(DOGUM_SAATLI, DOGUM_SAATSIZ)


class TestSinastriGenislemesi:
    """HA9: sinastri çarkı için EK alanlar — mevcut tüketici bozulmaz."""

    def test_tam_nokta_listeleri_doner(self, sinastri):
        assert len(sinastri["points1"]) >= 10
        assert len(sinastri["points2"]) >= 10
        ilk = sinastri["points1"][0]
        for alan in ("name", "abs_position", "sign", "position",
                     "retrograde"):
            assert alan in ilk

    def test_saatsiz_taraf_ev_iddiasi_tasimaz(self, sinastri):
        """Öğle dolgusu Yükselen'i çarka çizilmez (natal doktrini)."""
        assert sinastri["houses1"], "saatli tarafın 12 evi olmalı"
        assert len(sinastri["houses1"]) == 12
        assert sinastri["houses2"] == []
        assert all(p["house_no"] is None for p in sinastri["points2"])
        assert all(p["house"] is None for p in sinastri["points2"])

    def test_mevcut_anahtarlar_korunur(self, sinastri):
        """report_service yalnız bunları okuyor — ek alanlar kırmamalı."""
        for alan in ("person1", "person2", "aspects", "relationship_score",
                     "hour_known", "disclosures"):
            assert alan in sinastri

    def test_ham_dogum_verisi_sizmaz(self, sinastri):
        """Yanıtta yıl/ay/gün/şehir alanı YOK — yalnız türetilmiş konumlar.

        (Uç zaten iki doğum verisini İSTEMCİDEN alıyor — kendi profili +
        Çevrem; bu test yanıt şeklinin ileride ham girdiyi geri
        yansıtmamasını sabitler.)
        """
        def anahtarlar(obj, birikim):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    birikim.add(k)
                    anahtarlar(v, birikim)
            elif isinstance(obj, list):
                for v in obj:
                    anahtarlar(v, birikim)
            return birikim

        tum = anahtarlar(sinastri, set())
        for yasak in ("year", "month", "day", "birth_date", "birthDate",
                      "city", "nation", "lat", "lng"):
            assert yasak not in tum, f"ham doğum alanı sızdı: {yasak}"

    def test_yerellestirme_ek_alanlarla(self, sinastri):
        """HA1 sözleşmesi: kararlı anahtar korunur, *_local eklenir."""
        yerel = prompts.localize_synastry("tr", sinastri)
        p = yerel["points1"][0]
        assert p["name"] == sinastri["points1"][0]["name"]  # kararlı
        assert p["name_local"]                               # çevrilmiş
        a = yerel["aspects"][0]
        assert a["aspect"] == a["aspect"].lower()
        assert a["p1_local"] and a["aspect_local"]


class TestTransitsYerellestirmesi:
    """HA8: /astrology/transits bi-wheel'e bağlanırken HA1 sözleşmesi."""

    def test_kararli_anahtar_ve_local(self):
        ham = astro_service.get_transits(
            **astro_service.subject_kwargs(DOGUM_SAATLI), hour_known=True)
        yerel = prompts.localize_transits("tr", ham)
        assert yerel["transiting_points"], "transit noktaları boş olmamalı"
        nokta = yerel["transiting_points"][0]
        assert nokta["name"] == ham["transiting_points"][0]["name"]
        assert nokta["name_local"]
        for a in yerel["aspects_to_natal"][:5]:
            assert a["aspect"] == a["aspect"].lower()
            assert a["p1_local"] and a["p2_local"] and a["aspect_local"]

    def test_bos_veri_patlamaz(self):
        assert prompts.localize_transits("en", None) == {}
        assert prompts.localize_transits("en", {}) == {}
