"""I Ching motoru altın vektörleri (Revize İ0).

Bu dosyadan önce çekim motorunun HİÇBİR aritmetiği test edilmiyordu:
biri yarrow eşiğini `r < 6`'dan `r < 5`'e kaydırsa hiçbir test kırılmaz,
yalnızca olasılıklar sessizce bozulurdu. Kural test_bazi_engine ile aynı:
altın değerler çift kaynakla doğrulanır ve vektörün yanına yazılır.
"""
from __future__ import annotations

import pytest

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
