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

**Kapı her dilde kurulur ve mesaj TÜM dillerin kalıplarına karşı sınanır.**
Kalıplar yalnızca Türkçe olsaydı, uygulamayı İngilizce kullanan biri için
kapı hiç var olmazdı ("will my cancer get better?" doğrudan modele giderdi) —
ve dili değiştirmek kapıyı aşmanın yolu olurdu. Konu tespiti dilden
bağımsızdır; kullanıcıya dönen yanıt onun dilindedir.

Konu ile talep işaretinin **aynı dilden** olması gerekir: diller arası eşleşme
(Türkçe konu + İngilizce talep) gerçek bir cümlede neredeyse hiç oluşmaz ama
yanlış pozitif üretebilir.

İkinci savunma hattı persona talimatıdır (gemini_service); bu kapı yalnızca en
maliyetli hataları keser.
"""
from __future__ import annotations

import re

from core.i18n import DEFAULT, SUPPORTED

#: Türkçe soru eki, çekimli biçimleriyle: mı, mıyım, mısın, mıyız, mısınız...
#: Sadece "mı" aramak yetmiyor ("bırakmalı mıyım" yakalanmıyordu); sonuna
#: `\w{0,4}` koymak da "mimar" gibi kelimeleri yanlışlıkla yakalıyor.
_SORU_TR = r"m[iuü](?:y[iuü]m|s[iuü]n(?:[iuü]z)?|y[iuü]z)?\b"

#: Cevap/öngörü talebi işaretleri, dile göre. Biri YOKSA mesaj engellenmez.
_TALEP: dict[str, re.Pattern[str]] = {
    "tr": re.compile(
        _SORU_TR
        + r"|olacak|olur mu|gecece|iyilesece|kurtulaca|yakalanaca"
        + r"|birakmali|ne zaman|yukselece|dusece|alsam|satsam|al[iı]r m"
        + r"|kac yil|ne kadar surece",
        re.IGNORECASE,
    ),
    # İngilizcede soru eki yok; talep yardımcı fiil ve kalıplarla kurulur.
    # `\b` sınırları şart: "will" gibi parçalar başka kelimelerin içinde geçer.
    "en": re.compile(
        r"\bwill\b|\bwon't\b|\bshould i\b|\bshall i\b|\bam i\b|\bwas i\b"
        r"|\bis it\b|\bare they\b|\bdo i\b|\bdid i\b|\bcan i\b|\bcould i\b"
        r"|\bgoing to\b|\bwhen (?:will|do|does|should)\b|\bhow long\b"
        r"|\bhow many years\b|\bwhat are (?:my|the) chances\b"
        r"|\bpredict\b|\bforecast\b|\bshould i (?:buy|sell)\b",
        re.IGNORECASE,
    ),
}


class _Rule:
    """Bir yasak alan: dile göre konu işaretleri + dile göre yanıt.

    ``konu`` ve ``yanit`` sözlükleri dil koduyla anahtarlanır. Bir dil için
    konu kalıbı tanımlanmamışsa o dilde bu kural sınanmaz.
    """

    def __init__(self, kategori: str, konu: dict[str, str],
                 yanit: dict[str, str]):
        self.kategori = kategori
        self.konu = {dil: re.compile(kalip, re.IGNORECASE)
                     for dil, kalip in konu.items()}
        self.yanit = yanit


#: Konu kalıpları normalize edilmiş metne (ı/İ -> i, küçük harf) uygulanır.
#: İngilizce yanıtlar Türkçenin birebir çevirisi değil: aynı dürüst duruşu o
#: dilde doğal duran bir tonla kurar.
_RULES: list[_Rule] = [
    _Rule(
        "saglik",
        {
            "tr": r"kanser|tumor|hastalik|hastaligim|teshis|tani\b|ameliyat|ilac"
                  r"|tedavi|kisir|depresyon|hasta\b|hastayim|iyilesece",
            # "recover" / "get better" bilinçli olarak YOK: "will things get
            # better?" hayata dair sıradan bir soru ve engellenmesi kapıyı
            # aşırı geniş yapardı.
            "en": r"cancer|tumou?r|illness|disease|diagnos|surgery|operation"
                  r"|medication|medicine\b|treatment|chemo|infertil|depress"
                  r"|\bsick\b|\bill\b|symptom",
        },
        {
            "tr": "Sağlıkla ilgili sorulara yıldızlardan cevap aramam doğru "
                  "olmaz — bu konuda seni yanıltmak istemem. Böyle bir kaygın "
                  "varsa bir hekimle konuşman en sağlıklısı. Başka bir şey "
                  "sormak istersen buradayım.",
            "en": "I won't look to the sky for answers about health — I'd "
                  "rather not mislead you on something this important. If "
                  "this is weighing on you, a doctor is the right person to "
                  "talk to. I'm here for anything else.",
        },
    ),
    _Rule(
        "hamilelik",
        {
            "tr": r"hamile|gebe\b|bebegim|cocugum olacak|cocuk sahibi",
            "en": r"pregnan|conceiv|fertility|\bivf\b|having a baby"
                  r"|get pregnant|expecting a (?:baby|child)",
        },
        {
            "tr": "Çocuk sahibi olmak gibi bir konuda gökyüzüne dayanarak bir "
                  "şey söylemem sana haksızlık olur. Bu soru bir hekimin "
                  "alanı. İstersen bu dönemin genel temalarına bakabiliriz.",
            "en": "It wouldn't be fair to you if I answered a question about "
                  "having children from a chart. That belongs with a doctor. "
                  "If you'd like, we can look at the broader themes of this "
                  "period instead.",
        },
    ),
    _Rule(
        "olum",
        {
            "tr": r"olece|olurum|omrum|yasarim|yasar miyim|olum\b|vefat edece",
            "en": r"\bdie\b|\bdying\b|\bdeath\b|pass away|passing away"
                  r"|how long (?:do|will) i (?:have|live)|life ?span"
                  r"|when will i die",
        },
        {
            "tr": "Ömür ve ölüm üzerine kehanette bulunmam. Bunu kimse bilemez "
                  "ve bilirmiş gibi davranmak zarar verir. Aklını meşgul eden "
                  "bir korku varsa onu konuşabiliriz.",
            "en": "I don't make predictions about death or how long someone "
                  "will live. No one knows that, and pretending otherwise "
                  "does harm. If there's a fear sitting with you, we can talk "
                  "about that instead.",
        },
    ),
    _Rule(
        "finans",
        {
            "tr": r"hisse|borsa|kripto|bitcoin|coin\b|doviz|dolar|euro\b|altin"
                  r"|fon\b|portfoy|faiz",
            # Somut araçlarla sınırlı. Yalın "invest" veya "shares" YOK:
            # "should I invest more time in this?" ya da "he shares my
            # feelings" finans sorusu değil.
            "en": r"\bstocks?\b|stock market|share price|crypto|bitcoin"
                  r"|\bcoin\b|\bforex\b|exchange rate|\bdollars?\b|\beuros?\b"
                  r"|\bgold\b|\bfund\b|portfolio|interest rate",
        },
        {
            "tr": "Para ve yatırım kararlarında yıldızlara bakmak iyi bir "
                  "fikir değil; sana yanlış bir güven vermek istemem. Bu "
                  "konuda yetkili bir danışmana sormalısın. İşinin genel "
                  "temalarına bakmak istersen olur.",
            "en": "Looking to the stars for money decisions isn't a good "
                  "idea, and I don't want to give you false confidence. A "
                  "licensed advisor is the right place for this. I'm happy to "
                  "look at the broader themes around your work instead.",
        },
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


def forbidden_topic(message: str, lang: str = DEFAULT) -> tuple[str, str] | None:
    """Mesaj yasak bir alanda cevap talep ediyorsa (kategori, yanıt) döner.

    Engelleme için iki koşul birlikte gerekir: yasak konu + cevap talebi, ve
    ikisi aynı dilin kalıplarından gelmelidir. Mesaj desteklenen tüm dillere
    karşı sınanır; ``lang`` yalnızca dönen yanıtın dilini belirler.

    Eşleşme yoksa ``None`` — mesaj normal akışa devam eder.
    """
    if not message:
        return None

    hedef = _normalize(message)

    # Talep işareti taşıyan diller. Hiçbiri yoksa mesaj bir soru değil:
    # duygu paylaşımı, anlatı ya da genel sohbet.
    talep_dilleri = [dil for dil, kalip in _TALEP.items() if kalip.search(hedef)]
    if not talep_dilleri:
        return None

    yanit_dili = lang if lang in SUPPORTED else DEFAULT

    for rule in _RULES:
        for dil in talep_dilleri:
            kalip = rule.konu.get(dil)
            if kalip is not None and kalip.search(hedef):
                yanit = rule.yanit.get(yanit_dili) or rule.yanit[DEFAULT]
                return rule.kategori, yanit
    return None
