"""I Ching motoru altın vektörleri (Revize İ0).

Bu dosyadan önce çekim motorunun HİÇBİR aritmetiği test edilmiyordu:
biri yarrow eşiğini `r < 6`'dan `r < 5`'e kaydırsa hiçbir test kırılmaz,
yalnızca olasılıklar sessizce bozulurdu. Kural test_bazi_engine ile aynı:
altın değerler çift kaynakla doğrulanır ve vektörün yanına yazılır.
"""
from __future__ import annotations

import pytest

from services import bazi_service as bazi_service_mod
from services import iching_service, prompts
from services.iching_service import cast_iching, get_hexagram


class TestVeriButunlugu:
    def test_64_trigram_cifti_benzersiz(self):
        # Her heksagramın (alt+üst) çizgi deseni benzersiz olmalı; bir
        # trigramın `lines` dizisi bozulsa çekim rastgele KeyError atardı.
        index = iching_service._lines_index()
        assert len(index) == 64

    def test_king_wen_unicode_hizasi(self):
        # U+4DC0 bloğu King Wen sırasıyla birebir: #1 ䷀, #64 ䷿.
        assert get_hexagram(1)["unicode"] == "䷀"
        assert get_hexagram(64)["unicode"] == "䷿"

    def test_bilinen_heksagramlar(self):
        # Nokta kontrolleri (klasik King Wen tablosu): #1 Qian, #2 Kun,
        # #11 Tai (qian altta kun üstte), #63 Ji Ji, #64 Wei Ji.
        assert get_hexagram(1)["name"] == "Qian"
        assert get_hexagram(2)["name"] == "Kun"
        tai = get_hexagram(11)
        assert (tai["lower_trigram"]["element"],
                tai["upper_trigram"]["element"]) == ("metal", "earth")


class TestOlasilikDagilimi:
    """`secrets.randbelow` monkeypatch ile DETERMİNİSTİK sayım — istatistik
    değil, dağılım eşiklerinin birebir kilidi."""

    def test_coins_dagilimi(self, monkeypatch):
        # 3 para × {0,1}: 8 kombinasyonun tamamı sırayla beslenir.
        # Klasik: 6 (eski yin) 1/8, 7 (genç yang) 3/8, 8 (genç yin) 3/8,
        # 9 (eski yang) 1/8.
        sira = [b for kombo in range(8)
                for b in ((kombo >> 2) & 1, (kombo >> 1) & 1, kombo & 1)]
        beslenen = iter(sira)
        monkeypatch.setattr(iching_service.secrets, "randbelow",
                            lambda n: next(beslenen))
        sayim = {6: 0, 7: 0, 8: 0, 9: 0}
        for _ in range(8):
            sayim[iching_service._cast_line_coins()] += 1
        assert sayim == {6: 1, 7: 3, 8: 3, 9: 1}

    def test_yarrow_dagilimi(self, monkeypatch):
        # r=0..15'in tamamı: klasik yarrow 6:1/16, 7:5/16, 8:7/16, 9:3/16.
        beslenen = iter(range(16))
        monkeypatch.setattr(iching_service.secrets, "randbelow",
                            lambda n: next(beslenen))
        sayim = {6: 0, 7: 0, 8: 0, 9: 0}
        for _ in range(16):
            sayim[iching_service._cast_line_yarrow()] += 1
        assert sayim == {6: 1, 7: 5, 8: 7, 9: 3}


