"""İlişki ekseni bekçileri (R2-L1).

Üç değişmez: (1) sayısal uyum PUANI hiçbir yerde dönmez — bilinçli ürün
kararı; (2) her eksenin seviyesi ve tonu ölçülmüş açılardan determinist
çıkar ve dayanağı yanında taşınır; (3) sert açı ayrı bir "gerilim" ekseni
olarak İKİNCİ KEZ sayılmaz — ilgili eksenin TONUNU değiştirir.
"""
from __future__ import annotations

from services import astro_service, prompts, synastry_service


def _aci(p1, p2, aspect, orbit):
    return {"p1": p1, "p2": p2, "aspect": aspect, "orbit": orbit}


SAHTE_SINASTRI = {
    "aspects": [
        # İletişim: iki dar harmonik açı → eşiği (1.4) aşar, akıcı.
        _aci("Mercury", "Moon", "trine", 0.4),
        _aci("Mercury", "Sun", "sextile", 0.6),
        _aci("Mercury", "Venus", "conjunction", 0.5),
        # Duygu: Ay–Venüs kavuşum + Satürn–Ay karesi → karışık ton.
        _aci("Moon", "Venus", "conjunction", 0.9),
        _aci("Saturn", "Moon", "square", 0.5),
        # Çekim: tek geniş açı → hafif.
        _aci("Venus", "Mars", "trine", 4.0),
        # Hiçbir ekseni beslemeyen açı.
        _aci("Neptune", "Pluto", "sextile", 1.0),
    ],
    "relationship_score": {"score": 82, "description": "yüksek"},
}


def _eksen(sonuc, ad):
    return next(e for e in sonuc["axes"] if e["axis"] == ad)


class TestEksenHesabi:
    def test_dort_eksen_ve_seviyeler(self):
        sonuc = synastry_service.relationship_axes(SAHTE_SINASTRI)
        assert [e["axis"] for e in sonuc["axes"]] == list(
            synastry_service.AXES)
        assert _eksen(sonuc, "communication")["level"] in (
            "present", "strong")
        assert _eksen(sonuc, "attraction")["level"] == "light"

    def test_sert_aci_ayri_eksende_ikinci_kez_sayilmaz(self):
        """Satürn kare Ay duygusal ekseni AKTİVE eder ve TONUNU zorlar."""
        karisik = {"aspects": [
            _aci("Moon", "Venus", "conjunction", 0.9),
            _aci("Saturn", "Moon", "square", 0.5),
        ]}
        duygu = _eksen(synastry_service.relationship_axes(karisik),
                       "emotional")
        assert duygu["level"] != "quiet"
        assert duygu["tone"] == "mixed"
        assert len(duygu["basis"]) == 2
        # "friction" diye bağımsız bir eksen YOK (çift sayımın kaynağıydı).
        sonuc = synastry_service.relationship_axes(SAHTE_SINASTRI)
        assert "friction" not in [e["axis"] for e in sonuc["axes"]]

    def test_aci_birden_cok_eksene_girebilir(self):
        """Merkür–Ay teması hem iletişimi hem duyguyu ilgilendirir."""
        sonuc = synastry_service.relationship_axes(
            {"aspects": [_aci("Mercury", "Moon", "trine", 0.4)]})
        assert _eksen(sonuc, "communication")["count"] == 1
        assert _eksen(sonuc, "emotional")["count"] == 1

    def test_ton_harmonik_dengesinden(self):
        akici = {"aspects": [_aci("Mercury", "Sun", "trine", 0.5)]}
        zorlu = {"aspects": [_aci("Mercury", "Sun", "square", 0.5)]}
        assert _eksen(synastry_service.relationship_axes(akici),
                      "communication")["tone"] == "flowing"
        assert _eksen(synastry_service.relationship_axes(zorlu),
                      "communication")["tone"] == "challenging"

    def test_puan_asla_donmez(self):
        """Sayısal uyum puanı ürün kararıyla GİZLİ — sızıntı olmamalı."""
        sonuc = synastry_service.relationship_axes(SAHTE_SINASTRI)
        düz = repr(sonuc)
        assert "82" not in düz and "score" not in düz

    def test_dayanak_gercek_acilari_tasir(self):
        sonuc = synastry_service.relationship_axes(SAHTE_SINASTRI)
        kanit = _eksen(sonuc, "communication")["basis"]
        assert kanit and len(kanit) <= synastry_service.MAX_BASIS
        # En güçlü kanıt: dar orblu KAVUŞUM (kavuşum ağırlığı üçgeni geçer).
        assert (kanit[0]["aspect"], kanit[0]["orb"]) == ("conjunction", 0.5)
        assert kanit[0]["supportive"] is True
        assert all("weight" not in k for k in kanit)

    def test_bos_sinastri_cokmez(self):
        sonuc = synastry_service.relationship_axes({"aspects": []})
        assert all(e["level"] == "quiet" and e["basis"] == []
                   for e in sonuc["axes"])

    def test_determinist(self):
        a = synastry_service.relationship_axes(SAHTE_SINASTRI)
        b = synastry_service.relationship_axes(SAHTE_SINASTRI)
        assert a == b

    def test_gercek_haritalarda_eksenler_olculur(self):
        """Kalibrasyon bekçisi: gerçek bir çiftte eksenler ölü kalmamalı.

        Eşikler beş gerçek çiftin dağılımına göre seçildi; eşleme ya da
        eşikler bozulursa bu test 'her eksen sessiz' diyerek yakalar.
        """
        def kw(name, y, m, d, h, mi, city):
            return dict(name=name, year=y, month=m, day=d, hour=h,
                        minute=mi, city=city, nation=None)

        ham = astro_service.get_synastry(
            kw("a", 1990, 5, 12, 14, 30, "Istanbul"),
            kw("b", 1988, 11, 3, 9, 15, "Ankara"))
        sonuc = synastry_service.relationship_axes(ham)
        sessiz = [e["axis"] for e in sonuc["axes"] if e["level"] == "quiet"]
        assert len(sessiz) <= 1, f"eksenler ölü: {sessiz}"
        assert sonuc["lead_axis"] in synastry_service.AXES


