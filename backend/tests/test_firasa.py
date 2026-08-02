"""Firaset: oranlardan belirtiye, belirtiden prompt'a.

Bu katmanin ic degismezleri urun ilkelerinden geliyor:

* Sunucu GORUNTU GORMEZ. Uc yalnizca sayi alir.
* BELIRTI uretilir, HUKUM degil.
* Olcemedigimiz eksen HER SEFERINDE bildirilir; bilmedigini bilmeyen model
  uydurur.

Calistirma:  .venv\\Scripts\\python.exe -m pytest tests/test_firasa.py -q
"""
from __future__ import annotations

import pytest

from services import firasa_service, prompts

ORTALAMA = {
    "upperThird": 0.33, "middleThird": 0.33, "lowerThird": 0.34,
    "widthToHeight": 0.70, "jawToCheek": 0.80, "mouthToFaceWidth": 0.41,
    "lipFullness": 0.05, "eyeSpacing": 0.45, "symmetry": 0.98,
}
UZUN = {
    "upperThird": 0.40, "middleThird": 0.32, "lowerThird": 0.28,
    "widthToHeight": 0.62, "jawToCheek": 0.71, "mouthToFaceWidth": 0.34,
    "lipFullness": 0.035, "eyeSpacing": 0.41, "symmetry": 0.91,
}
GENIS = {
    "upperThird": 0.30, "middleThird": 0.31, "lowerThird": 0.39,
    "widthToHeight": 0.79, "jawToCheek": 0.89, "mouthToFaceWidth": 0.48,
    "lipFullness": 0.068, "eyeSpacing": 0.50, "symmetry": 0.97,
}


# --------------------------------------------------------------------------
# Belirti cikarimi
# --------------------------------------------------------------------------

def test_ortalama_yuz_belirti_uretmez():
    """Ortalama bir yuz hakkinda soylenecek belirti yoktur.

    Bos listeyi doldurmak icin esik gevsetmek, yorum uydurmaya davetiye
    olurdu. Az belirti uretip emin olmak, cok belirti uretip uydurmaktan iyi.
    """
    assert firasa_service.descriptors(ORTALAMA) == []


def test_uzun_yuz_kuruluk_tarafina_dusuyor():
    k = firasa_service.descriptors(UZUN)
    assert "face_long" in k
    assert "jaw_tapered" in k
    assert "lips_thin" in k
    assert firasa_service.moisture_lean(k) == "dry"


def test_genis_yuz_nemlilik_tarafina_dusuyor():
    k = firasa_service.descriptors(GENIS)
    assert "face_broad" in k
    assert "jaw_square" in k
    assert "lips_full" in k
    assert firasa_service.moisture_lean(k) == "moist"


def test_dengeli_belirtide_taraf_secilmez():
    """Beraberlikte None doner ve bu kasitli: gelenek 'tek belirti hukum
    vermez' diyor; dengeli bir yuzde bir tarafi secmek de hukum uydurmaktir.
    """
    assert firasa_service.moisture_lean(["face_long", "face_broad"]) is None
    assert firasa_service.moisture_lean([]) is None


def test_simetri_yalnizca_belirginse_anilir():
    """Hicbir yuz tam simetrik degil; her okumada 'yuzun biraz asimetrik'
    demek bilgi degil gurultudur."""
    assert "asymmetry_marked" not in firasa_service.descriptors(ORTALAMA)
    assert "asymmetry_marked" in firasa_service.descriptors(UZUN)


def test_bozuk_veri_coker_degil_eler():
    for bozuk in ({}, {"upperThird": "abc"}, {"widthToHeight": None}):
        assert firasa_service.descriptors(bozuk) == []


# --------------------------------------------------------------------------
# Prompt blogu
# --------------------------------------------------------------------------

@pytest.mark.parametrize("lang", ["tr", "en"])
def test_hareket_yoksa_eksen_olculemedi_denir(lang):
    """Hareket alani gonderilmediyse eksen olculemedi demektir.

    Bilmedigini bilmeyen model uydurur; sessiz kalmak modelin o eksende de
    hukum vermesine kapi acardi.
    """
    for oran in (ORTALAMA, UZUN, GENIS):
        blok = firasa_service.prompt_block(oran, lang)
        assert prompts.get(lang).FIRASA_HEAT_UNKNOWN in blok


# --------------------------------------------------------------------------
# Sicak-soguk ekseni (hareket)
# --------------------------------------------------------------------------

def test_hizli_hareket_sicak_tarafa():
    assert firasa_service.heat_lean({**UZUN, "motionRate": 0.31}) == "fast"


def test_agir_hareket_soguk_tarafa():
    assert firasa_service.heat_lean(
        {**UZUN, "motionRate": 0.04, "stillness": 0.02}) == "slow"


def test_arada_kalan_olcum_taraf_secmez():
    """Esikler arasi bosluk BILEREK genis: arada kalan bir olcum icin taraf
    secmektense hicbir sey sylememek dogru."""
    assert firasa_service.heat_lean({**UZUN, "motionRate": 0.11}) == "ambiguous"