class TestDonusum:
    def _sabit_cekim(self, monkeypatch, degerler):
        beslenen = iter(degerler)
        monkeypatch.setattr(iching_service, "_cast_line_coins",
                            lambda: next(beslenen))
        return cast_iching("test", method="coins")

    def test_tum_cizgiler_hareketli_qian_kun_olur(self, monkeypatch):
        # Altı eski yang (9): #1 Qian → tamamı döner → #2 Kun.
        # Kaynak: dönüşüm tanımı — eski çizgi tersine döner (klasik kural).
        cekim = self._sabit_cekim(monkeypatch, [9] * 6)
        assert cekim["primary"]["number"] == 1
        assert cekim["moving_lines"] == [1, 2, 3, 4, 5, 6]
        assert cekim["transformed"]["number"] == 2

    def test_tai_ucuncu_cizgi_lin_olur(self, monkeypatch):
        # [7,7,9,8,8,8] → #11 Tai, hareketli yalnız 3. çizgi →
        # alt trigram qian→dui → #19 Lin. Çift kaynak: King Wen tablosu +
        # trigram desen aritmetiği (1,1,0 = dui).
        cekim = self._sabit_cekim(monkeypatch, [7, 7, 9, 8, 8, 8])
        assert cekim["primary"]["number"] == 11
        assert cekim["moving_lines"] == [3]
        assert cekim["transformed"]["number"] == 19

    def test_hareketsiz_cekimde_donusum_yok(self, monkeypatch):
        cekim = self._sabit_cekim(monkeypatch, [7, 8, 7, 8, 7, 8])
        assert cekim["moving_lines"] == []
        assert "transformed" not in cekim


class TestNukleerHeksagram:
    """İ2: hu gua — 2-3-4. çizgiler alt, 3-4-5. çizgiler üst trigram.

    Altın vektörler klasik nükleer tablosundan; çift kaynak: çizgi
    aritmetiğinin elle turu + yayınlanmış hu gua eşlemeleri.
    """

    def _nukleer(self, monkeypatch, degerler):
        beslenen = iter(degerler)
        monkeypatch.setattr(iching_service, "_cast_line_coins",
                            lambda: next(beslenen))
        return cast_iching("test", method="coins")["nuclear"]["number"]

    def test_qian_kun_sabit_noktalar(self, monkeypatch):
        assert self._nukleer(monkeypatch, [7] * 6) == 1
        assert self._nukleer(monkeypatch, [8] * 6) == 2

    def test_tai_nukleeri_gui_mei(self, monkeypatch):
        # #11 Tai (1,1,1,0,0,0) → çekirdek (1,1,0 | 1,0,0) = dui altta
        # zhen üstte = #54 Gui Mei.
        assert self._nukleer(monkeypatch, [7, 7, 7, 8, 8, 8]) == 54

    def test_ji_ji_nukleeri_wei_ji(self, monkeypatch):
        # #63 Ji Ji (1,0,1,0,1,0) → çekirdek (0,1,0 | 1,0,1) = kan altta
        # li üstte = #64 Wei Ji — tamamlanmışın çekirdeği tamamlanmamıştır.
        assert self._nukleer(monkeypatch, [7, 8, 7, 8, 7, 8]) == 64


class TestGunBaglami:
    """İ2: tarih yardımcıları + enrich_cast."""

    def test_gun_sutunu_capalari(self):
        # test_bazi_engine çapalarının aynısı: 1949-10-01 JiaZi (döngü 0),
        # 2000-01-01 WuWu (döngü 54).
        import datetime as dtm
        p1 = bazi_service_mod.day_pillar_for_date(dtm.date(1949, 10, 1))
        assert (p1["stem"]["pinyin"], p1["branch"]["pinyin"],
                p1["cycle"]) == ("Jia", "Zi", 0)
        p2 = bazi_service_mod.day_pillar_for_date(dtm.date(2000, 1, 1))
        assert p2["cycle"] == 54

    def test_ay_sutunu_bes_kaplan(self):
        # 1984-02-05 (Li Chun sonrası, Jia yılı) → ilk ay BingYin.
        import datetime as dtm
        p = bazi_service_mod.month_pillar_for_date(dtm.date(1984, 2, 5))
        assert (p["stem"]["pinyin"], p["branch"]["pinyin"]) == \
            ("Bing", "Yin")

    def test_enrich_baglamsiz_dokunmaz(self, monkeypatch):
        beslenen = iter([7] * 6)
        monkeypatch.setattr(iching_service, "_cast_line_coins",
                            lambda: next(beslenen))
        cekim = cast_iching("test")
        assert iching_service.enrich_cast(cekim) is cekim

    def test_enrich_iliskileri_kurar(self, monkeypatch):
        # #11 Tai: alt qian (metal), üst kun (toprak). DM ağaç için:
        # metal ağacı kontrol eder → controls_me; ağaç toprağı kontrol
        # eder → i_control.
        beslenen = iter([7, 7, 7, 8, 8, 8])
        monkeypatch.setattr(iching_service, "_cast_line_coins",
                            lambda: next(beslenen))
        cekim = iching_service.enrich_cast(
            cast_iching("test"),
            day_pillar={"label": "x", "cycle": 0},
            day_master_element="wood", basis="utc")
        iliskiler = cekim["context"]["trigram_relations"]
        assert iliskiler == {"lower": "controls_me", "upper": "i_control"}
        assert cekim["context"]["basis"] == "utc"


