"""Çift-transit ölçümü bekçileri (GT-turu).

Korunan değişmezler:

1. İlişki katmanının TEK tarih-farkındalı ölçümü bu: gün-anahtarlı
   önbellek, aynı gün tek hesap, ertesi gün taze.
2. Süzgeç doktrini `chart_context.filter_transit_hits`ten gelir — Ay'sız
   gezenler, majör açı, orb ≤ 3.0, yavaş-önce (iki kopya iki doktrine
   ayrışırdı).
3. Fısıltı/uç/dyad üçü de aynı ölçümü kullanır; kişi yolunda yan etiketi
   İLİŞKİ etiketidir — gerçek ad sunucuda YOK.

Çalıştırma:  .venv\\Scripts\\python.exe -m pytest tests/test_pair_transits.py -q
"""
from __future__ import annotations

import datetime as dt

import pytest

from services import chart_context, prompts, synastry_service


KARSI = synastry_service.Counterpart(
    key="u1-p9-abc", label="eşin", sun_sign="Balık", relation="partner",
    birth={"name": "e", "year": 1992, "month": 3, "day": 4, "hour": 10,
           "minute": 15, "city": "Izmir", "nation": "TR",
           "hour_known": True})

ME = {"birthDate": "1987-02-05", "birthTime": "06:00",
      "birthCity": "Siverek", "birthNation": "TR"}


@pytest.fixture
def bellek(monkeypatch):
    import core.cache as cache_mod
    depo: dict = {}
    monkeypatch.setattr(cache_mod, "get", depo.get)
    monkeypatch.setattr(
        cache_mod, "set",
        lambda k, v, ttl_seconds=0, owner_uid=None: depo.update({k: v}))
    return depo


@pytest.fixture
def sahte_ortam(monkeypatch, bellek):
    """Profil + eksenler + transit motoru sahtelenir; sayaç dönülür."""
    from services import astro_service, profile_service

    monkeypatch.setattr(profile_service, "get_profile", lambda uid: dict(ME))
    monkeypatch.setattr(chart_context, "has_birth_data", lambda p: True)
    monkeypatch.setattr(profile_service, "birth_kwargs", lambda p: {
        "name": "t", "year": 1987, "month": 2, "day": 5, "hour": 6,
        "minute": 0, "city": "Siverek", "nation": "TR", "hour_known": True})
    # Eksen dayanağında Neptün (kullanıcı tarafı p1) — kişisel kümede yok,
    # basis birleşimiyle İLGİLİ sayılmalı.
    monkeypatch.setattr(synastry_service, "axes_for", lambda uid, other: {
        "axes": [{"axis": "bond", "basis": [
            {"p1": "Neptune", "p2": "Jupiter", "aspect": "trine",
             "orb": 1.0, "supportive": True}]}]})

    sayac = {"n": 0}

    def sahte_transit(**kw):
        sayac["n"] += 1
        return {"aspects_to_natal": [
            # GİRMELİ: yavaş gezen, kişisel nokta, dar orb.
            {"p1": "Saturn", "p2": "Venus", "aspect": "square",
             "orbit": 0.8, "movement": "applying"},
            # GİRMELİ: basis birleşimi sayesinde Neptün natal noktası.
            {"p1": "Jupiter", "p2": "Neptune", "aspect": "trine",
             "orbit": 1.2, "movement": "separating"},
            # DÜŞMELİ: gezen Ay (doktrin).
            {"p1": "Moon", "p2": "Sun", "aspect": "conjunction",
             "orbit": 0.1, "movement": "applying"},
            # DÜŞMELİ: minör açı.
            {"p1": "Saturn", "p2": "Sun", "aspect": "quintile",
             "orbit": 0.2, "movement": "applying"},
            # DÜŞMELİ: geniş orb.
            {"p1": "Pluto", "p2": "Moon", "aspect": "square",
             "orbit": 3.5, "movement": "applying"},
            # DÜŞMELİ: alakasız natal nokta (kümede yok).
            {"p1": "Saturn", "p2": "Lilith", "aspect": "square",
             "orbit": 0.3, "movement": "applying"},
            # Hızlı gezen — yavaşlardan SONRA sıralanmalı.
            {"p1": "Mercury", "p2": "Moon", "aspect": "sextile",
             "orbit": 0.1, "movement": "applying"},
        ]}

    monkeypatch.setattr(astro_service, "get_transits", sahte_transit)
    return sayac