def test_olculemedi_ile_arada_kaldi_AYRI_durumlar():
    """Ikisini ayni kefeye koymak yanlis olurdu.

    "Olcemedim, elimde yalnizca duragan bicim var" ile "olctum, net bir
    tarafa dusmedi" farkli ifadelerdir ve modele farkli soylenmeleri gerekir.
    """
    assert firasa_service.heat_lean(UZUN) is None
    assert firasa_service.heat_lean({**UZUN, "motionRate": 0.11}) == "ambiguous"

    for lang in ("tr", "en"):
        p = prompts.get(lang)
        yok = firasa_service.prompt_block(UZUN, lang)
        arada = firasa_service.prompt_block({**UZUN, "motionRate": 0.11}, lang)
        assert p.FIRASA_HEAT_UNKNOWN in yok
        assert p.FIRASA_HEAT_AMBIGUOUS in arada
        assert p.FIRASA_HEAT_UNKNOWN not in arada


def test_sifir_hareket_olcum_sayilmaz():
    """Istemci guvenilir bulmadiginda alani HIC gondermiyor. Sifir gelirse
    de bu 'olctum ve sifir cikti' degil, bozuk veri sayilir."""
    assert firasa_service.heat_lean(
        {**UZUN, "motionRate": 0.0, "stillness": 0.0}) == "ambiguous"


def test_bozuk_hareket_verisi_cokmez():
    for bozuk in ({"motionRate": "abc"}, {"stillness": None}):
        firasa_service.heat_lean({**UZUN, **bozuk})


@pytest.mark.parametrize("lang", ["tr", "en"])
def test_hareket_olculunce_eksen_acilir(lang):
    p = prompts.get(lang)
    hizli = firasa_service.prompt_block({**UZUN, "motionRate": 0.31}, lang)
    assert p.FIRASA_HEAT["fast"] in hizli
    assert p.FIRASA_HEAT_UNKNOWN not in hizli


@pytest.mark.parametrize("lang", ["tr", "en"])
def test_belirtisiz_yuzde_bos_blok_gonderilmez(lang):
    """Bos blok gondermek modele 'bir seyler bul' demek olurdu."""
    blok = firasa_service.prompt_block(ORTALAMA, lang)
    assert prompts.get(lang).FIRASA_NO_MARKED_SIGNS in blok


def test_blok_hukum_degil_gozlem_tasir():
    """Kaynakta 'burnu uzun olanin anlayisi kittir' gibi hukumler var; buraya
    yalnizca olculen BICIM giriyor."""
    blok = firasa_service.prompt_block(UZUN, "tr").lower()
    for yargi in ("zeki", "aptal", "ahmak", "güvenilir", "hain", "kıt"):
        assert yargi not in blok


def test_blok_ham_olcum_sizdirmaz():
    """Prompt'a sayilar degil belirtiler girer; ham oran modele bir sey
    ogretmiyor ama ciktida tekrarlanma riski tasiyor."""
    blok = firasa_service.prompt_block(UZUN, "tr")
    assert "0.40" not in blok and "0.62" not in blok


# --------------------------------------------------------------------------
# Dil izolasyonu
# --------------------------------------------------------------------------

def test_belirti_tablolari_ayni_anahtarlari_tasir():
    tr = set(prompts.get("tr").FIRASA_SIGNS)
    en = set(prompts.get("en").FIRASA_SIGNS)
    assert tr == en


def test_tum_belirtilerin_adi_var():
    """Motor yeni bir belirti uretirse iki dilde de karsiligi olmali."""
    uretilebilen = set()
    for oran in (ORTALAMA, UZUN, GENIS):
        uretilebilen.update(firasa_service.descriptors(oran))
    for lang in ("tr", "en"):
        tablo = prompts.get(lang).FIRASA_SIGNS
        assert uretilebilen <= set(tablo), \
            f"{lang} icinde eksik belirti: {uretilebilen - set(tablo)}"


def test_ingilizce_blok_turkce_icermez():
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from test_language_isolation import turkce_kalinti

    for oran in (ORTALAMA, UZUN, GENIS):
        blok = firasa_service.prompt_block(oran, "en")
        assert not turkce_kalinti(blok), \
            f"Ingilizce firaset blogunda Turkce: {turkce_kalinti(blok)}"


def test_firaset_sablonu_gelenegin_sinirini_tasir():
    """Personanin dayanacagi zemin korpustaki 'Firasetin Siniri' bolumu.

    Eski face_report 'her ozellik guc + gelisim alani' diyordu — urunun
    'pohpohlama yok' ilkesinin tam tersi. Yerini bu kurallar aldi.
    """
    tr = prompts.get("tr").FIRASA
    assert "TEK BELİRTİ HÜKÜM VERMEZ" in tr
    assert "KADER DEĞİLDİR" in tr
    assert "Sağlık" in tr

    en = prompts.get("en").FIRASA
    assert "A SINGLE SIGN DECIDES NOTHING" in en
    assert "NOT A FATE" in en
    assert "health" in en


def test_sablonda_yagcilik_talimati_yok():
    for lang in ("tr", "en"):
        sablon = prompts.get(lang).FIRASA.lower()
        for kalip in ("pozitif psikoloji", "güç + gelişim",
                      "positive psychology", "growth area"):
            assert kalip not in sablon
