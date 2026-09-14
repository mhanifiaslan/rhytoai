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


class TestPazarlamaDili:
    """Yayına çıkan METİNLER koddaki kapılarla ve kendi kılavuzumuzla
    uyuşmalı.

    Bu sınıf kapalı test denetiminde (2026-09-14) eklendi. Aynı kusur
    sınıfı ÜÇ kez tekrarladı: önce mağaza metni ücretsiz I Ching vadetti
    (R9-5'te düzeltildi), sonra aynı vaat web sitesinde bulundu, üstelik
    yanında "Sınırsız sohbet" ve projenin kendi kılavuzunun (ozellikler.md
    §12b) açıkça yasakladığı "NASA" ibaresi vardı. Metin koddan sapıyor ve
    bunu kimse fark etmiyor; bekçi bu yüzden var.
    """

    #: Yayına çıkan HTML'ler: Firebase Hosting `public: "web"`.
    _SAYFALAR = ("web/index.html", "web/en/index.html",
                 "web/legal/gizlilik.html", "web/en/legal/privacy.html",
                 "web/legal/kullanim.html",
                 "web/legal/hesap-silme.html",
                 "web/en/legal/delete-account.html")

    #: (aranan, neden yasak)
    _YASAKLAR = (
        ("nasa", "ozellikler.md §12b: 'NASA' ASLA — doğrusu 'astronomik "
                 "efemeris verisi'"),
        ("sınırsız sohbet", "Rytho+ aylık 300 kredidir; sınırsız değil"),
        ("unlimited chat", "Rytho+ is 300 credits a month, not unlimited"),
        ("iyileştirir", "sağlık iddiası — mağaza politikası"),
        ("tedavi eder", "sağlık iddiası — mağaza politikası"),
        ("şifa", "sağlık iddiası — mağaza politikası"),
        (" heals ", "health claim — store policy"),
        (" cures ", "health claim — store policy"),
    )

    def test_yayindaki_sayfalarda_yasak_ifade_yok(self):
        for yol in self._SAYFALAR:
            dosya = _KOK / yol
            if not dosya.exists():
                continue
            metin = dosya.read_text(encoding="utf-8").lower()
            for aranan, neden in self._YASAKLAR:
                assert aranan not in metin, (
                    f"{yol} içinde yasak ifade {aranan!r} — {neden}")

    def test_site_ucretsiz_i_ching_vadetmiyor(self):
        """`require_plus("iching")` kapıda; site 'ücretsiz' diyemez."""
        for yol in ("web/index.html", "web/en/index.html"):
            dosya = _KOK / yol
            if not dosya.exists():
                continue
            metin = dosya.read_text(encoding="utf-8").lower()
            for kalip in ("günde 1 i ching", "günde bir i ching",
                          "1 i ching cast a day"):
                assert kalip not in metin, (
                    f"{yol}: I Ching ücretsiz katmanda gösteriliyor ama "
                    f"backend/api/reports.py require_plus('iching') ile "
                    f"kilitliyor")

    def test_iching_gercekten_plus_kapisinda(self):
        """Yukarıdaki iki testin dayanağı: kapı hâlâ orada mı?

        Kapı kaldırılırsa (ürün kararı değişirse) bu test düşer ve site
        metinlerinin de güncellenmesi gerektiği hatırlatılır.
        """
        kaynak = (_KOK / "backend" / "api" / "reports.py").read_text(
            encoding="utf-8")
        assert 'require_plus("iching")' in kaynak, (
            "I Ching kapısı kalkmış: web sitesi ve mağaza metinleri de "
            "gözden geçirilmeli")
