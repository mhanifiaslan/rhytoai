"""S-turu: RAG kapisi para/aile sorularini gecirsin + korpus butunlugu.

## Bu dosyanin varlik sebebi

Olculdu: "Para konusunda hep ayni hatayi yapiyorum" ve "Babamla aram hic
duzelmeyecek mi" — en sik gelen iki hayat sorusu — RAG'e HIC gitmiyordu.
Sebep ikiye ayriliyordu:

1. `_TOPIC_TRIGGERS` para ve aile konusunu hic TANIMIYORDU, yani
   `should_use_rag` bu mesajlari kapiyordu.
2. Korpusta zaten karsiligi da YOKTU — servet ve ebeveyn/kardes/cocuk
   bolumleri hicbir dilde aktarilmamisti.

Bu dosya ikisini birden dogruluyor: kapinin acildigini VE korpusun
gercekten karsilik verdigini.

Calistirma:  .venv\\Scripts\\python.exe -m pytest tests/test_rag_coverage.py -q
"""
from __future__ import annotations

import pytest

from services import chart_query, rag_service as rs
from services.prompt_composer import detect_topics, should_use_rag


# --------------------------------------------------------------------------
# 1. Kapi acik — bu turun olcttugu bosluk
# --------------------------------------------------------------------------

PARA_TR = [
    "Para konusunda hep aynı hatayı yapıyorum",
    "Borç içinde debeleniyorum",
    "Maaşım hiç yetmiyor",
]
AILE_TR = [
    "Babamla aram hiç düzelmeyecek mi",
    "Annemle aramda hep bir mesafe var",
    "Kardeşimle sürekli çatışıyoruz",
]
PARA_EN = [
    "I keep making the same mistake with money",
    "I'm drowning in debt",
]
AILE_EN = [
    "Will things ever be right with my father",
    "My mother and I have never been close",
]


@pytest.mark.parametrize("mesaj", PARA_TR)
def test_para_sorulari_rag_ye_gider_tr(mesaj):
    assert should_use_rag(mesaj, "tr") is True, f"KAPALI KALDI: {mesaj}"
    assert "money" in detect_topics(mesaj, "tr")


@pytest.mark.parametrize("mesaj", AILE_TR)
def test_aile_sorulari_rag_ye_gider_tr(mesaj):
    assert should_use_rag(mesaj, "tr") is True, f"KAPALI KALDI: {mesaj}"
    assert "family" in detect_topics(mesaj, "tr")


@pytest.mark.parametrize("mesaj", PARA_EN)
def test_para_sorulari_rag_ye_gider_en(mesaj):
    assert should_use_rag(mesaj, "en") is True, f"STAYED CLOSED: {mesaj}"
    assert "money" in detect_topics(mesaj, "en")


@pytest.mark.parametrize("mesaj", AILE_EN)
def test_aile_sorulari_rag_ye_gider_en(mesaj):
    assert should_use_rag(mesaj, "en") is True, f"STAYED CLOSED: {mesaj}"
    assert "family" in detect_topics(mesaj, "en")


def test_var_olan_konular_bozulmadi():
    """Yeni kelime listeleri eski konularin isini calmamali."""
    assert "vocation" in detect_topics("İşimde tıkandım", "tr")
    assert "relationship" in detect_topics("Sevgilimden ayrıldım", "tr")


# --------------------------------------------------------------------------
# 2. Tohum + faktor tablolari
# --------------------------------------------------------------------------

class TestTohumVeFaktor:
    @pytest.mark.parametrize("dil", ["tr", "en"])
    def test_money_family_tohumu_var(self, dil):
        assert chart_query.topic_seed("money", dil)
        assert chart_query.topic_seed("family", dil)

    def test_money_family_faktoru_var(self):
        from services.chart_query import _TOPIC_FACTORS
        assert "money" in _TOPIC_FACTORS
        assert "family" in _TOPIC_FACTORS
        assert _TOPIC_FACTORS["money"]["houses"]
        assert _TOPIC_FACTORS["family"]["houses"]


# --------------------------------------------------------------------------
# 3. Korpus gercekten karsilik veriyor (tohumla birlikte — gercek yol)
# --------------------------------------------------------------------------