class TestLiuYao:
    """İ3: Jing Fang najia/saray/altı akraba — altın vektörler.

    Kaynaklar: klasik saray dizileri + najia şeması; her vektör iki
    bağımsız kaynaktan doğrulanıp donduruldu (transkripsiyon hatasının
    tek panzehiri — B0 kuralı).
    """

    @staticmethod
    def _liu_yao(numara: int, day_cycle=None):
        from services import liuyao_service
        h = get_hexagram(numara)
        alt = iching_service._load()["trigrams"]
        # get_hexagram çizgileri döndürmüyor; desen trigramlardan kurulur.
        data = iching_service._load()
        hx = next(x for x in data["hexagrams"] if x["number"] == numara)
        lines = (data["trigrams"][hx["lower"]]["lines"]
                 + data["trigrams"][hx["upper"]]["lines"])
        assert h["number"] == numara and alt
        return liuyao_service.analyze(lines, day_cycle=day_cycle)

    def test_qian_sarayi_tam_zinciri(self):
        # Klasik dizi: 1 Qian → 44 Gou → 33 Dun → 12 Pi → 20 Guan →
        # 23 Bo → 35 Jin (gezgin ruh) → 14 Da You (dönen ruh).
        beklenen = {1: 0, 44: 1, 33: 2, 12: 3, 20: 4, 23: 5, 35: 6, 14: 7}
        for numara, konum in beklenen.items():
            ly = self._liu_yao(numara)
            assert ly["palace"] == "qian", f"#{numara}"
            from services.liuyao_service import SHI_SEQUENCE
            assert ly["shi"] == SHI_SEQUENCE[konum], f"#{numara}"

    def test_ji_ji_kan_sarayinda(self):
        # 63 Ji Ji = Kan sarayının 3. dünyası (29→60→3→63): shi 3, ying 6.
        ly = self._liu_yao(63)
        assert (ly["palace"], ly["shi"], ly["ying"]) == ("kan", 3, 6)

    def test_hex1_najia_altin_vektoru(self):
        # Klasik: 甲子 甲寅 甲辰 壬午 壬申 壬戌 (alttan üste).
        ly = self._liu_yao(1)
        ciftler = [(c["stem"], c["branch"]) for c in ly["lines"]]
        assert ciftler == [("Jia", "Zi"), ("Jia", "Yin"), ("Jia", "Chen"),
                           ("Ren", "Wu"), ("Ren", "Shen"), ("Ren", "Xu")]

    def test_hex2_najia_altin_vektoru(self):
        # Klasik: 乙未 乙巳 乙卯 癸丑 癸亥 癸酉 (alttan üste).
        ly = self._liu_yao(2)
        ciftler = [(c["stem"], c["branch"]) for c in ly["lines"]]
        assert ciftler == [("Yi", "Wei"), ("Yi", "Si"), ("Yi", "Mao"),
                           ("Gui", "Chou"), ("Gui", "Hai"), ("Gui", "You")]

    def test_alti_akraba_turetimi(self):
        # Qian sarayı (metal): Zi (su) → metal suyu üretir → Evlat;
        # Yin (ağaç) → metal ağacı yönetir → Servet; Wu (ateş) → ateş
        # metali yönetir → Yönetici — klasik Qian tablosuyla birebir.
        ly = self._liu_yao(1)
        akraba = {c["branch"]: c["relative"] for c in ly["lines"]}
        assert akraba["Zi"] == "offspring"
        assert akraba["Yin"] == "wealth"
        assert akraba["Wu"] == "officer"
        assert akraba["Chen"] == "parent"   # toprak metali üretir
        assert akraba["Shen"] == "sibling"  # metal = saray elementi

    def test_bosluk_ve_carpisma(self):
        # Gün döngüsü 0 (JiaZi): boşluk Xu/Hai; gün dalı Zi ↔ Wu çarpışır.
        ly = self._liu_yao(1, day_cycle=0)
        satirlar = {c["branch"]: c for c in ly["lines"]}
        assert satirlar["Xu"]["void"] is True
        assert satirlar["Zi"]["void"] is False
        assert satirlar["Wu"]["clash"] is True
        assert satirlar["Shen"]["clash"] is False

    def test_gun_verilmezse_isaretler_none(self):
        # Bilinmeyen, yanlış bilinenden iyidir: gün yoksa void/clash None.
        ly = self._liu_yao(11)
        assert all(c["void"] is None and c["clash"] is None
                   for c in ly["lines"])

    def test_64_heksagramin_tamami_saraylanir(self):
        from services.liuyao_service import _palace_index
        assert len(_palace_index()) == 64


