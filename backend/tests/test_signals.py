"""Sinyal motoru bekçileri (R2-S1).

Sıralama ve tema eşleme DETERMİNİST olmalı: aynı takvim + aynı harita =
aynı sinyaller. Takvim ve natal olgular sahtelenir; burada test edilen şey
efemeris değil, puanlama/tema/çeşitlilik kuralları ve başlık şablonlarıdır.
"""
from __future__ import annotations

from services import prompts, signal_service


#: 16 Ağustos gününe kurulu sahte takvim. Kuzey Düğümü adayı bilerek var:
#: sinyale GİRMEMELİ (_SINYAL_NATAL yedili + eksenlerle sınırlı).
SAHTE_TAKVIM = {
    "calc_version": "3",
    "start": "2026-08-16",
    "days": 8,
    "events": [
        {"date": "2026-08-18", "type": "aspect_exact", "transit": "Saturn",
         "natal": "Moon", "aspect": "square", "orb": 0.1},
        {"date": "2026-08-20", "type": "aspect_exact", "transit": "Jupiter",
         "natal": "Venus", "aspect": "trine", "orb": 0.2},
        {"date": "2026-08-17", "type": "station_retrograde",
         "transit": "Uranus"},
    ],
    "active_now": [
        {"transit": "Saturn", "natal": "Moon", "aspect": "square",
         "orb": 0.8, "movement": "applying"},
        {"transit": "Uranus", "natal": "Medium_Coeli",
         "aspect": "conjunction", "orb": 2.4, "movement": "applying"},
        {"transit": "Chiron", "natal": "True_North_Lunar_Node",
         "aspect": "sextile", "orb": 0.1, "movement": "separating"},
    ],
    "disclosures": [],
}

SAHTE_NATAL = {
    "sun": {"planet": "Sun", "sign": "taurus", "house": 10},
    "moon": {"planet": "Moon", "sign": "cancer", "house": 4},
    "ascendant": "leo",
    "placements": [
        {"planet": "Venus", "sign": "aries", "house": 8},
    ],
}

DOGUM = {"name": "t", "year": 1990, "month": 5, "day": 12,
         "hour": 14, "minute": 30, "city": "Istanbul", "nation": None}


def _hesapla(monkeypatch, takvim=None, natal=SAHTE_NATAL):
    monkeypatch.setattr(signal_service.predict_service, "transit_calendar",
                        lambda **kw: takvim or SAHTE_TAKVIM)
    return signal_service.compute_signals(DOGUM, natal=natal)


class TestSiralamaVeTema:
    def test_determinist_siralama_ve_ust_sinir(self, monkeypatch):
        ham = _hesapla(monkeypatch)
        sinyaller = ham["signals"]
        assert len(sinyaller) <= signal_service.MAX_SIGNALS
        # Puan: Satürn-Ay (aktif, dar orb, yaklaşan, ışık) > Uranüs-MC >
        # Jüpiter-Venüs (henüz orb dışında, 4 gün uzakta).
        assert [(s["transit"], s["natal"]) for s in sinyaller] == [
            ("Saturn", "Moon"), ("Uranus", "Medium_Coeli"),
            ("Jupiter", "Venus")]
        # Aynı girdi -> aynı çıktı (determinizm).
        tekrar = _hesapla(monkeypatch)
        assert [s["score"] for s in tekrar["signals"]] == [
            s["score"] for s in sinyaller]

    def test_dugum_sinyal_olmaz(self, monkeypatch):
        ham = _hesapla(monkeypatch)
        assert all(s["natal"] != "True_North_Lunar_Node"
                   for s in ham["signals"])

    def test_dayanak_alanlari_dolu(self, monkeypatch):
        """Her sinyal 'Neden?' alt-sayfasının çizeceği dayanağı taşımalı."""
        birinci = _hesapla(monkeypatch)["signals"][0]
        assert birinci["transit"] == "Saturn"
        assert birinci["aspect"] == "square"
        assert birinci["orb"] == 0.8
        assert birinci["movement"] == "applying"
        assert birinci["exact_on"] == "2026-08-18"
        assert birinci["days_to_exact"] == 2
        assert birinci["natal_sign"] == "cancer"
        assert birinci["natal_house"] == 4
        assert birinci["theme"] == "inner"  # Ay natal 4. evde

    def test_ev_temasi_ve_nokta_yedegi(self, monkeypatch):
        ham = _hesapla(monkeypatch)
        temalar = {(s["transit"], s["natal"]): s["theme"]
                   for s in ham["signals"]}
        assert temalar[("Uranus", "Medium_Coeli")] == "career"  # ev 10
        assert temalar[("Jupiter", "Venus")] == "finance"       # ev 8
        # Natal olgular yoksa nokta tabanlı temaya düşülür, alanlar uydurulmaz.
        monkeypatch.setattr(signal_service.chart_context, "natal_facts",
                            lambda birth: (_ for _ in ()).throw(RuntimeError))
        monkeypatch.setattr(signal_service.predict_service,
                            "transit_calendar", lambda **kw: SAHTE_TAKVIM)
        yedek = signal_service.compute_signals(DOGUM)
        ay = next(s for s in yedek["signals"] if s["natal"] == "Moon")
        assert ay["theme"] == "inner"
        assert "natal_sign" not in ay and "natal_house" not in ay

    def test_tema_cesitliligi(self, monkeypatch):
        """2. ve 3. sırada kullanılmamış temanın en güçlüsü öne geçer."""
        takvim = {**SAHTE_TAKVIM, "events": [], "active_now": [
            # İki güçlü kariyer adayı + bir zayıf ilişki adayı.
            {"transit": "Saturn", "natal": "Sun", "aspect": "conjunction",
             "orb": 0.3, "movement": "applying"},
            {"transit": "Uranus", "natal": "Medium_Coeli",
             "aspect": "square", "orb": 0.5, "movement": "applying"},
            {"transit": "Jupiter", "natal": "Venus", "aspect": "sextile",
             "orb": 2.8, "movement": "separating"},
        ]}
        natal = {**SAHTE_NATAL, "placements": [
            {"planet": "Venus", "sign": "aries", "house": 7}]}
        ham = _hesapla(monkeypatch, takvim=takvim, natal=natal)
        # 1: Satürn-Güneş (kariyer). 2: kullanılmamış tema (ilişkiler)
        # puanı düşük de olsa öne geçer. 3: kalan kariyer adayı.
        assert [s["theme"] for s in ham["signals"]] == [
            "career", "relationships", "career"]