class TestYerellestirme:
    def test_tr_ve_en_metinleri(self):
        sonuc = synastry_service.relationship_axes(SAHTE_SINASTRI)
        tr = prompts.localize_relationship_axes("tr", sonuc)
        iletisim = next(e for e in tr["axes"]
                        if e["axis"] == "communication")
        assert iletisim["axis_local"] == "İletişim"
        assert iletisim["level_local"] in ("Belirgin", "Güçlü")
        assert iletisim["line"]
        assert iletisim["basis"][0]["p1_local"] == "Merkür"
        assert iletisim["basis"][0]["aspect_local"] == "Kavuşum"
        assert "puan vermez" in tr["footnote"]

        en = prompts.localize_relationship_axes("en", sonuc)
        ing = next(e for e in en["axes"] if e["axis"] == "communication")
        assert ing["axis_local"] == "Communication"
        assert "does not score" in en["footnote"]

    def test_her_eksen_ton_ciftinin_metni_var(self):
        for lang in ("tr", "en"):
            p = prompts.get(lang)
            for eksen in synastry_service.AXES:
                for ton in ("flowing", "mixed", "challenging", "quiet"):
                    assert p.SYNASTRY_AXIS_LINES[eksen][ton], (lang, eksen,
                                                               ton)

    def test_sessiz_seviye_niteliksiz_cumle_alir(self):
        """Ölçülmemiş bağa 'akıcı/zorlayıcı' denmez."""
        ham = {"axes": [{"axis": "bond", "level": "quiet",
                         "tone": "flowing", "basis": []}]}
        tr = prompts.localize_relationship_axes("tr", ham)
        assert "ölçülmüyor" in tr["axes"][0]["line"]

    def test_zorlayici_ton_kotu_demez(self):
        """Sürtünme 'kötü ilişki' diye sunulmaz — olgunlaştıran yer denir."""
        tr = prompts.get("tr").SYNASTRY_AXIS_LINES["bond"]["challenging"]
        assert "olgunlaştırıyor" in tr
