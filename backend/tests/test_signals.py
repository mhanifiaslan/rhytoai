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

    def test_ayrilan_aci_geri_duser(self, monkeypatch):
        """Sönen etki, aynı koşuldaki yaklaşan etkinin arkasında kalır."""
        takvim = {**SAHTE_TAKVIM, "events": [], "active_now": [
            {"transit": "Saturn", "natal": "Sun", "aspect": "square",
             "orb": 1.0, "movement": "separating"},
            {"transit": "Saturn", "natal": "Moon", "aspect": "square",
             "orb": 1.0, "movement": "applying"},
        ]}
        ham = _hesapla(monkeypatch, takvim=takvim)
        assert [s["natal"] for s in ham["signals"]] == ["Moon", "Sun"]

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
    """R2-S6: kart yüzeyi GÜNDELİK dil, teknik satır dayanak sayfasında."""

    #: Kart cümlesinde ASLA geçmemesi gereken jargon (kullanıcı geri
    #: bildirimi: "Kiron natal Venüs ile üçgen açısına yaklaşıyor" —
    #: anlamsız). Teknik terimler ayrı bir alanda, ayrı bir ekranda.
    JARGON_TR = ["Kiron", "Satürn", "Venüs", "natal", "Kare", "Üçgen",
                 "orb", "°"]
    JARGON_EN = ["Chiron", "Saturn", "Venus", "natal", "Square", "Trine",
                 "orb", "°"]

    def test_kart_cumlesi_tr_gundelik_dil(self, monkeypatch):
        ham = _hesapla(monkeypatch)
        birinci = prompts.localize_signals("tr", ham)["signals"][0]
        # Ay natal 4. evde + kare → iç dünya / gerilim.
        assert birinci["headline"] == (
            "İç dünyanda gerilim yükseliyor; kendine fazla yüklenmemek "
            "bugünün işi.")
        assert birinci["theme_local"] == "İç dünya"
        assert birinci["timing_local"] == "18 Ağustos günü netleşiyor"
        for jargon in self.JARGON_TR:
            assert jargon not in birinci["headline"], jargon

    def test_kart_cumlesi_en_gundelik_dil(self, monkeypatch):
        ham = _hesapla(monkeypatch)
        birinci = prompts.localize_signals("en", ham)["signals"][0]
        assert birinci["headline"] == (
            "Inner tension is rising; not overloading yourself is "
            "today's work.")
        assert birinci["timing_local"] == "Peaks on August 18"
        for jargon in self.JARGON_EN:
            assert jargon not in birinci["headline"], jargon

    def test_teknik_satir_dayanakta_durur(self, monkeypatch):
        """Teknik bilgi KAYBOLMAZ — 'Neye dayanıyor?' sayfasının ilk satırı."""
        ham = _hesapla(monkeypatch)
        birinci = prompts.localize_signals("tr", ham)["signals"][0]
        assert birinci["technical"] == (
            "Satürn, natal Ay ile Kare açısını 18 Ağustos günü "
            "kesinleştiriyor.")
        assert birinci["natal_sign_local"] == "Yengeç"
        ing = prompts.localize_signals("en", ham)["signals"][0]
        assert ing["technical"] == (
            "Saturn perfects its Square to your natal Moon on August 18.")

    def test_her_tema_ton_ciftinin_cumlesi_var(self):
        """Eksik kombinasyon kartı teknik cümleye düşürürdü — sessiz kusur."""
        for lang in ("tr", "en"):
            p = prompts.get(lang)
            for tema in signal_service.THEMES:
                for ton in ("support", "tension", "focus"):
                    cumle = p.SIGNAL_HUMAN_LINES[tema][ton]
                    assert cumle and len(cumle) <= 110, (lang, tema, ton)

    def test_zamanlama_satirlari(self):
        bugun = {"generated_for": "2026-08-16", "signals": [
            {"transit": "Saturn", "natal": "Moon", "aspect": "square",
             "orb": 0.1, "movement": "applying", "active": True,
             "exact_on": "2026-08-16", "days_to_exact": 0,
             "theme": "inner", "tone": "tension"},
            {"transit": "Jupiter", "natal": "Sun", "aspect": "trine",
             "orb": 1.4, "movement": "separating", "active": True,
             "theme": "career", "tone": "support"},
        ]}
        yerel = prompts.localize_signals("tr", bugun)
        assert yerel["signals"][0]["timing_local"] == "Bugün kesinleşiyor"
        assert yerel["signals"][1]["timing_local"] == "Etkisi sönüyor"
        assert "bugün kesinleştiriyor" in yerel["signals"][0]["technical"]

    def test_ton_acidan_turetilir(self, monkeypatch):
        ham = _hesapla(monkeypatch)
        tonlar = {(s["transit"], s["aspect"]): s["tone"]
                  for s in ham["signals"]}
        assert tonlar[("Saturn", "square")] == "tension"
        assert tonlar[("Jupiter", "trine")] == "support"
        assert tonlar[("Uranus", "conjunction")] == "focus"

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


