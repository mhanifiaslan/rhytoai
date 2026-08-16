"""Dürüstlük bekçileri (R2-D1): ürün HESAPLAMADIĞINI iddia edemez.

Tespit (docs/ozellikler.md "İddia edilemeyecekler"): persona ve README
Vedik astroloji (Nakshatra/Dasha) sayıyordu ama motor bunları hiçbir yerde
hesaplamıyor. Bu testler o sınıf tutarsızlığın geri gelmesini engeller —
"ölçülmeyen söylenmez" ilkesinin iddia tarafı.
"""
from __future__ import annotations

import pathlib

from services import prompts

_KOK = pathlib.Path(__file__).resolve().parents[2]

#: Hesaplanmayan sistemin persona/korpus yoluyla İDDİAYA dönüşen anahtar
#: kelimeleri. "Vedik/Jyotish" kelimesinin kendisi dürüstlük cümlesinde
#: ("hesaplanmıyor") geçebilir; yasak olan bunları BİLGİ diye sunmaktır.
_IDDIA_KALIPLARI = ("Nakshatra'lar", "Dasha dönemleri",
                    "nakshatras, dasha periods")


class TestPersona:
    def test_persona_hesaplanmayani_bilgi_saymaz(self):
        for lang in ("tr", "en"):
            metin = prompts.get(lang).SYSTEM_INSTRUCTION
            for kalip in _IDDIA_KALIPLARI:
                assert kalip not in metin, (lang, kalip)

    def test_persona_durustluk_cumlesi_tasir(self):
        assert "HESAPLANMIYOR" in prompts.get("tr").SYSTEM_INSTRUCTION
        assert "NOT computed" in prompts.get("en").SYSTEM_INSTRUCTION

    def test_persona_mizac_adi_saymaz(self):
        """H1 kararının persona ayağı: mizaç adları v1'de hesaplanmıyor,
        'bilgin' listesinde de geçmemeli (raporda yasak, personada teşvik
        çelişkiydi)."""
        for lang in ("tr", "en"):
            metin = prompts.get(lang).SYSTEM_INSTRUCTION.lower()
            for ad in ("demevi", "safrai", "sevdavi", "balgami",
                       "sanguine", "choleric", "melancholic", "phlegmatic"):
                assert ad not in metin, (lang, ad)


class TestKorpusVeBelgeler:
    def test_korpus_nakshatra_icermez(self):
        """RAG, korpustaki Vedik pasajını raporlara taşıyabilirdi —
        pasaj kaldırıldı, geri gelmesin."""
        for md in (_KOK / "knowledge" / "corpus").rglob("*.md"):
            metin = md.read_text(encoding="utf-8", errors="ignore").lower()
            assert "nakshatra" not in metin, md
            assert "dasha" not in metin, md

    def test_readme_vedik_iddia_etmez(self):
        metin = (_KOK / "README.md").read_text(encoding="utf-8")
        assert "Vedik" not in metin