class TestOlcum:
    def test_suzgec_ve_siralama(self, sahte_ortam):
        sonuc = synastry_service.pair_transits("u1", KARSI)
        vuruslar = sonuc["hits"]
        gezenler = [(v["side"], v["transit"], v["natal"]) for v in vuruslar]
        # Ay/minör/geniş-orb/alakasız yok; iki taraf da temsil ediliyor.
        assert all(v["transit"] != "Moon" for v in vuruslar)
        assert ("user", "Saturn", "Venus") in gezenler
        assert ("user", "Jupiter", "Neptune") in gezenler  # basis birleşimi
        assert len(vuruslar) <= synastry_service.PAIR_TRANSIT_CAP
        # Yavaş-önce: Merkür (varsa) en sonda.
        yavaslar = [chart_context.is_slow_mover(v["transit"])
                    for v in vuruslar]
        assert yavaslar == sorted(yavaslar, reverse=True)
        # movement taşınır — "güçleniyor/sönüyor" dili buradan.
        assert vuruslar[0]["movement"] in ("applying", "separating")

    def test_taraf_basina_ust_sinir(self, sahte_ortam):
        sonuc = synastry_service.pair_transits("u1", KARSI)
        from collections import Counter
        taraf = Counter(v["side"] for v in sonuc["hits"])
        assert all(n <= synastry_service.PAIR_TRANSIT_PER_SIDE
                   for n in taraf.values())

    def test_gun_anahtarli_onbellek(self, sahte_ortam, bellek):
        gun = dt.date(2099, 1, 1)
        synastry_service.pair_transits("u1", KARSI, today=gun)
        synastry_service.pair_transits("u1", KARSI, today=gun)
        # Aynı gün: iki taraf için toplam 2 motor koşusu, tekrar YOK.
        assert sahte_ortam["n"] == 2
        anahtarlar = [k for k in bellek if k.startswith("pair-transits-")]
        assert anahtarlar == [
            f"pair-transits-{synastry_service.SYNASTRY_CALC_VERSION}"
            f"-{KARSI.key}-2099-01-01"]
        # Ertesi gün: yeniden hesap.
        synastry_service.pair_transits("u1", KARSI,
                                       today=dt.date(2099, 1, 2))
        assert sahte_ortam["n"] == 4

    def test_dogum_verisi_yoksa_none(self, monkeypatch, bellek):
        from services import profile_service
        monkeypatch.setattr(profile_service, "get_profile", lambda uid: None)
        assert synastry_service.pair_transits("u1", KARSI) is None

    def test_taraf_hatasi_digerini_dusurmez(self, sahte_ortam, monkeypatch):
        from services import astro_service
        asil = astro_service.get_transits
        durum = {"ilk": True}

        def yarim(**kw):
            if durum["ilk"]:
                durum["ilk"] = False
                raise RuntimeError("efemeris")
            return asil(**kw)

        monkeypatch.setattr(astro_service, "get_transits", yarim)
        sonuc = synastry_service.pair_transits("u1", KARSI)
        assert sonuc is not None
        assert all(v["side"] == "other" for v in sonuc["hits"])


