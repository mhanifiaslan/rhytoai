r"""Jeneriklik bekcileri: "tum arkadaslarla ayni cevaplar" bir daha olmasin.

Cihaz bulgusu (1.5.2): kullanici her arkadasinda ayni ilisski metnini
goruyordu. Uc ayri kusur olculdu ve ucu de burada kilitleniyor:

1. Acilar ONEME gore degil LISTE SIRASINA gore kesiliyordu. kerykeion
   87-122 aci buluyor, prompta 30'u gidiyordu; Yukselen temaslari 15
   acidan 1'ine dusuyordu. Kalan 30 aci her ciftte ayni gezegen
   gruplarindan geldigi icin ciftler birbirine benziyordu.
2. Esikler bes ciftle elle konmustu: 28 ciftte iletisim %78 "hafif"
   (hic "guclu" yok), cekim %53 "guclu". Her iliskide ayni tablo.
3. Gorunen metin 16 cumlelik HAZIR TABLODAN geliyordu (eksen x ton);
   seviye cumleye hic girmiyordu. 15 ciftin 15'i farkli olcum uretiyor
   ama yalniz 12'si farkli metin goruyordu.

Calistirma:  .venv\Scripts\python.exe -m pytest tests/test_relationship_quality.py -q
"""
from __future__ import annotations

import collections
import itertools

from services import astro_service, prompts, synastry_service

#: Kucuk ama cesitli havuz: farkli yil/mevsim/saat/sehir. Buyutmek testi
#: dakikalara cikarir; asil kalibrasyon `scripts/calibrate_synastry.py`.
KISILER = [
    dict(name="A", year=1990, month=5, day=12, hour=14, minute=30,
         city="Istanbul", nation="TR"),
    dict(name="B", year=1985, month=11, day=3, hour=8, minute=15,
         city="Ankara", nation="TR"),
    dict(name="C", year=1996, month=2, day=27, hour=21, minute=45,
         city="Izmir", nation="TR"),
    dict(name="D", year=1978, month=7, day=19, hour=3, minute=5,
         city="Bursa", nation="TR"),
    dict(name="E", year=2001, month=9, day=8, hour=17, minute=20,
         city="Adana", nation="TR"),
]


def _eksenler():
    """Tum ciftlerin eksen sonuclari (10 cift)."""
    return [synastry_service.relationship_axes(
                astro_service.get_synastry(a, b))
            for a, b in itertools.combinations(KISILER, 2)]


class TestAciSiralamasi:
    """Kesme ONEMDEN sonra yapilir — bu turun kok nedeni."""

    def test_en_onemli_aci_basa_gelir(self):
        acilar = [
            {"p1": "Jupiter", "p2": "Neptune", "aspect": "trine",
             "orbit": 0.1},                      # dar ama kisisel degil
            {"p1": "Venus", "p2": "Mars", "aspect": "conjunction",
             "orbit": 0.3},                      # dar VE iki uc kisisel
            {"p1": "Sun", "p2": "Saturn", "aspect": "opposition",
             "orbit": 6.9},                      # kisisel ama cok genis
        ]
        sirali = astro_service.rank_aspects(acilar)
        assert (sirali[0]["p1"], sirali[0]["p2"]) == ("Venus", "Mars")
        # Genis orb en sona duser: eskiden listede ilk sirada olabiliyordu
        # ve prompta o gidiyordu.
        assert (sirali[-1]["p1"], sirali[-1]["p2"]) == ("Sun", "Saturn")

    def test_siralama_kararli(self):
        """Ayni girdi her kosuda ayni listeyi vermeli; aksi halde onbellek
        ve altin vektorler oynar."""
        acilar = [
            {"p1": "Sun", "p2": "Moon", "aspect": "trine", "orbit": 1.0},
            {"p1": "Mars", "p2": "Venus", "aspect": "trine", "orbit": 1.0},
        ]
        assert (astro_service.rank_aspects(acilar)
                == astro_service.rank_aspects(list(reversed(acilar))))

    def test_guney_dugum_aynasi_elenir(self):
        """Kuzey ve Guney dugumu 180 derece zit: 'Merkur-Kuzey kavusum' ile
        'Merkur-Guney karsit' TEK olcumdur. Ikisini birden vermek modele
        ayni kaniti iki kez gostermekti."""
        acilar = [
            {"p1": "Mercury", "p2": "True_North_Lunar_Node",
             "aspect": "conjunction", "orbit": 0.47},
            {"p1": "Mercury", "p2": "True_South_Lunar_Node",
             "aspect": "opposition", "orbit": 0.47},
        ]
        sirali = astro_service.rank_aspects(acilar)
        assert len(sirali) == 1
        assert sirali[0]["p2"] == "True_North_Lunar_Node"

    def test_gercek_sinastri_sirali_ve_yukselen_tasiyor(self):
        ham = astro_service.get_synastry(KISILER[0], KISILER[1])
        acilar = ham["aspects"]
        onemler = [astro_service.aspect_significance(a) for a in acilar]
        assert onemler == sorted(onemler, reverse=True), "liste sirali degil"
        # Yukselen temaslari eskiden 15'te 1'e dusuyordu.
        asc = [a for a in acilar
               if "Ascendant" in (a["p1"], a["p2"])]
        assert len(asc) >= 3, f"Yukselen temasi yine kesiliyor: {len(asc)}"