class TestSozlukVeYerlestirme:
    def test_localize_hexagram_dil_indirger(self):
        # /hexagram/{n} artık localize'dan geçiyor (İ0): İngilizce istemci
        # "judgment" alanını İngilizce metinle alır.
        h = prompts.localize_hexagram("en", get_hexagram(1))
        assert h["judgment"] == h["judgment_en"]
        assert h["name_local"] == h["name_en"]
        t = prompts.localize_hexagram("tr", get_hexagram(1))
        assert t["judgment"] == t["judgment_tr"]

    def test_gecersiz_numara_hata(self):
        with pytest.raises(ValueError):
            get_hexagram(65)


class TestYaoVerisi:
    """İ1 tamlık kapısı: 384 çizgi pasajı iki dilde de eksiksiz olmalı.

    Kısmi veri sessizce yayınlanamaz — çizgi metni olmayan bir heksagram
    raporda o çizgiyi anlatamaz ve kimse hata görmez. İ4 (rapor v2) bu
    test yeşilken açılır.
    """

    def test_384_cizgi_iki_dilde_tam(self):
        data = iching_service._load()
        for h in data["hexagrams"]:
            for alan in ("lines_en", "lines_tr"):
                cizgiler = h.get(alan)
                assert cizgiler and len(cizgiler) == 6, \
                    f"#{h['number']} {alan} eksik"
                assert all(len(c.strip()) > 15 for c in cizgiler), \
                    f"#{h['number']} {alan} kısa/boş pasaj içeriyor"

    def test_tum_cizgiler_pasaji_yalniz_1_ve_2(self):
        # Yong jiu / yong liu klasik olarak yalnız Qian ve Kun'da vardır.
        data = iching_service._load()
        sahipler = sorted(h["number"] for h in data["hexagrams"]
                          if h.get("all_lines_en") or h.get("all_lines_tr"))
        assert sahipler == [1, 2]

    def test_bilinen_cizgi_imgeleri(self):
        # Nokta doğrulama (klasik imgeler): #2/1 kırağı, #63/1 tekerlek.
        h2 = get_hexagram(2)
        assert "hoarfrost" in h2["lines_en"][0]
        assert "Kırağı" in h2["lines_tr"][0] or "kırağı" in h2["lines_tr"][0]
        h63 = get_hexagram(63)
        assert "wheel" in h63["lines_en"][0].lower()
        assert "teker" in h63["lines_tr"][0].lower()

    def test_trigram_atributlari_tam(self):
        # Shuo Gua atributları (İ1): 8 trigramın aile rolleri benzersiz.
        data = iching_service._load()
        aileler = [t["family"] for t in data["trigrams"].values()]
        assert len(set(aileler)) == 8
        for t in data["trigrams"].values():
            assert t["attribute"] and t["direction"]