class TestTakvimYorumu:
    """Ç1/Ç6: `calendar_insights` — `signal_insights`'la (R2-S1) BİREBİR
    AYNI biçim/doğrulama deseninde çalışır, ama eşleşme SIRAYLA değil
    `event_fingerprint` KİMLİĞİYLE yapılır (takvim olayları sinyaller gibi
    sabit-3'lük bir liste değil).

    `test_cakisma_bekcisi_farkli_olaylar_farkli_cumle_alir` bu turun ÖLÇÜLMÜŞ
    kusurunu birebir yakalar: eskiden `SIGNAL_HUMAN_LINES` (4 tema × 3 ton
    = 12 sabit cümle) yüzünden 30 günlük takvimde birçok farklı astrolojik
    olay (özellikle "iç dünya"/Ay simgesi teması) BİREBİR AYNI cümleye
    düşüyordu; bir örnek haritada bir günde üç olay aynı cümleyi üç kez
    gösterdi.
    """

    OLAYLAR = [
        {"date": "2026-08-18", "type": "aspect_exact", "transit": "Saturn",
         "natal": "Moon", "aspect": "square", "theme": "inner",
         "tone": "tension"},
        {"date": "2026-08-20", "type": "aspect_exact", "transit": "Uranus",
         "natal": "Mercury", "aspect": "conjunction", "theme": "inner",
         "tone": "focus"},
        {"date": "2026-09-10", "type": "aspect_exact", "transit": "Neptune",
         "natal": "Sun", "aspect": "square", "theme": "inner",
         "tone": "tension"},
        # İstasyonun teması yok — havuzdan düşmeli (SIGNAL_HUMAN_LINES'ta
        # istasyonların zaten hiç cümlesi yoktu, bu yeni fonksiyonda da
        # olmamalı).
        {"date": "2026-08-25", "type": "station_retrograde",
         "transit": "Pluto"},
    ]

    def test_dogru_bicimde_parmak_izine_eslenir(self, monkeypatch):
        monkeypatch.setattr(
            signal_service.gemini_service, "generate",
            lambda prompt, lang=None: "1. Birinci.\n2. İkinci.\n3. Üçüncü.")
        yorumlar = signal_service.calendar_insights(self.OLAYLAR, "tr")
        assert len(yorumlar) == 3
        for o, beklenen in zip(self.OLAYLAR[:3],
                               ["Birinci.", "İkinci.", "Üçüncü."]):
            assert yorumlar[signal_service.event_fingerprint(o)] == beklenen

    def test_istasyon_ve_temasiz_olay_promptan_cikar(self, monkeypatch):
        yakalanan = {}

        def sahte_uret(prompt, lang=None):
            yakalanan["prompt"] = prompt
            return "1. Birinci.\n2. İkinci.\n3. Üçüncü."

        monkeypatch.setattr(signal_service.gemini_service, "generate",
                            sahte_uret)
        signal_service.calendar_insights(self.OLAYLAR, "tr")
        assert "Pluto" not in yakalanan["prompt"]

    def test_satir_sayisi_tutmazsa_none(self, monkeypatch):
        monkeypatch.setattr(signal_service.gemini_service, "generate",
                            lambda prompt, lang=None: "1. Tek satır.")
        assert signal_service.calendar_insights(self.OLAYLAR, "tr") is None

    def test_asiri_uzun_satir_none(self, monkeypatch):
        uzun = "1. " + "ç" * 200 + "\n2. Kısa.\n3. Kısa."
        monkeypatch.setattr(signal_service.gemini_service, "generate",
                            lambda prompt, lang=None: uzun)
        assert signal_service.calendar_insights(self.OLAYLAR, "tr") is None

    def test_temali_olay_yoksa_cagirmadan_none(self, monkeypatch):
        """Yalnız istasyon varsa LLM'e hiç gidilmez — boşuna harcama yok."""
        cagrildi = {"n": 0}

        def sahte_uret(prompt, lang=None):
            cagrildi["n"] += 1
            return "1. x"

        monkeypatch.setattr(signal_service.gemini_service, "generate",
                            sahte_uret)
        istasyonlar = [o for o in self.OLAYLAR if o["type"] != "aspect_exact"]
        assert signal_service.calendar_insights(istasyonlar, "tr") is None
        assert cagrildi["n"] == 0

    def test_yigin_ust_siniri_uygulanir(self, monkeypatch):
        """20'den fazla açı-kesinleşmesi verilse bile yalnız ilk
        CALENDAR_INSIGHT_MAX_EVENTS kadarı promta girer — maliyet tavanı
        (Ç-turu ölçümü: gerçek 30-90 günlük takvimlerde 3-17 olay çıktı)."""
        cok = [{"date": f"2026-{(i % 12) + 1:02d}-10", "type": "aspect_exact",
               "transit": "Saturn", "natal": f"Point{i}", "aspect": "square",
               "theme": "inner"} for i in range(30)]
        yakalanan = {}

        def sahte_uret(prompt, lang=None):
            yakalanan["prompt"] = prompt
            n = signal_service.CALENDAR_INSIGHT_MAX_EVENTS
            return "\n".join(f"{i}. Yorum {i}." for i in range(1, n + 1))

        monkeypatch.setattr(signal_service.gemini_service, "generate",
                            sahte_uret)
        yorumlar = signal_service.calendar_insights(cok, "tr")
        assert len(yorumlar) == signal_service.CALENDAR_INSIGHT_MAX_EVENTS
        assert "Point20" not in yakalanan["prompt"]  # 21. olay dışarda kaldı

    def test_cakisma_bekcisi_farkli_olaylar_farkli_cumle_alir(
            self, monkeypatch):
        """Bu turun ölçülen kusurunu birebir yakalar (bkz. sınıf docstring).

        Beşi de 'inner' temasında — eski tabloda hepsi aynı 1-2 cümleye
        düşerdi. Burada model beş FARKLI cümle üretir (sahtelenmiş) ve
        fonksiyonun bunları beş AYRI olaya, birbirine karıştırmadan
        eşlediği doğrulanır: ne çakışma (aynı cümle iki olaya), ne kayıp
        (bir olay cümlesiz kalması).
        """
        genis_takvim = [
            {"date": f"2026-09-{d:02d}", "type": "aspect_exact",
             "transit": t, "natal": n, "aspect": "square", "theme": "inner"}
            for d, (t, n) in enumerate(
                [("Uranus", "Mercury"), ("Uranus", "Venus"),
                 ("Neptune", "Sun"), ("Neptune", "Ascendant"),
                 ("Pluto", "Moon")], start=1)
        ]
        monkeypatch.setattr(
            signal_service.gemini_service, "generate",
            lambda prompt, lang=None: "\n".join(
                f"{i}. Bu olaya özgü {i}. cümle." for i in range(1, 6)))
        yorumlar = signal_service.calendar_insights(genis_takvim, "tr")
        assert len(yorumlar) == 5
        assert len(set(yorumlar.values())) == 5  # tekrar YOK
        for i, o in enumerate(genis_takvim, 1):
            assert yorumlar[signal_service.event_fingerprint(o)] == (
                f"Bu olaya özgü {i}. cümle.")