class TestKalibrasyon:
    """Esikler dagilimdan geliyor; seviyeler ciftler arasinda DEGISMELI."""

    def test_seviyeler_tek_degerde_kilitlenmiyor(self):
        sonuclar = _eksenler()
        dagilim: dict[str, collections.Counter] = {
            e: collections.Counter() for e in synastry_service.AXES}
        for s in sonuclar:
            for e in s["axes"]:
                dagilim[e["axis"]][e["level"]] += 1

        for eksen, c in dagilim.items():
            assert len(c) >= 2, (
                f"{eksen} her ciftte ayni seviye: {dict(c)} — esikler "
                "kalibrasyonunu yitirmis (scripts/calibrate_synastry.py)")

    def test_esikler_eksen_basina_ayri(self):
        """Ortak esik 'her iliskide cekim guclu' gibi sahte tablo uretir:
        cekimin medyani iletisimin maksimumunun ustunde."""
        degerler = set(synastry_service._ESIKLER.values())
        assert len(degerler) == len(synastry_service.AXES)


class TestAyirtEdicilik:
    """Bu turun ASIL bekcisi: iki cift ayni seyi gormemeli."""

    def test_her_cift_farkli_olcum_uretir(self):
        imzalar = [
            tuple((e["level"], e["tone"]) for e in s["axes"])
            for s in _eksenler()
        ]
        assert len(set(imzalar)) == len(imzalar), (
            "iki cift ayni olcum imzasini uretti")

    def test_iki_cift_AYNI_yaniti_gormez(self):
        """Sunucunun DONDURDUGU yuk cift basina benzersiz olmali.

        Eski hazir cumle tablosunda 15 ciftin 3'u dort cumlenin dordunu
        de birebir ayni okuyordu; olcum ayirt ediyor, anlatim
        etmiyordu. Artik yukte gorunen sey olcumun kendisi (seviye, ton,
        dayanak aci) — yorumu AI yaziyor ve o da bu yukten besleniyor.
        """
        yukler = []
        for s in _eksenler():
            yerel = prompts.localize_relationship_axes("tr", s)
            yukler.append(repr([
                (e["axis_local"], e["level_local"], e["tone_local"],
                 [(b["p1_local"], b["aspect_local"], b["p2_local"])
                  for b in e["basis"]])
                for e in yerel["axes"]
            ]))
        tekrar = [n for n in collections.Counter(yukler).values() if n > 1]
        assert not tekrar, f"{len(tekrar)} cift grubu ayni yaniti goruyor"

    def test_dayanak_aciler_cifte_ozgu(self):
        """Kanit listesi ciftten cifte degismeli: AI yorumu bundan
        besleniyor, sabitse yorum da sabitlesir."""
        kanitlar = set()
        for s in _eksenler():
            for e in s["axes"]:
                for b in e["basis"]:
                    kanitlar.add((b["p1"], b["aspect"], b["p2"]))
        assert len(kanitlar) >= 15, (
            f"dayanak cesitliligi cok dusuk: {len(kanitlar)}")


