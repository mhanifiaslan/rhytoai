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

        def sahte_generate(prompt, lang=None, **_):
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
            lambda prompt, lang=None, **_: (
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
                            lambda prompt, lang=None, **_: "Serbest bir paragraf.")

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

    def test_arkadas_anahtari_cift_bazli_ve_simetrik(self, monkeypatch):
        """Simetri garantisi P-turu'nda `friend_counterpart`'a TASINDI.

        `relationship_reading` artik hazir bir `pair_key` aliyor (cunku
        karsi taraf bir arkadas da olabilir, eklenen bir kisi de). Simetri
        hala bir gereklilik — iki arkadas ayni kaydi paylasmali — ama
        garantiyi veren yer degisti; test onu ORADA tutuyor.
        """
        from services import synastry_service
        import services.profile_service as ps

        monkeypatch.setattr(ps, "get_profile",
                            lambda uid: {"displayName": uid.upper(),
                                         "birthDate": "1990-01-01",
                                         "birthCity": "Ankara"})
        ab = synastry_service.friend_counterpart("a", "b")
        ba = synastry_service.friend_counterpart("b", "a")
        assert ab.key == ba.key, "anahtar siraya bagli"
        assert "a-b" in ab.key

    def test_kisi_anahtari_sahibe_ozel_ve_dogum_ozetli(self, monkeypatch):
        """Eklenen kisinin anahtari SAHIBE ozeldir ve dogum ozeti tasir:
        kullanici kisinin dogum saatini duzeltince eski eksenler
        kendiliginden duser (arkadas yolunda bu yapilamiyor)."""
        from services import people_service, synastry_service

        kayit = {"id": "p1", "relation": "child", "birthDate": "2015-06-01",
                 "birthCity": "Izmir"}
        monkeypatch.setattr(people_service, "get_person",
                            lambda uid, pid: dict(kayit))
        ilk = synastry_service.person_counterpart("ben", "p1", "tr")

        kayit["birthTime"] = "07:05"          # kullanici saati ekledi
        sonra = synastry_service.person_counterpart("ben", "p1", "tr")

        assert ilk.key.startswith("ben-pp1-")
        assert ilk.key != sonra.key, "dogum degisti, anahtar degismedi"

        monkeypatch.setattr(people_service, "get_person",
                            lambda uid, pid: None)
        assert synastry_service.person_counterpart("baskasi", "p1") is None


class TestOnbellekYolu:
    """Onbellekten gelen okuma da EKSEN CUMLELERINI tasimali.

    Cihaz bulgusu (1.6.2): "ilisikiyi incele"de kartlar bos geliyor, bazi
    arkadaslarda once dolu gelip sonra bos kaliyor. Sebep: onbellek
    isabetinde erken donus yapiliyor ve ayristirma atlaniyordu --
    ilk acilis uretim yolundan gectigi icin doluydu, IKINCI acilistan
    itibaren bos kaliyordu ve onbellek 30 gun oldugu icin o cift kalici
    olarak bos kaliyordu.
    """

    BICIMLI = ("communication: Merkur temasi konusmayi kolaylastiriyor.\n"
               "emotional: Ay-Saturn zemini olgun.\n"
               "attraction: Mars kivilcimli.\n"
               "bond: Jupiter tasiyici.\n"
               "theme: Ana tema. Ikinci cumle.")

    def _bellek(self, monkeypatch, uretim):
        from services import report_service as rs
        kutu: dict = {}
        monkeypatch.setattr(rs.cache, "get", lambda k: kutu.get(k))
        monkeypatch.setattr(
            rs.cache, "set",
            lambda k, v, **kw: kutu.__setitem__(k, v))
        monkeypatch.setattr(rs.gemini_service, "generate",
                            lambda p, lang=None, **_: uretim)
        return rs, kutu

    def test_ikinci_acilis_da_eksen_cumlesi_tasir(self, monkeypatch):
        rs, _ = self._bellek(monkeypatch, self.BICIMLI)
        eks = {"calc_version": "2", "axes": []}

        birinci = rs.relationship_reading("a", "b", "Ben", "F", eks,
                                          lang="tr")
        ikinci = rs.relationship_reading("a", "b", "Ben", "F", eks,
                                         lang="tr")

        assert ikinci["cached"] is True, "ikinci istek uretim yapmamali"
        assert len(birinci["axis_lines"]) == 4
        assert ikinci["axis_lines"] == birinci["axis_lines"], (
            "onbellekten gelen yanit eksen cumlelerini kaybetti — "
            "kartlar bos kalir")
        assert ikinci["theme"] == birinci["theme"]

    def test_bicimsiz_uretim_30_GUN_kilitlenmez(self, monkeypatch):
        """Model anahtarlari atlarsa kartlar bos kalir; bunu bir ay
        saklamak tek bir kotu uretimi kalicilastirirdi."""
        rs, kutu = self._bellek(monkeypatch, "Serbest bir paragraf.")
        omurler: list[int] = []
        gercek_set = rs.cache.set
        monkeypatch.setattr(
            rs.cache, "set",
            lambda k, v, **kw: (omurler.append(kw.get("ttl_seconds", 0)),
                                gercek_set(k, v, **kw))[1])

        sonuc = rs.relationship_reading("a", "b", "Ben", "F",
                                        {"calc_version": "2", "axes": []},
                                        lang="tr")
        assert sonuc["axis_lines"] == {}
        assert min(omurler) <= 3600, f"kisa omur verilmedi: {omurler}"