class TestKorpusKarsiligi:
    """`api/chat.py`'deki gercek yol: `build_query` harita varken tohumu
    mesajin ONUNE ekler (bkz. `chart_query.build_query`). Test bu bilesimi
    kullaniyor — tohum TEK BASINA kisa bir anahtar kelime listesi ve gercek
    uretimde hic bu sekilde aranmiyor; yalniz tohumla aramak dusuk isabetli
    cikabilir ve bu korpusun degil, testin gerceklige uymayacagi bir
    senaryo olurdu."""

    @pytest.mark.parametrize("dil,tohum_konu,mesaj,beklenen_baslik_parcasi", [
        ("tr", "money", "Para konusunda hep aynı hatayı yapıyorum", "Kazanç"),
        ("tr", "family", "Babamla aram hiç düzelmeyecek mi", "Baba"),
        ("en", "family", "Will things ever be right with my father",
         "Father"),
    ])
    def test_tohum_ve_mesajla_dogru_bolum_gelir(
            self, dil, tohum_konu, mesaj, beklenen_baslik_parcasi):
        tohum = chart_query.topic_seed(tohum_konu, dil)
        sorgu = f"{tohum} {mesaj}"
        sonuc = rs.retrieve_passages(sorgu, top_k=3, lang=dil)
        basliklar = " ".join(p.get("title", "") for p in sonuc)
        assert beklenen_baslik_parcasi in basliklar, (
            f"'{beklenen_baslik_parcasi}' hicbir baslikta yok: {basliklar}")

    def test_en_money_dogru_dokumandan_gelir(self):
        """Buradaki asil iddia TOPIC dogrulugu: getirilen parcalar
        wealth_doctrine'den mi geliyor. Hangi ALT BASLIGIN one ciktigi
        (Permanence mi, Earning Gate mi) embedding modelinin kendi
        siralamasi ve kirilgan bir beklenti olurdu — icerik zaten S5'te
        kanitlandi (bkz. test_servet_dokumani_yuklu)."""
        tohum = chart_query.topic_seed("money", "en")
        sorgu = f"{tohum} I keep making the same mistake with money"
        sonuc = rs.retrieve_passages(sorgu, top_k=3, lang="en")
        assert sonuc, "hicbir parca donmedi"
        # Basliklarin en az biri servet dokumaninin bilinen basliklarindan.
        bilinen = {"The Part of Fortune: the Marker of Livelihood",
                  "The Earning Gate, by Planet", "Inheritance and What "
                  "Comes From Outside", "Permanence",
                  "The Second-House Tradition"}
        basliklar = {p.get("title") for p in sonuc}
        assert basliklar & bilinen, f"servet dokumanindan hicbir parca yok: {basliklar}"

    @pytest.mark.parametrize("dil", ["tr", "en"])
    def test_servet_dokumani_yuklu(self, dil):
        parcalar = rs._load_chunks(dil)
        kaynaklar = {c.doc for c in parcalar}
        assert any("wealth" in d or "servet" in d for d in kaynaklar)

    @pytest.mark.parametrize("dil", ["tr", "en"])
    def test_aile_dokumani_yuklu(self, dil):
        parcalar = rs._load_chunks(dil)
        kaynaklar = {c.doc for c in parcalar}
        assert any("family" in d or "aile" in d for d in kaynaklar)


# --------------------------------------------------------------------------
# 4. Guvenlik sinirlari korundu (S5'in aktarmadigi icerik)
# --------------------------------------------------------------------------

class TestGuvenlikSiniriKorpusaGirmedi:
    """Aile dokumaninin OLUMLU/ANLATI kismi olum/dogurganlik kehaneti
    TASIMAMALI — bu S5'te bilincli olarak disarida birakilan icerikti.

    "Sinir"/"Boundary" bolumu ISTISNA: o bolumun ISI, yasakli konuyu ADIYLA
    anip reddetmek ("cocugun saglig... asla yorumlanmaz" gibi). O cumleyi
    de tarasaydik kendi inkarimizi "sizinti" sayardik — bu yuzden yalniz
    ANLATI (doktrin) parcalari taranir.
    """

    YASAK_TR = ("çocuk sahibi ol", "doğurgan", "kısır", "ölüm şekli",
               "ne zaman ölecek")
    YASAK_EN = ("will have children", "infertil", "manner of death",
               "when they will die")

    @pytest.mark.parametrize("dil,yasaklar", [("tr", YASAK_TR),
                                              ("en", YASAK_EN)])
    def test_yasak_kehanet_anlati_kisminda_yok(self, dil, yasaklar):
        parcalar = rs._load_chunks(dil)
        aile = [c for c in parcalar
               if ("family" in c.doc or "aile" in c.doc)
               and "sınır" not in c.title.lower()
               and "boundary" not in c.title.lower()]
        assert aile, f"aile dokumaninin anlati kismi bulunamadi ({dil})"
        tum_metin = " ".join(c.text.lower() for c in aile)
        for yasak in yasaklar:
            assert yasak not in tum_metin, f"YASAK ICERIK ANLATIYA SIZDI: {yasak}"

    @pytest.mark.parametrize("dil", ["tr", "en"])
    def test_sinir_bolumu_yasakli_konuyu_REDDEDEREK_anar(self, dil):
        """Sinir bolumu yasakli konudan HIC bahsetmezse, sunucu ekibi
        yarin ayni hatayi (olum kehaneti sizmasi) fark edemez — bolumun
        var olma sebebi tam olarak bu konuyu adiyla reddetmek."""
        parcalar = rs._load_chunks(dil)
        sinir = [c for c in parcalar
                if ("family" in c.doc or "aile" in c.doc)
                and ("sınır" in c.title.lower()
                     or "boundary" in c.title.lower())]
        assert sinir, f"sinir bolumu bulunamadi ({dil})"
        metin = " ".join(c.text.lower() for c in sinir)
        anahtar = "doğurgan" if dil == "tr" else "fertility"
        assert anahtar in metin


# --------------------------------------------------------------------------
# 5. Kapsama bekcisi (build_embeddings --check ile ayni sozlesme)
# --------------------------------------------------------------------------

def test_hicbir_parcanin_vektoru_eksik_degil():
    """Yeni dosyalar embed edilmeden birakilmis olabilir — bu, RAG'in
    sessizce yari calisir kalmasinin en kolay yolu."""
    for dil in ("tr", "en"):
        parcalar = rs._load_chunks(dil)
        vektorler = rs.read_artifact(dil)
        eksik = [c.chunk_id for c in parcalar if c.chunk_id not in vektorler]
        assert not eksik, f"[{dil}] vektoru eksik parca: {eksik[:5]}"