class TestIliskiOkumasiPromptu:
    """Okuma OLCUMDEN uretilir; ham dogum verisi prompta GIRMEZ."""

    def test_prompt_olcumu_tasir_dogum_verisini_TASIMAZ(self, monkeypatch):
        from services import report_service

        yakalanan = {}

        def sahte_generate(prompt, lang=None):
            yakalanan["prompt"] = prompt
            return "okuma"

        monkeypatch.setattr(report_service.gemini_service, "generate",
                            sahte_generate)
        monkeypatch.setattr(report_service.cache, "get", lambda k: None)
        monkeypatch.setattr(report_service.cache, "set",
                            lambda k, v, **kw: None)

        eksenler = synastry_service.relationship_axes(
            astro_service.get_synastry(KISILER[0], KISILER[1]))
        report_service.relationship_reading(
            "uid-a", "uid-b", "Ben", "Erkan", eksenler, lang="tr")

        p = yakalanan["prompt"]
        assert "Erkan" in p
        assert "orb" in p, "dayanak acilar prompta girmiyor"
        assert "İletişim" in p, "eksen adlari prompta girmiyor"
        # Ham dogum verisi hicbir katmanda tasinmaz (dyad kurali).
        for sizinti in ("1985", "1990", "Ankara", "Istanbul"):
            assert sizinti not in p, f"dogum verisi sizdi: {sizinti}"

    def test_her_eksen_KENDI_cumlesini_alir(self, monkeypatch):
        """Kart bos kalmamali.

        Ilk surumde okuma TEK BLOK donuyordu; eksen kartlarinda hicbir
        cumle kalmadi ve kullanici dort bos baslik + dort "Rytho'ya sor"
        gordu ("neyi soracak!"). Kartin isi meraki acmak.
        """
        from services import report_service

        monkeypatch.setattr(report_service.cache, "get", lambda k: None)
        monkeypatch.setattr(report_service.cache, "set",
                            lambda k, v, **kw: None)
        monkeypatch.setattr(
            report_service.gemini_service, "generate",
            lambda prompt, lang=None: (
                "communication: Merkur gerilimi konusmayi keskinlestiriyor.\n"
                "emotional: Ay-Jupiter temasi duyguyu comert kiliyor.\n"
                "attraction: Mars-Uranus kivilcimi ani ve dalgali.\n"
                "bond: Saturn zemini yavas ama tasiyici.\n"
                "theme: Zihinsel surtusme ile duygusal comertlik arasinda "
                "bir denge. Kucuk adimlar bu zemini tasir."))

        sonuc = report_service.relationship_reading(
            "a", "b", "Ben", "Erkan", {"calc_version": "2", "axes": []},
            lang="tr")

        assert set(sonuc["axis_lines"]) == {
            "communication", "emotional", "attraction", "bond"}
        assert all(v for v in sonuc["axis_lines"].values())
        assert "denge" in sonuc["theme"]
        assert "theme:" not in sonuc["axis_lines"]["bond"]

    def test_bicim_tutmazsa_UYDURMA_yapilmaz(self, monkeypatch):
        """Model biçimi kacirirsa eksen cumlesi URETILMEZ; caginan katman
        tam metni tek blok gosterir. Yanlis cumle gostermektense eksik
        kalmak yeglenir."""
        from services import report_service

        monkeypatch.setattr(report_service.cache, "get", lambda k: None)
        monkeypatch.setattr(report_service.cache, "set",
                            lambda k, v, **kw: None)
        monkeypatch.setattr(report_service.gemini_service, "generate",
                            lambda prompt, lang=None: "Serbest bir paragraf.")

        sonuc = report_service.relationship_reading(
            "a", "b", "Ben", "Erkan", {"calc_version": "2", "axes": []},
            lang="tr")
        assert sonuc["axis_lines"] == {}
        assert sonuc["text"] == "Serbest bir paragraf."

    def test_ayristirici_suslemeye_dayanikli(self):
        """Model bazen `**communication**:` ya da `- communication:` yazar."""
        from services import report_service

        cozum = report_service.parse_relationship_reading(
            "- **communication**: Ilk cumle\n"
            "  ikinci satira tasti.\n"
            "* emotional: Ikinci eksen\n"
            "theme: Ana tema.")
        assert cozum["axis_lines"]["communication"] == (
            "Ilk cumle ikinci satira tasti.")
        assert cozum["axis_lines"]["emotional"] == "Ikinci eksen"
        assert cozum["theme"] == "Ana tema."

    def test_onbellek_anahtari_cift_bazli_ve_simetrik(self, monkeypatch):
        from services import report_service

        anahtarlar = []
        monkeypatch.setattr(report_service.cache, "get",
                            lambda k: anahtarlar.append(k))
        monkeypatch.setattr(report_service.gemini_service, "generate",
                            lambda prompt, lang=None: "x")
        monkeypatch.setattr(report_service.cache, "set",
                            lambda k, v, **kw: None)

        eksenler = {"calc_version": "2", "axes": []}
        report_service.relationship_reading("a", "b", "A", "B", eksenler,
                                            lang="tr")
        report_service.relationship_reading("b", "a", "B", "A", eksenler,
                                            lang="tr")
        assert anahtarlar[0] == anahtarlar[1], "anahtar sıraya bagli"
        assert "a-b" in anahtarlar[0]