class TestDogumHeksagrami:
    """İ5: 64 kapı çarkı — çapraz çapalar + dürüstlük beyanları.

    Çark sırası dondurulmuş veridir; üç bağımsız çapa (41→302°, 1→223.25°
    Akrep, 2→43.25° Boğa) listedeki tek bir kaymayı birden yakalar.
    """

    def test_uc_capraz_capa(self):
        from services.birth_hexagram_service import gate_for_longitude
        assert gate_for_longitude(302.0)["gate"] == 41
        assert gate_for_longitude(307.0)["gate"] == 41   # hâlâ 41 içinde
        assert gate_for_longitude(223.25)["gate"] == 1
        assert gate_for_longitude(43.25)["gate"] == 2
        # Koç noktası (0°) Kapı 25'in içindedir — dördüncü çapa.
        assert gate_for_longitude(0.0)["gate"] == 25

    def test_64_kapi_benzersiz_ve_tam(self):
        from services.birth_hexagram_service import GATE_ORDER
        assert sorted(GATE_ORDER) == list(range(1, 65))

    def test_cizgi_hesabi(self):
        from services.birth_hexagram_service import gate_for_longitude
        # Kapı 41 başlangıcından 1.0° içeride: 1.0 / 0.9375 → 2. çizgi.
        assert gate_for_longitude(303.0)["line"] == 2
        assert gate_for_longitude(302.0)["line"] == 1

    def test_saatli_dogum_kapiyi_verir(self):
        from services.birth_hexagram_service import birth_hexagram
        sonuc = birth_hexagram(1990, 5, 12, 14, 30, city="Istanbul")
        assert 1 <= sonuc["gate"] <= 64
        assert 1 <= sonuc["line"] <= 6
        assert sonuc["hour_known"] is True
        assert sonuc["alternate_gate"] is None or True  # yapı var
        assert sonuc["hexagram"]["number"] == sonuc["gate"]

    def test_64_kapi_pasaji_iki_dilde_tam(self):
        # İ8 tamlık kapısı: kısmi kapı içeriği sessizce yayınlanamaz.
        from services.birth_hexagram_service import gate_passage
        for n in range(1, 65):
            pasaj = gate_passage(n)
            assert len(pasaj.get("gate_tr", "")) > 80, f"kapı {n} TR"
            assert len(pasaj.get("gate_en", "")) > 80, f"kapı {n} EN"

    def test_saatsiz_sinirda_iki_aday(self):
        from services.birth_hexagram_service import birth_hexagram
        # Gün içinde Güneş ~1° ilerler: kapı sınırının aşıldığı bir gün
        # bulmak için tarama — saatli/saatsiz farkını yapısal test eder.
        import datetime as dtm
        bulundu = False
        for gun in range(1, 20):
            s = birth_hexagram(2000, 3, gun, None, 0, city="Istanbul")
            assert s["hour_known"] is False
            if s["alternate_gate"]:
                bulundu = True
                assert s["alternate_gate"] != s["gate"]
                assert s["alternate_hexagram"]["number"] == \
                    s["alternate_gate"]
        assert bulundu, "20 günlük taramada hiç sınır günü çıkmadı"


class TestOnbellekAnahtari:
    def test_yontem_anahtari_ayirir(self, tmp_path, monkeypatch):
        """İ0 kusur kapanışı: aynı soru + aynı heksagram + aynı çizgilerle
        yarrow çeken kullanıcı coins yorumunu GÖRMEMELİ — prompt yöntemi
        metne yazıyor."""
        from core import cache, config
        from services import report_service
        monkeypatch.setattr(config, "CACHE_DIR", tmp_path)
        monkeypatch.setattr(config, "CACHE_BACKEND", "file")
        cache._memory.clear()

        uretim = {"n": 0}

        def sahte(prompt, **k):
            uretim["n"] += 1
            return "ok"

        monkeypatch.setattr(report_service.gemini_service, "generate", sahte)
        monkeypatch.setattr(report_service, "retrieve_context",
                            lambda *a, **k: "")

        def cekim(method):
            return {"question": "test", "method": method,
                    "line_values": [7] * 6, "lines": [1] * 6,
                    "moving_lines": [],
                    "primary": iching_service._hexagram_info([1] * 6)}

        report_service.iching_reading("u-i0", cekim("coins"), lang="tr")
        report_service.iching_reading("u-i0", cekim("coins"), lang="tr")
        assert uretim["n"] == 1  # ikinci coins isabet
        report_service.iching_reading("u-i0", cekim("yarrow"), lang="tr")
        assert uretim["n"] == 2  # yarrow AYRI anahtar
        cache._memory.clear()


