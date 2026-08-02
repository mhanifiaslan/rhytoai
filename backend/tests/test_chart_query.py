"""Haritadan RAG sorgusu üretme.

Buranin degeri tek cumleyle: arama artik kullanicinin CUMLESIYLE degil,
cumlenin konusu + haritanin o konudaki faktorleriyle yapiliyor. "Isimle
ilgili ne yapmaliyim?" kadim metinde hicbir seye denk gelmez; "meslek,
statu + Saturn 10. evde + Gunes Kare Mars" gelir.

Calistirma:  .venv\\Scripts\\python.exe -m pytest tests/test_chart_query.py -q
"""
from __future__ import annotations

import pytest

from services import chart_query
from services.prompt_composer import detect_topics, normalize, should_use_rag

#: Sabit olgu sozlugu — efemeris hesabi bu testlerin konusu degil.
OLGULAR = {
    "sun": {"planet": "Sun", "sign": "leo", "house": 12, "retrograde": False},
    "moon": {"planet": "Moon", "sign": "taurus", "house": 9,
             "retrograde": False},
    "ascendant": "virgo",
    "placements": [
        {"planet": "Mercury", "sign": "virgo", "house": 1, "retrograde": False},
        {"planet": "Venus", "sign": "leo", "house": 11, "retrograde": False},
        {"planet": "Mars", "sign": "taurus", "house": 9, "retrograde": False},
        {"planet": "Jupiter", "sign": "cancer", "house": 10,
         "retrograde": False},
        {"planet": "Saturn", "sign": "capricorn", "house": 5,
         "retrograde": True},
    ],
    "elements": {"fire": 2, "earth": 5, "air": 0, "water": 1},
    "modalities": {"cardinal": 2, "fixed": 4, "mutable": 2},
    "stelliums": [],
    "aspects": [
        {"p1": "Sun", "p2": "Mars", "aspect": "square", "orb": 0.5},
        {"p1": "Moon", "p2": "Jupiter", "aspect": "sextile", "orb": 1.0},
    ],
    "transits": [
        {"transit": "Saturn", "natal": "Sun", "aspect": "opposition",
         "orb": 0.8},
    ],
}


# --------------------------------------------------------------------------
# Turkce noktali I — sessiz ve gercek bir hata
# --------------------------------------------------------------------------

def test_turkce_noktali_i_dogru_kucultulur():
    """Python'un str.lower() metodu Turkce bilmez.

    ``"İ".lower()`` sonucu ``"i"`` DEGIL, ``"i" + U+0307`` (birlesik nokta).
    Sonuc sessiz bir bozulmaydi: "Isimle ilgili..." diye baslayan mesajda
    "is" koku hic eslesmiyordu. Turkce cumleler buyuk harfle basladigi icin
    bu kenar durum degil.
    """
    assert normalize("İşimle") == "işimle"
    assert "iş" in normalize("İşimle")
    # Turkcede buyuk I'nin karsiligi noktasiz i'dir
    assert normalize("Ilık") == "ılık"
    assert normalize("İLİŞKİ") == "ilişki"


def test_buyuk_harfle_baslayan_soru_rag_tetikler():
    """Regresyon: bu mesaj daha once RAG'e HIC ugramiyordu."""
    assert should_use_rag("İşimle ilgili ne yapmalıyım?", "tr")
    assert detect_topics("İşimle ilgili ne yapmalıyım?", "tr") == ["vocation"]


# --------------------------------------------------------------------------
# Konu tespiti
# --------------------------------------------------------------------------

def test_iliski_sorusu_meslek_konusunu_tetiklemez():
    """Regresyon: "ilişkimde" kelimesinin ICINDE "iş" geciyor
    (il-**iş**-kimde) ve alt dizi aramasi ile iliski sorusu meslek konusunu
    tetikliyordu. Turkce sondan eklemeli oldugu icin kelime BASI eslesmesi
    dogru olan."""
    konular = detect_topics("İlişkimde neden hep aynı yere geliyorum?", "tr")
    assert "relationship" in konular
    assert "vocation" not in konular


@pytest.mark.parametrize("mesaj,beklenen", [
    ("İşimle ilgili ne yapmalıyım?", "vocation"),
    ("Sevgilimle sürekli tartışıyoruz", "relationship"),
    ("Kafam çok dağınık, odaklanamıyorum", "mind"),
    ("Mizacım neden böyle?", "temperament"),
    ("Yurtdışına taşınmayı düşünüyorum", "travel"),
])
def test_turkce_konular_taninir(mesaj, beklenen):
    assert beklenen in detect_topics(mesaj, "tr")


@pytest.mark.parametrize("mesaj,beklenen", [
    ("What should I do about my job?", "vocation"),
    ("My relationship keeps hitting the same wall", "relationship"),
    ("Why do I overthink everything?", "mind"),
    ("What is my temperament like?", "temperament"),
])
def test_ingilizce_konular_taninir(mesaj, beklenen):
    assert beklenen in detect_topics(mesaj, "en")


def test_ingilizce_alt_dizi_kullanir():
    """Ingilizcede ekler ONE de gelir; kelime basi eslesmesi "overthink"
    icindeki "think"i kacirirdi."""
    assert "mind" in detect_topics("I overthink constantly", "en")