class TestSatirlar:
    HITS = [{"side": "user", "transit": "Saturn", "natal": "Venus",
             "aspect": "square", "orb": 0.8, "movement": "applying"},
            {"side": "other", "transit": "Jupiter", "natal": "Moon",
             "aspect": "trine", "orb": 1.2, "movement": None}]

    def test_tr_satirlar_yan_etiketli(self):
        satirlar = synastry_service.pair_transit_lines(self.HITS, "eşin",
                                                       "tr")
        assert satirlar[0].startswith("sende: Satürn → Venüs Kare")
        assert "yaklaşıyor" in satirlar[0]
        assert satirlar[1].startswith("eşin tarafında: Jüpiter")
        assert "(1.2°)" in satirlar[1]  # movement yoksa parantez sade

    def test_localize_gercek_ad_tasimaz(self):
        """Kişi yolunda yan etiket İLİŞKİ etiketidir; sunucu zaten adı
        bilmez — bu test yapıyı kilitler."""
        y = prompts.localize_pair_transits(
            "tr", {"date": "2099-01-01", "hits": self.HITS}, "eşin")
        assert y["hits"][0]["side_label"] == "sende"
        assert y["hits"][1]["side_label"] == "eşin tarafında"
        assert y["hits"][1]["supportive"] is True
        assert y["hits"][0]["supportive"] is False
        assert "Satürn" in y["hits"][0]["text"]

    def test_whisper_bugunu_tasir(self, sahte_ortam):
        metin = synastry_service.whisper_for("u1", KARSI, "tr")
        p = prompts.get("tr")
        assert p.PAIR_TODAY_LABEL in metin
        assert "Satürn" in metin
        assert len(metin) <= 900

    def test_whisper_olcum_dusse_de_yasar(self, sahte_ortam, monkeypatch):
        monkeypatch.setattr(
            synastry_service, "pair_transits",
            lambda uid, other, today=None: (_ for _ in ()).throw(
                RuntimeError))
        metin = synastry_service.whisper_for("u1", KARSI, "tr")
        assert "İletişim" in metin or "Ortak zemin" in metin or metin
        assert prompts.get("tr").PAIR_TODAY_LABEL not in metin


class TestDyadVeUc:
    def test_dyad_sablonu_iki_dilde_slotu_tanir(self):
        for lang in ("tr", "en"):
            p = prompts.get(lang)
            p.DYAD.format(name_a="A", name_b="B", today="2099-01-01",
                          moon_name="x", moon_emoji="e", illumination=50,
                          retros="-", aspects="-", axes="-", rag="-",
                          pair_transits="- sende: test")

    def test_dyad_promptu_cift_satirlarini_tasir(self, monkeypatch):
        from services import report_service
        yakalanan = {}

        def sahte(cache_key, prompt, fallback, **kw):
            yakalanan["prompt"] = prompt
            return {"text": "ok"}

        monkeypatch.setattr(report_service, "_cached_generate", sahte)
        monkeypatch.setattr(report_service, "retrieve_context",
                            lambda *a, **k: "-")
        import core.cache as cache_mod
        monkeypatch.setattr(cache_mod, "get", lambda k: None)
        report_service.dyad_reading(
            "u1", "cift", "A", "B",
            {"aspects": [], "person1": {}, "person2": {}},
            {"moon_phase": {}, "retrogrades": []}, lang="tr",
            today=dt.date(2099, 1, 1),
            pair_transits="- sende: Satürn → Venüs Kare (0.8°)")
        assert "sende: Satürn → Venüs Kare" in yakalanan["prompt"]

    def test_uc_ucretsiz_kullaniciya_today_doner(self, monkeypatch,
                                                 sahte_ortam):
        pytest.importorskip("fastapi")
        try:
            from main import app
        except Exception as exc:  # pragma: no cover
            pytest.skip(f"uygulama içe aktarılamadı: {exc}")
        from fastapi.testclient import TestClient
        from api import reports
        from core import entitlements
        from services import profile_service

        monkeypatch.setattr(entitlements, "FORCE_PLUS", False)
        monkeypatch.setattr(reports.entitlements, "is_subscriber",
                            lambda uid: False)
        monkeypatch.setattr(reports.entitlements, "user_local_date",
                            lambda uid: dt.date(2099, 1, 1))
        monkeypatch.setattr(profile_service, "are_friends",
                            lambda a, b: True)
        arkadas = synastry_service.Counterpart(
            key="u1-f1", label="Erkan", sun_sign="Boğa", relation=None,
            birth=KARSI.birth)
        monkeypatch.setattr(synastry_service, "friend_counterpart",
                            lambda uid, fuid: arkadas)
        with TestClient(app) as client:
            yanit = client.post(
                "/api/v1/reports/relationship",
                json={"friend_uid": "f1"},
                headers={"Authorization": "Bearer test-gt"})
        assert yanit.status_code == 200, yanit.text
        veri = yanit.json()["data"]
        assert veri.get("reading_locked") is True
        assert veri.get("today", {}).get("hits"), "ücretsiz katman ölçümü görmeli"