class TestYerellestirme:
    def test_baslik_tr_kesinlesme(self, monkeypatch):
        ham = _hesapla(monkeypatch)
        yerel = prompts.localize_signals("tr", ham)
        birinci = yerel["signals"][0]
        assert birinci["headline"] == (
            "Satürn, natal Ay ile Kare açısını 18 Ağustos günü "
            "kesinleştiriyor.")
        assert birinci["theme_local"] == "İç dünya"
        assert birinci["natal_sign_local"] == "Yengeç"

    def test_baslik_en_kesinlesme(self, monkeypatch):
        ham = _hesapla(monkeypatch)
        yerel = prompts.localize_signals("en", ham)
        assert yerel["signals"][0]["headline"] == (
            "Saturn perfects its Square to your natal Moon on August 18.")

    def test_baslik_bugun_ve_ayrilan(self):
        bugun = {"generated_for": "2026-08-16", "signals": [
            {"transit": "Saturn", "natal": "Moon", "aspect": "square",
             "orb": 0.1, "movement": "applying", "active": True,
             "exact_on": "2026-08-16", "days_to_exact": 0,
             "theme": "inner"},
            {"transit": "Jupiter", "natal": "Sun", "aspect": "trine",
             "orb": 1.4, "movement": "separating", "active": True,
             "theme": "career"},
        ]}
        yerel = prompts.localize_signals("tr", bugun)
        assert "bugün kesinleştiriyor" in yerel["signals"][0]["headline"]
        assert "etkisi sönüyor" in yerel["signals"][1]["headline"]

    def test_insight_oldugu_gibi_tasinir(self):
        veri = {"signals": [
            {"transit": "Saturn", "natal": "Moon", "aspect": "square",
             "orb": 1.0, "movement": "applying", "active": True,
             "theme": "inner", "insight": "Deneme yorumu."}]}
        yerel = prompts.localize_signals("tr", veri)
        assert yerel["signals"][0]["insight"] == "Deneme yorumu."