def test_selamlasma_konu_uretmez():
    assert detect_topics("selam nasılsın", "tr") == []
    assert detect_topics("hey there", "en") == []
    assert not should_use_rag("selam nasılsın", "tr")


def test_en_fazla_iki_konu():
    """Ucuncu konu sorguyu odaksiz hale getiriyor."""
    karisik = ("işim, ilişkim, kafam, mizacım ve yolculuk planlarım "
               "hakkında ne düşünüyorsun")
    assert len(detect_topics(karisik, "tr")) <= 2


# --------------------------------------------------------------------------
# Sorgu kurulumu
# --------------------------------------------------------------------------

def test_meslek_sorgusu_ilgili_gezegenleri_tasir():
    sorgu = chart_query.build_query("İşimle ilgili ne yapmalıyım?",
                                    OLGULAR, lang="tr")
    assert "Mesleğin niteliği" in sorgu
    # Batlamyus'un meslek belirleyicileri
    assert "Merkür" in sorgu
    # 10. evdeki gezegen de alinmali (ev uzerinden secim)
    assert "Jüpiter" in sorgu


def test_iliski_sorgusu_venus_ve_yedinci_evi_tasir():
    sorgu = chart_query.build_query("Sevgilimle tartışıyoruz", OLGULAR,
                                    lang="tr")
    assert "Evlilik" in sorgu
    assert "Venüs" in sorgu


def test_sorgu_korpusun_dilinde_kurulur():
    """Ingilizce korpusta "Satürn" aramak aramanin yarisini bosa harcamak
    olurdu."""
    tr = chart_query.build_query("İşimle ilgili ne yapmalıyım?", OLGULAR,
                                 lang="tr")
    en = chart_query.build_query("What should I do about my job?", OLGULAR,
                                 lang="en")
    assert "Merkür" in tr and "Başak" in tr
    assert "Mercury" in en and "Virgo" in en
    assert "Merkür" not in en
    assert "Mercury" not in tr


def test_transit_yalnizca_zaman_sorusunda_girer():
    """Her sorguya eklemek bugunun gokyuzunu kalici bir karakter ozelligi gibi
    agirliklandirirdi."""
    zaman = chart_query.build_query("Şu an nasıl bir dönemdeyim?", OLGULAR,
                                    lang="tr")
    genel = chart_query.build_query("Mizacım neden böyle?", OLGULAR,
                                    lang="tr")
    assert "Karşıt" in zaman  # transit Satürn karşıt Güneş
    assert "transit" in zaman.lower()
    assert "Karşıt" not in genel


def test_mizac_sorusunda_baskin_element_girer():
    sorgu = chart_query.build_query("Mizacım neden böyle?", OLGULAR,
                                    lang="tr")
    assert "Toprak" in sorgu  # olgularda earth 5 ile baskin


def test_harita_yoksa_mesajin_kendisi_kullanilir():
    """Dogum verisi girilmemis kullanicida davranis eskisiyle ayni kalir."""
    mesaj = "İşimle ilgili ne yapmalıyım?"
    assert chart_query.build_query(mesaj, None, lang="tr") == mesaj
    assert chart_query.build_query(mesaj, {}, lang="tr") == mesaj


def test_konu_bulunamazsa_haritanin_omurgasi_verilir():
    sorgu = chart_query.build_query("bugün biraz tuhaf hissediyorum",
                                    OLGULAR, lang="tr")
    assert sorgu
    # Bos sorgu embedding'i anlamsizdir; en azindan buyuk uclu girmeli
    assert "Güneş" in sorgu or "Ay" in sorgu


def test_sorgu_odagini_kaybedecek_kadar_uzamaz():
    """Embedding tek bir vektore indirger: her fazladan ayrinti asil konuyu
    seyreltir."""
    for mesaj in ("İşimle ilgili ne yapmalıyım?",
                  "Şu an nasıl bir dönemdeyim?",
                  "işim ve ilişkim hakkında ne düşünüyorsun"):
        sorgu = chart_query.build_query(mesaj, OLGULAR, lang="tr")
        assert len(sorgu) < 400, f"sorgu {len(sorgu)} karaktere cikti"


def test_sorgu_ayni_konuda_kararlidir():
    """Sorgu embedding'i sorgu metnine gore onbellekleniyor. Ham kullanici
    mesajlari neredeyse hic tekrar etmedigi icin onbellek calismiyordu;
    haritadan kurulan sorgu ayni kullanici + ayni konu icin AYNI metni
    uretir ve ~1 sn'lik embedding cagrisi atlanir."""
    a = chart_query.build_query("İşimle ilgili ne yapmalıyım?", OLGULAR,
                                lang="tr")
    b = chart_query.build_query("İşim beni çok yoruyor", OLGULAR, lang="tr")
    assert a == b


def test_ham_dogum_verisi_sorguya_girmez():
    """Sorgu embedding API'sine gidiyor; ham dogum verisi disari cikmamali."""
    sorgu = chart_query.build_query("İşimle ilgili ne yapmalıyım?", OLGULAR,
                                    lang="tr")
    for yasak in ("1990", "Istanbul", "07:35", "08-14"):
        assert yasak not in sorgu
