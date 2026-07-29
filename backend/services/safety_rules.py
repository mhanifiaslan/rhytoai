"""Yasak alan kapısı — LLM'e hiç gitmeyen kesin engel.

Persona talimatındaki "sağlık/finans yorumu yapma" kuralı bir tavsiyedir; model
ona uyar ya da uymaz. Sağlık, hamilelik, ölüm ve finans gibi alanlarda yanlış
bir cümlenin bedeli yüksek olduğu için burada deterministik bir kapı var:
istek bu kalıplara uyuyorsa model çağrılmaz, sabit ve şeffaf bir yanıt döner.

**Kapı bilinçli olarak DARDIR.** Bir mesajın engellenmesi için hem bir YASAK
KONU hem de bir CEVAP TALEBİ işareti gerekir. Konunun tek başına geçmesi
yetmez — yoksa "annem hasta, çok üzgünüm" gibi bir duygu paylaşımı da
engellenirdi ve kullanıcı teselli aradığı anda duvara çarpardı. Bu, yasak
soruyu cevaplamaktan daha büyük bir hata olur.

İki işaret ayrı ayrı arandığı için sıraları önemli değil: "hastalığım geçecek
mi" ile "geçecek mi acaba hastalığım" aynı şekilde yakalanır.

İkinci savunma hattı persona talimatıdır (gemini_service); bu kapı yalnızca en
maliyetli hataları keser.
"""
from __future__ import annotations

import re

#: Türkçe soru eki, çekimli biçimleriyle: mı, mıyım, mısın, mıyız, mısınız...
#: Sadece "mı" aramak yetmiyor ("bırakmalı mıyım" yakalanmıyordu); sonuna
#: `\w{0,4}` koymak da "mimar" gibi kelimeleri yanlışlıkla yakalıyor.
_SORU = r"m[iuü](?:y[iuü]m|s[iuü]n(?:[iuü]z)?|y[iuü]z)?\b"

#: Cevap/öngörü talebi işaretleri. Bunlardan biri YOKSA mesaj engellenmez.
_TALEP = re.compile(
    _SORU
    + r"|olacak|olur mu|gecece|iyilesece|kurtulaca|yakalanaca"
    + r"|birakmali|ne zaman|yukselece|dusece|alsam|satsam|al[iı]r m"
    + r"|kac yil|ne kadar surece",
    re.IGNORECASE,
)


class _Rule:
    """Bir yasak alan: konu işareti + kullanıcıya dönecek yanıt."""

    def __init__(self, kategori: str, konu: str, yanit: str):
        self.kategori = kategori
        self.konu = re.compile(konu, re.IGNORECASE)
        self.yanit = yanit


#: Konu kalıpları normalize edilmiş metne (ı/İ -> i, küçük harf) uygulanır.
_RULES: list[_Rule] = [
    _Rule(
        "saglik",
        r"kanser|tumor|hastalik|hastaligim|teshis|tani\b|ameliyat|ilac"
        r"|tedavi|kisir|depresyon|hasta\b|hastayim|iyilesece",
        "Sağlıkla ilgili sorulara yıldızlardan cevap aramam doğru olmaz — "
        "bu konuda seni yanıltmak istemem. Böyle bir kaygın varsa bir hekimle "
        "konuşman en sağlıklısı. Başka bir şey sormak istersen buradayım.",
    ),
    _Rule(
        "hamilelik",
        r"hamile|gebe\b|bebegim|cocugum olacak|cocuk sahibi",
        "Çocuk sahibi olmak gibi bir konuda gökyüzüne dayanarak bir şey "
        "söylemem sana haksızlık olur. Bu soru bir hekimin alanı. "
        "İstersen bu dönemin genel temalarına bakabiliriz.",
    ),
    _Rule(
        "olum",
        r"olece|olurum|omrum|yasarim|yasar miyim|olum\b|vefat edece",
        "Ömür ve ölüm üzerine kehanette bulunmam. Bunu kimse bilemez ve "
        "bilirmiş gibi davranmak zarar verir. Aklını meşgul eden bir korku "
        "varsa onu konuşabiliriz.",
    ),
    _Rule(
        "finans",
        r"hisse|borsa|kripto|bitcoin|coin\b|doviz|dolar|euro\b|altin"
        r"|fon\b|portfoy|faiz",
        "Para ve yatırım kararlarında yıldızlara bakmak iyi bir fikir değil; "
        "sana yanlış bir güven vermek istemem. Bu konuda yetkili bir "
        "danışmana sormalısın. İşinin genel temalarına bakmak istersen olur.",
    ),
]


#: Türkçe harfleri ASCII'ye katlama tablosu.
#: Kalıplar ASCII yazılır, gelen metin buraya katlanır — aksi halde her kalıbı
#: "yasarim|yaşarım" gibi çift yazmak gerekir ve biri mutlaka atlanır.
_FOLD = str.maketrans({
    "ç": "c", "Ç": "c", "ğ": "g", "Ğ": "g",
    "ı": "i", "I": "i", "İ": "i", "i": "i",
    "ö": "o", "Ö": "o", "ş": "s", "Ş": "s",
    "ü": "u", "Ü": "u",
    # Bileşik noktalı i (aşağıdaki nota bakın)
    "̇": "",
})


def _normalize(text: str) -> str:
    """Metni ASCII'ye katlar ve küçük harfe indirir.

    Sıra önemli: Python'da ``"İ".lower()`` iki kodpuanlı ``i + U+0307`` üretir,
    yani önce küçültüp sonra "İ" aramak hiçbir zaman eşleşmez. Bu yüzden
    katlama küçültmeden ÖNCE yapılır; artakalan birleşen nokta da tabloda
    siliniyor.
    """
    return text.translate(_FOLD).lower().replace("̇", "")


def forbidden_topic(message: str) -> tuple[str, str] | None:
    """Mesaj yasak bir alanda cevap talep ediyorsa (kategori, yanıt) döner.

    Engelleme için iki koşul birlikte gerekir: yasak konu + cevap talebi.
    Eşleşme yoksa ``None`` — mesaj normal akışa devam eder.
    """
    if not message:
        return None

    hedef = _normalize(message)
    if not _TALEP.search(hedef):
        # Talep işareti yok: duygu paylaşımı, anlatı ya da genel sohbet.
        return None

    for rule in _RULES:
        if rule.konu.search(hedef):
            return rule.kategori, rule.yanit
    return None