class TestYorumKatmani:
    HAM = {"generated_for": "2026-08-16", "signals": [
        {"transit": "Saturn", "natal": "Moon", "aspect": "square",
         "orb": 0.8, "exact_on": "2026-08-18", "theme": "inner"},
        {"transit": "Uranus", "natal": "Medium_Coeli",
         "aspect": "conjunction", "orb": 2.4, "theme": "career"},
    ]}

    def test_dogru_bicim_liste_doner(self, monkeypatch):
        monkeypatch.setattr(
            signal_service.gemini_service, "generate",
            lambda prompt, lang=None: "1. Birinci yorum.\n2. İkinci yorum.")
        yorumlar = signal_service.signal_insights(self.HAM, "tr")
        assert yorumlar == ["Birinci yorum.", "İkinci yorum."]

    def test_satir_sayisi_tutmazsa_none(self, monkeypatch):
        monkeypatch.setattr(signal_service.gemini_service, "generate",
                            lambda prompt, lang=None: "1. Tek satır.")
        assert signal_service.signal_insights(self.HAM, "tr") is None

    def test_asiri_uzun_satir_none(self, monkeypatch):
        uzun = "1. " + "ç" * 200 + "\n2. Kısa."
        monkeypatch.setattr(signal_service.gemini_service, "generate",
                            lambda prompt, lang=None: uzun)
        assert signal_service.signal_insights(self.HAM, "tr") is None

    def test_parmak_izi_tarih_ve_kumeye_bagli(self):
        iz1 = signal_service.signals_fingerprint(self.HAM)
        iz2 = signal_service.signals_fingerprint(
            {**self.HAM, "generated_for": "2026-08-17"})
        assert iz1 != iz2


PROFIL = {"uid": "u1", "birthDate": "1990-05-12", "birthTime": "14:30",
          "birthCity": "Istanbul", "displayName": "t"}


class TestOnbellekVeBildirim:
    def test_cached_signals_gunde_bir_hesaplar(self, monkeypatch):
        """Uç ve bildirim aynı kaydı paylaşır: ikinci çağrı hesap yapmaz.

        Önbellek BELLEK-İÇİ sahteyle izole edilir: gerçek katman kalıcı
        (dosya/Firestore) olduğu için sabit anahtar önceki test KOŞUSUNDAN
        dönebilir ve sayaç hiç artmazdı (tam takımda bir kez düştü).
        """
        import datetime as dt
        import core.cache as cache_mod
        depo: dict = {}
        monkeypatch.setattr(cache_mod, "get", depo.get)
        monkeypatch.setattr(
            cache_mod, "set",
            lambda k, v, ttl_seconds=0, owner_uid=None: depo.update({k: v}))

        sayac = {"n": 0}

        def sahte_hesap(birth, hour_known=True):
            sayac["n"] += 1
            return {"calc_version": "1", "generated_for": "2099-01-01",
                    "signals": [], "disclosures": []}

        monkeypatch.setattr(signal_service, "compute_signals", sahte_hesap)
        gun = dt.date(2099, 1, 1)
        birinci = signal_service.cached_signals(PROFIL, today=gun)
        ikinci = signal_service.cached_signals(PROFIL, today=gun)
        assert birinci == ikinci
        assert sayac["n"] == 1

    def test_cached_signals_dogum_verisi_yoksa_none(self):
        assert signal_service.cached_signals({"uid": "u2"}) is None

    def test_bildirim_govdesi_bir_numarali_sinyal(self, monkeypatch):
        from services import notification_service
        ham = {"generated_for": "2026-08-16", "signals": [
            {"transit": "Saturn", "natal": "Moon", "aspect": "square",
             "orb": 0.8, "movement": "applying", "active": True,
             "exact_on": "2026-08-18", "days_to_exact": 2,
             "theme": "inner"}], "disclosures": []}
        monkeypatch.setattr(signal_service, "cached_signals",
                            lambda profile, today=None: ham)
        govde = notification_service.signal_push_body(PROFIL, "tr")
        assert govde == ("Satürn, natal Ay ile Kare açısını 18 Ağustos "
                         "günü kesinleştiriyor.")

    def test_bildirim_sinyal_yoksa_none(self, monkeypatch):
        """None dönüşü çağıranı paylaşımlı burç satırına düşürür."""
        from services import notification_service
        monkeypatch.setattr(signal_service, "cached_signals",
                            lambda profile, today=None: None)
        assert notification_service.signal_push_body(PROFIL, "tr") is None

    def test_bildirim_uzun_satiri_reddeder(self, monkeypatch):
        from services import notification_service, prompts
        ham = {"signals": [{"transit": "Saturn", "natal": "Moon",
                            "aspect": "square", "theme": "inner"}]}
        monkeypatch.setattr(signal_service, "cached_signals",
                            lambda profile, today=None: ham)
        monkeypatch.setattr(
            prompts, "localize_signals",
            lambda lang, data: {"signals": [{"headline": "u" * 200}]})
        assert notification_service.signal_push_body(PROFIL, "tr") is None

    def test_bildirim_hatada_dusmez(self, monkeypatch):
        """Sinyal hesabı düşerse bildirim düşmez; None ile yedeğe geçilir."""
        from services import notification_service
        monkeypatch.setattr(
            signal_service, "cached_signals",
            lambda profile, today=None: (_ for _ in ()).throw(RuntimeError))
        assert notification_service.signal_push_body(PROFIL, "tr") is None
