"""Haritadan RAG sorgusu üretme.

Sorun neydi: bilgi tabanı araması **kullanıcının cümlesiyle** yapılıyordu.
Biri "işimle ilgili ne yapmalıyım?" yazdığında korpusta bu cümleye benzeyen
bir şey aranıyordu — kadim metinde öyle bir cümle yok. Dönen pasaj ya
alakasız oluyordu ya hiç dönmüyordu. Korpus 900 parçaya çıksa bile bu böyle
kalırdı: aranan şey yanlıştı, arama değil.

Artık kullanıcının haritasını biliyoruz (`chart_context`). Aynı soru için
gerçek sorgu şudur:

    Mesleğin niteliği, statü, geçim. Satürn: Oğlak (10. ev) ·
    Mars: Boğa (9. ev). Güneş Kare Mars. Transit Satürn → Güneş Karşıt.

Bu, korpustan **o kişiye ait** pasajı çeker. Faz A (harita derinliği) ile
Faz C (kitap) ancak burada birleşiyor.

## Üç tasarım kararı

**Konu eşlemesi LLM'e sordurulmuyor.** Küçük ve denetlenebilir bir tablo
kullanılıyor. LLM'e sormak hem her sohbet turuna bir çağrı daha eklerdi hem
de sonucu belirsiz kılardı; tablo yanlış eşleşirse görülebilir ve düzeltilir.

**Sorgu korpusun dilinde kurulur.** Korpus dile göre ayrı (`corpus/tr`,
`corpus/en`) ve `base_for(lang)` hangisinde arayacağını dilden seçiyor. Bu
yüzden gezegen/burç adları da o dile çevrilir — İngilizce korpusta "Satürn"
aramak, aramanın yarısını boşa harcamak olurdu.

**Yan fayda: önbellek isabeti artıyor.** Sorgu embedding'i sorgu metnine göre
önbellekleniyordu ve ham kullanıcı mesajları neredeyse hiç tekrar etmediği
için önbellek çalışmıyordu. Haritadan kurulan sorgu ise aynı kullanıcı + aynı
konu için AYNI metni üretir; embedding çağrısı (sohbet turuna ~1 sn ekleyen
kısım) ikinci soruda atlanır.
"""
from __future__ import annotations

import re

from services import prompts
from services.prompt_composer import detect_topics

#: Konu -> o konunun bilgi tabanındaki karşılığını çeken tohum kelimeler.
#: Bunlar korpustaki bölüm başlıklarıyla eşleşecek şekilde seçildi; sorgunun
#: anlamsal yönünü belirleyen kısım burası.
_TOPIC_SEEDS = {
    "tr": {
        "vocation": "Mesleğin niteliği, iş, statü, rütbe",
        "relationship": "Evlilik, ortaklık, bağ, dostluk",
        "mind": "Aklın niteliği, düşünme biçimi, muhakeme",
        "temperament": "Mizaç, bedenin biçimi, dört element dengesi",
        "physiognomy": ("Firaset, kıyafet ilmi, dış belirtiden mizaca; "
                        "yüz hatları, ses ve duruş"),
        "travel": "Yolculuk, yer değiştirme, kökten uzaklaşma",
        "timing": "Yaklaşma ve ayrılma, transit, açının kurulması",
        "self": "Yükselen derece, kişinin kendi doğası",
    },
    "en": {
        "vocation": "The quality of employment, work, rank, station",
        "relationship": "Marriage, partnership, friendship, bonds",
        "mind": "The quality of the mind, manner of thinking, judgement",
        "temperament": "Temperament, form of the body, balance of elements",
        "physiognomy": ("Firasa, the science of physiognomy, from outward "
                        "sign to temperament; facial features, voice, bearing"),
        "travel": "Travelling, journeys, leaving one's own ground",
        "timing": "Application and separation, transit, an aspect forming",
        "self": "The degree ascending, a person's own nature",
    },
}

