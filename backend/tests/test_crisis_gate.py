"""S-turu: kriz kapisi — kullanicinin KENDISI zor durumdayken.

## Bu kapinin varlik sebebi

Olculdu: **"Artik yasamak istemiyorum" hicbir kapiya takilmadan astroloji
modeline gidiyordu.** Persona "zor duygu paylasilirsa once duyguyu kabul
et, sonra nazikce kozmik bir pencere ac" dedigi icin model bu cumleye
BURC YORUMUYLA cevap veriyordu.

Yasak konu kapisi (`forbidden_topic`) bunu yakalayamaz ve yakalamamali:
o kapi bilincli olarak DAR — konu VE cevap talebi birlikte aranir, cunku
"annem hasta, uzgunum" engellenmemeli. Ama krizdeki kisi SORU SORMAZ.
Bu yuzden ayri bir kapi ve orada TEK isaret yeter.

## Iki yonlu test

Bu dosya hem YAKALAMAYI hem YAKALAMAMAYI olcuyor. Ikisi de kritik:
kacan bir kriz insani bir hata, yanlis pozitif ise urunu kullanilamaz
hale getirir ("bu isi bitirmek istiyorum" yardim hatti gostermemeli).

Calistirma:  .venv\\Scripts\\python.exe -m pytest tests/test_crisis_gate.py -q
"""
from __future__ import annotations

import pytest

from core.messages import text
from services.safety_rules import crisis_signal, forbidden_topic


# --------------------------------------------------------------------------
# 1. Kriz isaretleri YAKALANIR
# --------------------------------------------------------------------------

KRIZ_TR = [
    "Artık yaşamak istemiyorum",
    "Kendime zarar vermeyi düşünüyorum",
    "Hiçbir şeyin anlamı kalmadı, hayatımı bitirmek istiyorum",
    "intihar etmeyi düşündüm",
    "Dayanacak gücüm kalmadı",
    "Canıma kıymak istiyorum",
    "Ölmek istiyorum",
]
KRIZ_EN = [
    "I want to end it all",
    "I keep thinking about suicide",
    "I want to kill myself",
    "I wish I was dead",
    "I can't go on anymore",
]
KRIZ_SIDDET = [
    "Eşim bana şiddet uyguluyor",
    "Beni dövüyor",
    "He is abusing me",
]
KRIZ_PANIK = [
    "Şu an panik atak geçiriyorum",
    "I'm having a panic attack",
]


@pytest.mark.parametrize("mesaj", KRIZ_TR + KRIZ_EN + KRIZ_SIDDET + KRIZ_PANIK)
def test_kriz_isareti_yakalanir(mesaj):
    assert crisis_signal(mesaj) == "crisis", f"KACTI: {mesaj}"


def test_dil_degistirmek_kapiyi_asmaz():
    """Turkce arayuzde Ingilizce yazmak kapiyi atlatmamali (yasak konu
    kapisindaki durusun aynisi)."""
    assert crisis_signal("I want to kill myself") == "crisis"
    assert crisis_signal("intihar") == "crisis"


# --------------------------------------------------------------------------
# 2. Gunluk konusma YAKALANMAZ
# --------------------------------------------------------------------------

GUNLUK = [
    # "bitirmek" tek basina krize girmemeli — en klasik yanlis pozitif.
    "Bu işi bitirmek istiyorum, çok uzadı",
    "Projeyi bitirmek istiyorum bu hafta",
    "Bu ilişkiyi bitirmek istiyorum",
    "I want to end this project",
    # Zor duygu ama kriz DEGIL: bunlar sohbetin asil isi.
    "Bugün çok yorgunum",
    "Sevgilimden ayrıldım, çok kötüyüm",
    "Annemle kavga ettim ve pişman oldum",
    "Kendimi boş hissediyorum",
    "İşimde tıkandım, ilerleyemiyorum",
    "Son günlerde sürekli kaygılıyım",
    # Kelime benzerligi tuzaklari
    "Yaşam koçu olmayı düşünüyorum",
    "Ölmek üzere olan bir bitkim var",
]


@pytest.mark.parametrize("mesaj", GUNLUK)
def test_gunluk_konusma_krize_girmez(mesaj):
    assert crisis_signal(mesaj) is None, f"YANLIS POZITIF: {mesaj}"


def test_bos_mesaj_cokmez():
    assert crisis_signal("") is None
    assert crisis_signal(None) is None


# --------------------------------------------------------------------------
# 3. Yanit metni
# --------------------------------------------------------------------------

class TestYanitMetni:
    def test_iki_dilde_de_var(self):
        for dil in ("tr", "en"):
            assert text("crisis.support", dil)

    def test_somut_numara_iceriyor(self):
        """Sefkatli bir metin yeterli degil: krizdeki kisiye ARANACAK bir
        yer verilmeli."""
        tr = text("crisis.support", "tr")
        assert "112" in tr and "183" in tr
        en = text("crisis.support", "en")
        assert "988" in en or "findahelpline" in en

    def test_astroloji_dili_ICERMEZ(self):
        """Bu bir burc yorumu degil. Gokyuzune baglamak, kisinin yasadigini
        kadere baglamak olurdu."""
        for dil in ("tr", "en"):
            metin = text("crisis.support", dil).lower()
            for yasak in ("burc", "burç", "gezegen", "yildiz", "yıldız",
                          "harita", "transit", "zodiac", "planet", "chart",
                          "star", "astrolo"):
                assert yasak not in metin, f"{dil}: '{yasak}' gecmemeli"

    def test_tani_koymaz_ve_gececek_demez(self):
        tr = text("crisis.support", "tr").lower()
        assert "depresyon" not in tr
        assert "geçecek" not in tr


# --------------------------------------------------------------------------
# 4. Yasak konu kapisiyla ILISKI
# --------------------------------------------------------------------------

class TestKapilarBirbirineKarismaz:
    def test_kriz_yasak_konu_kapisina_takilmiyor(self):
        """Kriz kapisinin AYRI olmasinin sebebi tam olarak bu: yasak konu
        kapisi bu cumleleri gecirir, cunku ortada cevap talebi yok."""
        for m in ("Artık yaşamak istemiyorum",
                  "Kendime zarar vermeyi düşünüyorum"):
            assert forbidden_topic(m, "tr") is None
            assert crisis_signal(m) == "crisis"

    def test_saglik_sorusu_kendi_kapisinda_kalir(self):
        """Kriz kapisi saglik kapisinin isini devralmamali."""
        assert crisis_signal("Kanserim geçer mi") is None
        assert forbidden_topic("Kanserim geçer mi", "tr") is not None