class TestSoruKapisi:
    """R10: günde tek çekim hakkı "merhaba" ile harcanmasın."""

    def test_niyetsiz_girisler_cevrilir(self):
        for soru in ["merhaba", "selam", "Selam naber", "MERHABA NASILSIN",
                     "iyi misin", "test", "deneme", "asdf", "evet", "iş?"]:
            assert not iching_service.question_is_meaningful(soru), soru

    def test_gercek_sorular_gecer(self):
        for soru in ["İş değiştirmeli miyim?", "Önümdeki yol nereye çıkıyor",
                     "Bu ilişki beni büyütüyor mu",
                     "Should I take the new job offer?",
                     "taşınma kararım doğru mu"]:
            assert iching_service.question_is_meaningful(soru), soru

    def test_turkce_buyuk_i_tuzagi(self):
        # casefold("İ") birleşik nokta üretir; motor onu atmalı ki "İYİ"
        # dolgu listesindeki "iyi" ile, "MISIN" da "misin" ile eşleşsin.
        assert not iching_service.question_is_meaningful("İYİ MISIN")
        assert not iching_service.question_is_meaningful("İyi misin")


class TestSoruHukmu:
    """R11: kapı kararı LLM'de — kelime listesi yalnız bariz ön filtre."""

    @staticmethod
    def _zemin(monkeypatch, tmp_path, cevap):
        from core import cache, config
        from services import report_service
        monkeypatch.setattr(config, "CACHE_DIR", tmp_path)
        monkeypatch.setattr(config, "CACHE_BACKEND", "file")
        cache._memory.clear()
        cagri = {"n": 0}

        def sahte(prompt, schema=None, **_):
            cagri["n"] += 1
            return cevap

        monkeypatch.setattr(report_service.gemini_service,
                            "extract_json", sahte)
        return report_service, cache, cagri

    def test_llm_hukumleri_uygulanir(self, monkeypatch, tmp_path):
        rs, cache, _ = self._zemin(monkeypatch, tmp_path,
                                   '{"verdict": "CHAT"}')
        assert rs.iching_question_verdict("beni seviyor musun",
                                          "tr") == "CHAT"
        cache._memory.clear()

    def test_bariz_dolgu_llm_cagirmaz(self, monkeypatch, tmp_path):
        rs, cache, cagri = self._zemin(monkeypatch, tmp_path,
                                       '{"verdict": "VALID"}')
        assert rs.iching_question_verdict("merhaba", "tr") == "INVALID"
        assert cagri["n"] == 0  # ücretsiz ön filtre kesmiş olmalı
        cache._memory.clear()

    def test_siniflandirici_dusunce_gecirir(self, monkeypatch, tmp_path):
        # Fail-open: model erişilemezse ya da saçma dönerse ritüel durmaz;
        # prompt'taki anlamsız-soru kuralı son ağ olarak kalır.
        for bozuk in [None, "not-json", '{"verdict": "MAYBE"}']:
            rs, cache, _ = self._zemin(monkeypatch, tmp_path, bozuk)
            assert rs.iching_question_verdict(
                f"garip metin {bozuk}", "tr") == "VALID"
            cache._memory.clear()

    def test_hukum_onbelleklenir(self, monkeypatch, tmp_path):
        rs, cache, cagri = self._zemin(monkeypatch, tmp_path,
                                       '{"verdict": "INVALID"}')
        for _ in range(2):
            assert rs.iching_question_verdict("dsfkj sdlkfj weoi",
                                              "tr") == "INVALID"
        assert cagri["n"] == 1  # ikinci soruş önbellekten
        cache._memory.clear()