#: Konu -> haritanın hangi parçasına bakılacağı.
#:
#: Ev eşlemeleri geleneksel: meslek 10. ev, ortaklık 7., yolculuk 9., kişinin
#: kendisi 1. Gezegen eşlemeleri Batlamyus'un kendi tarifinden geliyor
#: (meslek Merkür/Mars/Venüs, akıl Merkür/Ay, ortaklık Venüs/Ay/Güneş).
_TOPIC_FACTORS: dict[str, dict[str, tuple]] = {
    "vocation": {"planets": ("Mercury", "Mars", "Venus", "Saturn"),
                 "houses": (10, 6, 2)},
    "relationship": {"planets": ("Venus", "Moon", "Sun", "Mars"),
                     "houses": (7, 5, 11)},
    "mind": {"planets": ("Mercury", "Moon"), "houses": (3, 9)},
    "temperament": {"planets": ("Sun", "Moon", "Saturn", "Mars", "Jupiter"),
                    "houses": (1,)},
    # Firaset bedeni okur; gelenekte beden birinci evin işidir. Yükselen ve
    # oradaki gezegenler, mizaç belirleyicileriyle aynı kümeye düşer.
    "physiognomy": {"planets": ("Sun", "Moon", "Mars", "Venus", "Saturn"),
                    "houses": (1,)},
    "travel": {"planets": ("Moon", "Jupiter"), "houses": (9, 3, 4)},
    "timing": {"planets": (), "houses": ()},
    "self": {"planets": ("Sun", "Moon"), "houses": (1,)},
}

#: Sorguya girecek en fazla yerleşim / açı / transit satırı. Sorgu uzadıkça
#: anlamsal odak dağılır: embedding tek bir vektöre indirgediği için her
#: fazladan ayrıntı asıl konuyu seyreltir.
_MAX_PLACEMENTS = 4
_MAX_ASPECTS = 2
_MAX_TRANSITS = 1

#: Konu bulunamazsa kullanılacak varsayılan. "self" en genel olanı ve
#: haritanın büyük üçlüsünü taşır.
_DEFAULT_TOPIC = "self"


def _lang_key(lang: str | None) -> str:
    return lang if lang in _TOPIC_SEEDS else "tr"


def _placement_text(lang: str | None, y: dict) -> str:
    ad = prompts.planet_name(lang, y["planet"])
    burc = prompts.sign_name(lang, y["sign"])
    ev = y.get("house")
    if isinstance(ev, int):
        return f"{ad} {burc} {prompts.get(lang).HOUSE_FMT.format(house=ev)}"
    return f"{ad} {burc}"


def _relevant_placements(facts: dict, konular: list[str]) -> list[dict]:
    """Konulara göre öne çıkan yerleşimler.

    Hem gezegen hem ev üzerinden seçilir: "meslek" sorusunda hem Merkür/Mars
    (Batlamyus'un meslek belirleyicileri) hem de 10. evde ne varsa alınır.
    """
    gezegenler: set[str] = set()
    evler: set[int] = set()
    for konu in konular:
        faktor = _TOPIC_FACTORS.get(konu, {})
        gezegenler.update(faktor.get("planets", ()))
        evler.update(faktor.get("houses", ()))

    tumu = [y for y in (facts.get("sun"), facts.get("moon")) if y]
    tumu += facts.get("placements") or []

    secilen = [y for y in tumu
               if y["planet"] in gezegenler or y.get("house") in evler]
    # Hiçbiri tutmazsa haritanın omurgası verilir; boş sorgudan iyidir.
    if not secilen:
        secilen = tumu[:2]
    return secilen[:_MAX_PLACEMENTS]


def _relevant_aspects(facts: dict, konular: list[str]) -> list[dict]:
    gezegenler: set[str] = set()
    for konu in konular:
        gezegenler.update(_TOPIC_FACTORS.get(konu, {}).get("planets", ()))

    acilar = facts.get("aspects") or []
    ilgili = [a for a in acilar
              if a["p1"] in gezegenler or a["p2"] in gezegenler]
    # Konuyla ilgili açı yoksa en sıkı açı yine anlamlı: haritanın en baskın
    # gerilimi her konuya sızar.
    return (ilgili or acilar)[:_MAX_ASPECTS]