class TestTakvimParmakIzi:
    """`event_fingerprint` + `calendar_fingerprint`: önbellek anahtarının
    dayandığı kararlı kimlik."""

    def test_event_fingerprint_kararli_ve_ayirt_edici(self):
        o1 = {"transit": "Saturn", "natal": "Moon", "aspect": "square",
              "date": "2026-08-18"}
        o2 = {**o1}
        o3 = {**o1, "date": "2026-09-07"}  # yalnız tarih farklı
        assert signal_service.event_fingerprint(o1) == \
            signal_service.event_fingerprint(o2)
        assert signal_service.event_fingerprint(o1) != \
            signal_service.event_fingerprint(o3)

    def test_calendar_fingerprint_farkli_kumeler_farkli_iz(self):
        temel = [{"type": "aspect_exact", "theme": "inner",
                  "transit": "Saturn", "natal": "Moon", "aspect": "square",
                  "date": "2026-08-18"}]
        genisletilmis = temel + [{"type": "aspect_exact", "theme": "career",
                                  "transit": "Jupiter", "natal": "Sun",
                                  "aspect": "trine", "date": "2026-08-20"}]
        assert signal_service.calendar_fingerprint(temel) != \
            signal_service.calendar_fingerprint(genisletilmis)

    def test_calendar_fingerprint_istasyonu_ve_temasizi_saymaz(self):
        """İmzaya yalnız temalı açı-kesinleşmeleri girer — istasyon
        değişse de takvim yorumu önbelleği boşuna tazelenmemeli."""
        temel = [{"type": "aspect_exact", "theme": "inner",
                  "transit": "Saturn", "natal": "Moon", "aspect": "square",
                  "date": "2026-08-18"}]
        istasyonlu = temel + [{"type": "station_retrograde",
                               "transit": "Pluto", "date": "2026-08-25"}]
        temasiz = temel + [{"type": "aspect_exact", "transit": "Mars",
                            "natal": "Sun", "aspect": "opposition",
                            "date": "2026-08-19"}]  # theme yok
        assert signal_service.calendar_fingerprint(temel) == \
            signal_service.calendar_fingerprint(istasyonlu)
        assert signal_service.calendar_fingerprint(temel) == \
            signal_service.calendar_fingerprint(temasiz)