class TestSaatsizDisiplin:
    """Saatsiz tarafin Yukselen/MC temaslari sinastriden de duser.

    Natal ekranda Yukselen hic gosterilmezken ayni kisinin iliski
    eksenlerinde "Yukselen'ine kavusum" bir DAYANAK olarak gorunebiliyordu;
    ustelik `_KISISEL` Yukselen'i kisisel nokta saydigi icin eksen puanini
    da yukari cekiyordu. Olculdu: uydurma Yukselen "ortak zemin" eksenini
    bir seviye sisiriyor.
    """

    A_SAATLI = dict(name="A", year=1990, month=5, day=12, hour=14,
                    minute=30, city="Istanbul", nation="TR")
    B = dict(name="B", year=1985, month=11, day=3, hour=8, minute=15,
             city="Ankara", nation="TR")

    @property
    def a_saatsiz(self):
        return {**self.A_SAATLI, "hour": 12, "minute": 0,
                "hour_known": False}

    def test_saatsiz_tarafin_eksen_acilari_duser(self):
        ham = astro_service.get_synastry(self.a_saatsiz, self.B)
        a_ekseni = [x for x in ham["aspects"]
                    if x["p1"] in ("Ascendant", "Medium_Coeli")]
        assert a_ekseni == [], "ogle Yukselen'i sinastride durdu"

    def test_saati_bilinen_tarafin_acilari_KORUNUR(self):
        """Disiplin yalniz saatsiz tarafa uygulanir."""
        ham = astro_service.get_synastry(self.a_saatsiz, self.B)
        b_ekseni = [x for x in ham["aspects"]
                    if x["p2"] in ("Ascendant", "Medium_Coeli")]
        assert b_ekseni, "saati bilinen tarafin acilari da dustu"

    def test_beyan_uretilir_ve_dile_cevrilir(self):
        ham = astro_service.get_synastry(self.a_saatsiz, self.B)
        assert "synastry_hour_unknown_p1" in ham["disclosures"]
        eksenler = synastry_service.relationship_axes(ham)
        for dil in ("tr", "en"):
            yerel = prompts.localize_relationship_axes(dil, eksenler)
            metin = " ".join(yerel.get("disclosure_texts") or [])
            assert metin, dil
            assert "{" not in metin, dil

    def test_eksen_dayanaklarinda_yukselen_YOK(self):
        eksenler = synastry_service.relationship_axes(
            astro_service.get_synastry(self.a_saatsiz, self.B))
        kanit = [b for e in eksenler["axes"] for b in e["basis"]]
        assert not [k for k in kanit
                    if "Ascendant" in (k["p1"], k["p2"])]


class TestSaatsizAy:
    """Ay gunde ~13 derece yol alir: saat bilinmiyorsa burc sasabilir.

    Olculdu (16 tarih, 1993): 7'sinde Ay gun icinde burc degistiriyor.
    Yukselen hic uretilmiyordu ama Ay ogle dolgusuyla "senin Ay'in" diye
    gosteriliyordu. Karar: goster ama BEYAN ET.
    """

    def _ay(self, **kw):
        c = astro_service.get_natal_chart(
            "t", 1993, 4, 3, 12, 0, "Istanbul", **kw)
        return next(p for p in c["points"] if p["name"] == "Moon")

    def test_saatsizde_belirsiz_isaretlenir(self):
        assert self._ay(hour_known=False)["uncertain"] is True

    def test_saat_biliniyorsa_bayrak_YOK(self):
        ay = self._ay()
        assert not ay.get("uncertain")
        assert not ay.get("sign_alt")

    def test_sinirdaysa_ikinci_aday_yazilir(self):
        """1993-04-03: gun basi Aslan, gun sonu Basak."""
        ay = self._ay(hour_known=False)
        assert ay.get("sign_alt"), "sinir tarihinde ikinci aday yok"
        assert ay["sign_alt"] != ay["sign"]

    def test_sinirda_degilse_ikinci_aday_UYDURULMAZ(self):
        c = astro_service.get_natal_chart(
            "t", 1993, 1, 19, 12, 0, "Istanbul", hour_known=False)
        ay = next(p for p in c["points"] if p["name"] == "Moon")
        assert ay["uncertain"] is True
        assert ay.get("sign_alt") is None