def build_query(message: str, facts: dict | None,
                lang: str | None = None) -> str:
    """Mesaj + haritadan bilgi tabanı sorgusu kurar.

    Harita yoksa (doğum verisi girilmemiş) mesajın kendisi döner — davranış
    eskisiyle aynı kalır, sohbet bozulmaz.
    """
    if not facts:
        return message

    dil = _lang_key(lang)
    konular = detect_topics(message, lang)

    # Konu tanınmadıysa harita EKLENMEZ, mesaj olduğu gibi aranır.
    #
    # Konuyu bilmemek, hangi olguların ilgili olduğunu bilmemek demektir;
    # o durumda haritayı yine de eklemek sorguyu alakasız yerleşimlerle
    # dolduruyor ve asıl soruyu boğuyordu. Ölçülen örnek: "Bugün hangi
    # gezegenin günü?" ham hâliyle doğru bölümü buluyordu (Günlerin ve
    # Saatlerin Yöneticileri, 0,75); büyük üçlü + açılar eklenince o
    # bölüm listeden düşüyor ve yerine genel gezegen pasajları geliyordu.
    #
    # Kişiye özel olmayan bir soru için kişiye özel bağlam eklemek
    # kişiselleştirme değil, gürültüdür.
    if not konular:
        return re.sub(r"\s+", " ", message).strip() or message

    # Mesajın kendisi sorgunun ÖNÜNDE durur ve asla atılmaz.
    #
    # İlk sürümde mesaj tamamen değiştiriliyordu (yalnızca konu tohumu +
    # harita) ve bu iki şeyi birden bozuyordu:
    #
    #   1. Konu eşleşmediğinde sorgu HER SORU İÇİN AYNI oluyordu.
    #      "Bugün hangi gezegenin günü?" ile "Ayın menzili ne demek?"
    #      birebir aynı sorgu metnini üretiyor, dolayısıyla aynı pasajları
    #      getiriyordu.
    #   2. Konu eşleşse bile mesajın kendi içeriği kayboluyordu:
    #      "YÜZÜMDEN mizacım okunur mu?" sorusunda "yüzümden" düşüyor ve
    #      firaset bölümü yerine genel mizaç bölümü geliyordu.
    #
    # Doğru bölüşüm şu: mesaj NEYİN sorulduğunu, harita KİMİN sorduğunu
    # taşır. İkisi de gerekli.
    parcalar = [re.sub(r"\s+", " ", message).strip()]
    parcalar += [_TOPIC_SEEDS[dil][k] for k in konular
                 if k in _TOPIC_SEEDS[dil]]

    yerlesimler = _relevant_placements(facts, konular)
    if yerlesimler:
        parcalar.append(", ".join(_placement_text(lang, y)
                                  for y in yerlesimler))

    acilar = _relevant_aspects(facts, konular)
    if acilar:
        parcalar.append(", ".join(
            f"{prompts.planet_name(lang, a['p1'])} "
            f"{prompts.aspect_name(lang, a['aspect'])} "
            f"{prompts.planet_name(lang, a['p2'])}" for a in acilar))

    # Transitler yalnızca zamanla ilgili sorularda: her sorguya eklemek
    # bugünün gökyüzünü kalıcı bir karakter özelliği gibi ağırlıklandırırdı.
    if "timing" in konular:
        for t in (facts.get("transits") or [])[:_MAX_TRANSITS]:
            parcalar.append(
                f"{prompts.planet_name(lang, t['transit'])} "
                f"{prompts.aspect_name(lang, t['aspect'])} "
                f"{prompts.planet_name(lang, t['natal'])}")

    # Element/nitelik dengesi yalnızca mizaç sorusunda: sayı dizisi anlamsal
    # aramada gürültüdür, konuyla doğrudan ilgili olmadıkça eklenmez.
    if "temperament" in konular:
        p = prompts.get(lang)
        elementler = facts.get("elements") or {}
        baskin = max(elementler, key=elementler.get) if elementler else None
        if baskin:
            parcalar.append(p.ELEMENT_NAMES[baskin])

    sorgu = ". ".join(x for x in parcalar if x)
    return re.sub(r"\s+", " ", sorgu).strip() or message