class TestSignalHumanLinesKapsami:
    """Ç4/Ç5 regresyon bekçisi: `SIGNAL_HUMAN_LINES` yalnız sinyal
    kartlarının ücretsiz-katman son çaresinde yaşamalı. Takvim bir daha
    bu tabloyu kullanmaya BAŞLARSA (ör. birileri eski satırı geri
    yapıştırırsa) bu test kırılır — tam bu turun kusurunun geri gelmesini
    yakalayacak şekilde tasarlandı.
    """

    def test_takvim_yerellestirmesi_tabloya_dokunmaz(self):
        """`.SIGNAL_HUMAN_LINES` ERİŞİMİ (gerçek kullanım) aranır — takvimin
        önceki davranışını AÇIKLAYAN yorum satırındaki bare isim geçişi
        (`SIGNAL_HUMAN_LINES` tırnaksız anılıyor) bilerek dışarıda
        bırakılır; asıl tehlike kodun tabloyu tekrar OKUMASIdır."""
        import inspect
        kaynak = inspect.getsource(prompts.localize_transit_calendar)
        assert ".SIGNAL_HUMAN_LINES" not in kaynak

    def test_sinyal_yerellestirmesi_hala_tabloyu_kullanir(self):
        """Ters yönde de bir bekçi: tablo YANLIŞLIKLA sinyal kartlarından
        da silinmemeli (Ç5'te bilerek geri konan davranış)."""
        import inspect
        kaynak = inspect.getsource(prompts.localize_signals)
        assert ".SIGNAL_HUMAN_LINES" in kaynak


