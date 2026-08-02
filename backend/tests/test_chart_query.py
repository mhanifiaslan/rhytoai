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


def test_mesaj_sorguya_her_zaman_girer():
    """Regresyon: ilk surumde mesaj tamamen ATILIYOR, yerine yalnizca konu
    tohumu + harita konuyordu. Iki sonucu vardi:

    1. Konu eslesmediginde sorgu HER SORU ICIN AYNI oluyordu — "Bugun hangi
       gezegenin gunu?" ile "Ayin menzili ne demek?" birebir ayni metni
       uretiyordu.
    2. Konu eslesse bile mesajin kendi icerigi kayboluyordu: "YUZUMDEN
       mizacim okunur mu?" sorusunda "yuzumden" dusuyor, firaset yerine
       genel mizac bolumu geliyordu.

    Dogru bolusum: mesaj NEYIN soruldugunu, harita KIMIN sordugunu tasir.
    """
    a = chart_query.build_query("Bugün hangi gezegenin günü?", OLGULAR,
                                lang="tr")
    b = chart_query.build_query("Ayın menzili ne demek?", OLGULAR, lang="tr")
    assert a != b, "farkli sorular ayni sorguyu uretiyor"
    assert "gezegenin günü" in a
    assert "menzili" in b

    c = chart_query.build_query("Yüzümden mizacım okunur mu?", OLGULAR,
                                lang="tr")
    assert "Yüzümden" in c


def test_konu_taninmazsa_harita_eklenmez():
    """Konuyu bilmemek, hangi olgularin ilgili oldugunu bilmemek demektir.
    Kisiye ozel olmayan bir soruya kisiye ozel baglam eklemek
    kisisellestirme degil, gurultudur."""
    mesaj = "Ayın menzili ne demek?"
    sorgu = chart_query.build_query(mesaj, OLGULAR, lang="tr")
    assert sorgu == mesaj
    assert "Aslan" not in sorgu and "Kare" not in sorgu


def test_firaset_kendi_konusudur():
    """Yuz okuma aktif edilecegi icin firaset ayri bir konu; sorgunun
    Marifetname'nin firaset bolumune gitmesi buna bagli."""
    assert "physiognomy" in detect_topics("Yüzümden mizacım okunur mu?", "tr")
    assert "physiognomy" in detect_topics("Firaset ne anlatır?", "tr")
    assert "physiognomy" in detect_topics("Can my face show my nature?", "en")

    sorgu = chart_query.build_query("Firaset ne anlatır?", OLGULAR, lang="tr")
    assert "Firaset" in sorgu and "kıyafet ilmi" in sorgu


def test_yuzden_kalibi_firaseti_tetiklemez():
    """"bu yüzden" / "onun yüzünden" Turkcede cok sik ve konuyla ilgisiz;
    bu yuzden "yüz" koku TEK BASINA tetikleyici degil."""
    for mesaj in ("bu yüzden çok yoruldum", "onun yüzünden geç kaldım",
                  "bu yüzden karar veremiyorum"):
        assert "physiognomy" not in detect_topics(mesaj, "tr"), mesaj


def test_harita_yoksa_mesajin_kendisi_kullanilir():
    """Dogum verisi girilmemis kullanicida davranis eskisiyle ayni kalir."""
    mesaj = "İşimle ilgili ne yapmalıyım?"
    assert chart_query.build_query(mesaj, None, lang="tr") == mesaj
    assert chart_query.build_query(mesaj, {}, lang="tr") == mesaj


def test_konu_bulunamazsa_sorgu_bos_kalmaz():
    """Mesaj her zaman sorguda oldugu icin bos sorgu ihtimali yok.

    Bu test eskiden bunun TERSINI iddia ediyordu: konu bulunamazsa haritanin
    buyuk uclusu eklensin diyordu. O davranis kaldirildi, cunku alakasiz
    yerlesimler asil soruyu boguyordu (bkz.
    test_konu_taninmazsa_harita_eklenmez).
    """
    mesaj = "bugün biraz tuhaf hissediyorum"
    sorgu = chart_query.build_query(mesaj, OLGULAR, lang="tr")
    assert sorgu == mesaj


def test_sorgu_odagini_kaybedecek_kadar_uzamaz():
    """Embedding tek bir vektore indirger: her fazladan ayrinti asil konuyu
    seyreltir."""
    for mesaj in ("İşimle ilgili ne yapmalıyım?",
                  "Şu an nasıl bir dönemdeyim?",
                  "işim ve ilişkim hakkında ne düşünüyorsun"):
        sorgu = chart_query.build_query(mesaj, OLGULAR, lang="tr")
        assert len(sorgu) < 400, f"sorgu {len(sorgu)} karaktere cikti"


def test_ayni_konuda_harita_kismi_kararlidir():
    """Sorgunun HARITA kismi ayni konuda ayni kalir; mesaj kismi degisir.

    Bu test eskiden sorgunun TAMAMININ ayni kalmasini bekliyordu ve bunu
    "sorgu embedding onbellegi artik calisiyor" diye bir kazanc sayiyordum.
    O kazanc gercek degildi: sorgular ayni cikiyordu cunku MESAJ ATILIYORDU
    (bkz. test_mesaj_sorguya_her_zaman_girer). Iki farkli soru ayni sorguyu
    uretiyorsa bu onbellek isabeti degil, bilgi kaybidir.
    """
    a = chart_query.build_query("İşimle ilgili ne yapmalıyım?", OLGULAR,
                                lang="tr")
    b = chart_query.build_query("İşim beni çok yoruyor", OLGULAR, lang="tr")
    assert a != b, "farkli mesajlar ayni sorguyu uretmemeli"

    # Mesajdan sonraki kisim (konu tohumu + harita) ayni olmali.
    assert a.split(". ", 1)[1] == b.split(". ", 1)[1]


def test_ham_dogum_verisi_sorguya_girmez():
    """Sorgu embedding API'sine gidiyor; ham dogum verisi disari cikmamali."""
    sorgu = chart_query.build_query("İşimle ilgili ne yapmalıyım?", OLGULAR,
                                    lang="tr")
    for yasak in ("1990", "Istanbul", "07:35", "08-14"):
        assert yasak not in sorgu