class TestTakvimZenginlestirme:
    """R2-Z1: 90 günlük takvim olayları sinyallerle aynı tema/ton dilini
    taşır; istasyonlara tema UYDURULMAZ."""

    OLAYLAR = [
        {"date": "2026-08-18", "type": "aspect_exact", "transit": "Saturn",
         "natal": "Moon", "aspect": "square", "orb": 0.1},
        {"date": "2026-08-20", "type": "station_retrograde",
         "transit": "Uranus"},
    ]

    def test_kesinlesme_tema_ton_alir_istasyon_almaz(self):
        zengin = signal_service.enrich_events(self.OLAYLAR, SAHTE_NATAL)
        kesin, istasyon = zengin
        assert kesin["theme"] == "inner" and kesin["tone"] == "tension"
        assert kesin["natal_sign"] == "cancer"
        assert "theme" not in istasyon and "tone" not in istasyon

    def test_natal_yoksa_temasiz_ama_cokmez(self):
        zengin = signal_service.enrich_events(self.OLAYLAR, None)
        assert zengin[0]["theme"] == "inner"  # nokta tabanlı yedek (Ay)
        assert "natal_sign" not in zengin[0]

    def test_yerellestirme_teknik_hep_var_line_onceden_yazilirsa_gecer(self):
        """Ç-turu: `line` artık tema×ton tablosundan DEĞİL, olaya ÖNCEDEN
        yazılmış AI metninden gelir (`api/astrology.py`'nin
        `calendar_insights` sonucunu olaya yazdığı yer). Bu fonksiyon
        yalnız TAŞIR — kendi başına üretmez.

        Ölçülen kusur tam olarak buydu: eskiden burası tema+ton'a bakıp
        12 sabit cümleden birini seçiyordu ve 30 günde birçok farklı olay
        birebir aynı cümleye düşüyordu.
        """
        zengin = signal_service.enrich_events(self.OLAYLAR, SAHTE_NATAL)
        cal = {"start": "2026-08-16", "days": 90, "events": zengin,
               "active_now": [], "disclosures": []}
        yerel = prompts.localize_transit_calendar("tr", cal)
        kesin = yerel["events"][0]
        # Teknik dayanak HER ZAMAN üretilir (tema+ton'dan bağımsız,
        # `SIGNAL_LINE_EXACT` şablonundan) — bu değişmedi.
        assert kesin["theme_local"] == "İç dünya"
        assert "Satürn" in kesin["technical"]
        assert kesin["date_local"] == "18 Ağustos"
        # `line` önceden yazılmadıysa BOŞ kalır — sabit cümleye DÜŞMEZ.
        assert kesin["line"] == ""
        # İstasyon satırı eski davranışını korur.
        istasyon = yerel["events"][1]
        assert "line" not in istasyon
        assert istasyon["type_local"] == "retroya dönüş"

    def test_onceden_yazilmis_ai_metni_oldugu_gibi_tasinir(self):
        """`api/astrology.py` `line`'ı olaya YAZDIKTAN SONRA çağırır —
        localize bunu değiştirmeden geçirmeli."""
        zengin = signal_service.enrich_events(self.OLAYLAR, SAHTE_NATAL)
        zengin[0] = {**zengin[0], "line": "Bu çift o güne özgü bir cümle."}
        cal = {"start": "2026-08-16", "days": 90, "events": zengin,
               "active_now": [], "disclosures": []}
        yerel = prompts.localize_transit_calendar("tr", cal)
        assert yerel["events"][0]["line"] == "Bu çift o güne özgü bir cümle."


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

    def test_bildirim_bir_numarali_sinyalden(self, monkeypatch):
        """Bildirimde de kart cümlesi görünür — jargon telefona düşmez."""
        from services import notification_service
        ham = {"generated_for": "2026-08-16", "signals": [
            {"transit": "Saturn", "natal": "Moon", "aspect": "square",
             "orb": 0.8, "movement": "applying", "active": True,
             "exact_on": "2026-08-18", "days_to_exact": 2,
             "theme": "inner", "tone": "tension"}], "disclosures": []}
        monkeypatch.setattr(signal_service, "cached_signals",
                            lambda profile, today=None: ham)
        baslik, govde = notification_service.signal_push(PROFIL, "tr")
        assert baslik == "Bugün: İç dünya"
        assert govde == ("İç dünyanda gerilim yükseliyor; kendine fazla "
                         "yüklenmemek bugünün işi.")
        assert "natal" not in govde and "Satürn" not in govde

    def test_bildirim_sinyal_yoksa_none(self, monkeypatch):
        """None dönüşü çağıranı paylaşımlı burç satırına düşürür."""
        from services import notification_service
        monkeypatch.setattr(signal_service, "cached_signals",
                            lambda profile, today=None: None)
        assert notification_service.signal_push(PROFIL, "tr") is None

    def test_bildirim_uzun_satiri_reddeder(self, monkeypatch):
        from services import notification_service, prompts
        ham = {"signals": [{"transit": "Saturn", "natal": "Moon",
                            "aspect": "square", "theme": "inner"}]}
        monkeypatch.setattr(signal_service, "cached_signals",
                            lambda profile, today=None: ham)
        monkeypatch.setattr(
            prompts, "localize_signals",
            lambda lang, data: {"signals": [{"headline": "u" * 200,
                                             "theme_local": "İç dünya"}]})
        assert notification_service.signal_push(PROFIL, "tr") is None

    def test_bildirim_hatada_dusmez(self, monkeypatch):
        """Sinyal hesabı düşerse bildirim düşmez; None ile yedeğe geçilir."""
        from services import notification_service
        monkeypatch.setattr(
            signal_service, "cached_signals",
            lambda profile, today=None: (_ for _ in ()).throw(RuntimeError))
        assert notification_service.signal_push(PROFIL, "tr") is None
