"""Sohbet prompt düzenleyicisi — seçici RAG ve arka plan fısıltısı.

İki görev üstlenir:
1. should_use_rag: Kullanıcı mesajının bilgi tabanı (RAG) araması gerektirip
   gerektirmediğine sezgisel olarak karar verir. Selamlaşma, duygu paylaşımı
   ve kısa onaylarda RAG (ve dolayısıyla embedding çağrısı) atlanır — hem
   gecikme düşer hem de model gereksiz kaynak dökümünden uzak durur.
2. compose_chat_message: Bulunan pasajları prompta olduğu gibi boca etmek
   yerine, en fazla 2 pasajı kırpılmış birer "arka plan fısıltısı" olarak
   iliştirir ve modele bunları asla blok halinde aktarmamasını söyler.
"""
from __future__ import annotations

import re

from services import prompts

# Pasaj başına karakter sınırı ve en fazla pasaj sayısı.
#
# Bu iki sayı 13 parçalık, dil başına ~9 KB'lık bir korpus için konmuştu ve
# o zaman doğruydu: dönen pasaj çoğu zaman alakasızdı, alakasız metni
# büyütmek cevabı iyileştirmez, yalnızca pahalılaştırırdı.
#
# Üç şey değişti ve ölçüldü:
#   1. Korpus gerçek bir kitap taşıyor (Tetrabiblos, EN 136 / TR 33 parça).
#   2. Sorgu artık haritadan kuruluyor; dönen pasajlar 0,71–0,84 skorla
#      gerçekten ilgili (alakasız sorgular 0,49–0,56'da kalıyor).
#   3. 280 karakter, ortalama 907 karakterlik bir parçanın **%68'ini**
#      atıyordu — yani doğru bulunan pasajın üçte ikisi çöpe gidiyordu.
#
# 700 karakter parçanın büyük kısmını taşıyor. Sohbet turuna maliyeti
# ~210 token; harita bloğuyla birlikte bile Flash sınıfı bir modelde
# ihmal edilebilir.
#
# Pasaj SAYISI 2'de bırakıldı. Üçüncü kaynak odağı dağıtıyor ve persona
# zaten "en fazla tek bir ilgili ayrıntıyı kendi cümlene sindir" diyor;
# daha çok kaynak vermek modeli aktarmaya davet ediyor. Çeşitlilik kuralı
# sayesinde bu 2 pasaj zaten farklı bölümlerden geliyor.
MAX_PASSAGES = 2
MAX_PASSAGE_CHARS = 700

# Bilgi tabanının kapsadığı kadim sistem terimleri (kök bazlı, küçük harf).
# Mesajda bunlardan biri geçiyorsa korpus araması değerlidir.
#
# Terimler İKİ DİLDE birden aranır ve mesajın dili sorulmaz: liste yalnızca
# Türkçe olduğu sürece İngilizce yazan kullanıcı için RAG hiç tetiklenmiyordu
# ("what does my Mercury retrograde mean" korpusa hiç uğramıyordu). Fazladan
# arama maliyeti düşük, eksik arama ise cevabın kalitesini doğrudan düşürür.
_DOMAIN_TERMS = (
    # Türkçe
    "burc", "burç", "yükselen", "yukselen", "astroloji", "gezegen", "retro",
    "merkür", "merkur", "venüs", "venus", "jüpiter", "jupiter",
    "satürn", "saturn", "plüton", "pluton", "neptün", "neptun", "uranüs",
    "uranus", "natal", "harita", "transit", "sinastri", "nakshatra", "dasha",
    "bazi", "day master", "on tanrı", "on tanri", "heksagram", "i ching",
    "iching", "yin", "yang", "element", "mizaç", "mizac", "kıyafetname",
    "kiyafetname", "sima", "mian xiang", "yüz okuma", "yuz okuma", "ay evresi",
    "dolunay", "yeniay", "tutulma", "ev yerleş", "ev yerles", "açı", "orb",
    "koç", "boğa", "ikizler", "yengeç", "yengec", "aslan", "başak", "basak",
    "terazi", "akrep", "yay", "oğlak", "oglak", "kova", "balık",
    # İngilizce
    "zodiac", "sign", "rising", "ascendant", "astrolog", "planet",
    "retrograde", "mercury", "venus", "mars", "jupiter", "saturn", "pluto",
    "neptune", "uranus", "chart", "synastry", "hexagram", "horoscope",
    "house", "aspect", "conjunction", "sextile", "square", "trine",
    "opposition", "moon phase", "full moon", "new moon", "eclipse",
    "temperament", "four humours", "four humors", "physiognomy",
    "aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra",
    "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
)

# Derinlemesine açıklama isteyen soru kalıpları (tam kelime olarak aranır ki
# "nasılsın" içindeki "nasıl" tetiklemesin).
_QUESTION_WORDS = {
    "neden", "nasıl", "nasil", "niye", "anlat", "anlatır",
    "anlatir", "nedir", "açıkla", "acikla", "ne demek",
    "why", "how", "explain", "meaning", "means", "what",
}

# Selamlaşma / duygu / kısa onay işaretleri — RAG'e gerek yok.
_SMALL_TALK = {
    "selam", "merhaba", "günaydın", "gunaydin", "nasılsın",
    "nasilsin", "naber", "teşekkür", "tesekkur", "teşekkürler",
    "tesekkurler", "sağol", "sagol", "evet", "hayır", "hayir",
    "tamam", "peki", "olur", "harika", "süper", "super", "eyvallah",
    "keyifsiz", "üzgün", "uzgun", "mutlu", "yorgun", "moral",
    "canım", "canim", "sıkıldım", "sikildim", "iyiyim", "kötüyüm",
    "kotuyum", "görüşürüz", "gorusuruz", "iyi geceler",
    "hi", "hello", "hey", "thanks", "thank", "ok", "okay", "sure",
    "yes", "no", "great", "awesome", "bye", "goodnight", "tired",
    "sad", "happy", "lonely", "bored",
}


def normalize(message: str) -> str:
    """Küçük harfe indirger — Türkçe noktalı I'yı doğru ele alarak.

    Python'un `str.lower()` metodu Türkçe bilmez: ``"İ".lower()`` sonucu
    ``"i"`` DEĞİL, ``"i" + U+0307`` (birleşik nokta) olur. Sonuç sessiz bir
    bozulmaydı — "İşimle ilgili..." diye başlayan bir mesajda ``"iş"`` kökü
    hiç eşleşmiyor, yani RAG tetiklenmiyor ve kullanıcı kaynaksız cevap
    alıyordu. Aynı şekilde ``"I".lower()`` ``"i"`` verir, oysa Türkçede
    karşılığı ``"ı"``.

    Türkçe cümleler büyük harfle başladığı için bu, kenar durum değil —
    "İşim", "İlişkim", "İnsanlar" gibi en sık sorulan kelimeler tam da
    buradan düşüyordu.
    """
    return message.replace("İ", "i").replace("I", "ı").lower()


def _words(message: str) -> list[str]:
    return re.findall(r"[a-zçğıöşü]+", normalize(message))


#: Konu -> mesajda geçince o konuyu tetikleyen kökler.
#:
#: Eşleşme dile göre farklı çalışır ve bu bilinçli:
#:
#: **Türkçe: kelime BAŞI eşleşmesi.** Türkçe sondan eklemeli, yani "işim",
#: "işimle", "işten" hep "iş" ile başlar. Alt dizi araması denendi ve yanlış
#: eşleşti: "ilişkimde" kelimesinin içinde de "iş" geçiyor (il-**iş**-kimde)
#: ve ilişki sorusu meslek konusunu tetikliyordu.
#:
#: **İngilizce: alt dizi.** Ekler öne de gelir ("overthink" içinde "think");
#: kelime başı eşleşmesi bunları kaçırırdı.
_TOPIC_TRIGGERS = {
    "tr": {
        "vocation": ("iş", "meslek", "kariyer", "çalış", "patron", "terfi",
                     "mesai", "statü", "emek", "mesleğ"),
        "relationship": ("ilişki", "sevgili", "eş", "evli", "evlen", "aşk",
                         "partner", "ayrıl", "flört", "arkadaş", "dost",
                         "nişan", "boşan", "sevdiğ"),
        # S-turu: "para" ve "aile" hiç konu SAYILMIYORDU. Ölçüldü — "Para
        # konusunda hep aynı hatayı yapıyorum" ve "Babamla aram düzelmeyecek
        # mi" RAG'e hiç gitmiyordu, oysa korpusta artık doğrudan karşılığı
        # var (servet_doktrin.md, aile_doktrin.md).
        "money": ("para", "borç", "kazanç", "geçim", "birikim", "maaş",
                  "harca", "tasarruf", "gelir", "zengin", "fakir",
                  "yoksul", "servet"),
        "family": ("annem", "babam", "anneme", "babama", "annemle",
                   "babamla", "annesi", "babası", "ebeveyn", "kardeş",
                   "abim", "ablam", "kardeşim", "ailem", "ailesi",
                   "çocuğum", "evlad"),
        "mind": ("düşün", "kafam", "zihin", "odaklan", "karar", "anlam",
                 "öğren", "konsantr", "unut", "hafıza", "akıl", "akl"),
        "temperament": ("mizaç", "mizac", "huy", "karakter", "element",
                        "kişilik", "doğam", "yapım"),
        # "yüz" tek başına KULLANILMIYOR: "bu yüzden", "onun yüzünden" gibi
        # kalıplar Türkçede çok sık ve konuyla ilgisiz. Daha dar kökler ve
        # çok kelimeli kalıplar tercih edildi.
        "physiognomy": ("yüzüm", "suratım", "çehre", "sima", "firaset",
                        "kıyafetname", "yüz okuma", "yüz hat"),
        "travel": ("yolculuk", "seyahat", "taşın", "göç", "yurtdışı",
                   "uzağa", "şehir değiş"),
        # "bugün", "şimdi" gibi kelimeler BİLEREK yok: sıradan sohbette çok
        # sık geçiyorlar ve "bugün biraz keyifsizim" gibi bir duygu ifadesini
        # dönem sorusu sanmaya yol açıyorlardı.
        "timing": ("dönem", "transit", "ne zaman", "bu ara", "şu an",
                   "bu sıralar"),
    },
    "en": {
        "vocation": ("job", "work", "career", "profession", "boss",
                     "promotion", "employ", "vocation", "business",
                     "colleague", "office"),
        "relationship": ("relationship", "partner", "marri", "love",
                         "boyfriend", "girlfriend", "spouse", "dating",
                         "breakup", "friend", "divorce", "engaged"),
        # S-turu: "money" and "family" weren't topics at all. Measured —
        # "I keep making the same mistake with money" and "will things
        # ever be right with my father" never reached RAG, though the
        # corpus now has a direct answer (wealth_doctrine.md,
        # family_doctrine.md).
        "money": ("money", "debt", "income", "savings", "salary", "spend",
                  "afford", "broke", "wealth", "poor", "rich", "budget"),
        "family": ("my mother", "my father", "my mom", "my dad",
                   "my parent", "my sibling", "my brother", "my sister",
                   "my family", "my child", "my kid", "my son",
                   "my daughter"),
        "mind": ("think", "mind", "focus", "decide", "decision", "learn",
                 "memory", "understand", "concentrat"),
        "temperament": ("temperament", "character", "personality", "nature",
                        "element", "who i am"),
        "physiognomy": ("my face", "facial", "physiognom", "my looks",
                        "my features", "face reading", "appearance"),
        "travel": ("travel", "move abroad", "relocat", "journey", "emigrat",
                   "moving to"),
        # "when" ve "today" bilerek yok — İngilizcede her cümlede geçebilirler.
        "timing": ("right now", "period", "transit", "these days", "lately",
                   "at the moment"),
    },
}


def _topic_hits(message: str, dil: str, konu: str) -> int:
    kokler = _TOPIC_TRIGGERS[dil][konu]
    dusuk = normalize(message)
    kelimeler = _words(message)
    adet = 0
    for kok in kokler:
        if " " in kok or dil != "tr":
            adet += 1 if kok in dusuk else 0
        else:
            adet += 1 if any(k.startswith(kok) for k in kelimeler) else 0
    return adet


def detect_topics(message: str, lang: str | None = None) -> list[str]:
    """Mesajın hangi konu(lar)a değdiğini döndürür.

    Konu, bilgi tabanında karşılığı olan bir alan demektir; bu yüzden konu
    tespiti aynı zamanda "korpusta aranacak bir şey var" kanıtıdır
    (bkz. `should_use_rag`).
    """
    dil = lang if lang in _TOPIC_TRIGGERS else "tr"
    skorlar = [(_topic_hits(message, dil, konu), konu)
               for konu in _TOPIC_TRIGGERS[dil]]
    skorlar = sorted((s for s in skorlar if s[0]), key=lambda s: -s[0])
    # En fazla iki konu: üçüncüsü sorguyu odaksız hale getiriyor.
    return [konu for _, konu in skorlar[:2]]


def should_use_rag(message: str, lang: str | None = None) -> bool:
    """Mesaj kadim bilgi gerektiriyorsa True; selamlaşma/duygu/onay ise False."""
    lowered = normalize(message)
    words = _words(message)

    # Alan terimi geçiyorsa korpus her zaman değerli
    if any(term in lowered for term in _DOMAIN_TERMS):
        return True

    # Bilinen bir konuya değiyorsa korpusta karşılığı var demektir.
    #
    # Bu kapı olmadan "İşimle ilgili ne yapmalıyım?" RAG'e hiç uğramıyordu:
    # mesajda alan terimi yok, "ne yapmalıyım" derin soru kalıbı listesinde
    # değil ve mesaj 4 kelime olduğu için kısa sayılıp eleniyordu. Oysa
    # korpusta o soruya doğrudan cevap veren bir bölüm var.
    #
    # "timing" TEK BAŞINA yeterli sayılmaz: zaman kelimeleri duygu
    # paylaşımında da geçiyor ve tek başına korpusa gitmeyi haklı çıkarmıyor.
    # Gerçek bir dönem sorusu ("şu an nasıl bir dönemdeyim") zaten aşağıdaki
    # soru kalıbı kapısından geçer.
    if [k for k in detect_topics(message, lang) if k != "timing"]:
        return True

    # "neden/nasıl/anlat" gibi derin soru kalıpları (tam kelime eşleşmesi)
    if "ne demek" in lowered or any(w in _QUESTION_WORDS for w in words):
        return True

    # Kısa mesajlar ve bariz sohbet/duygu ifadeleri: RAG atla
    if len(words) <= 5:
        return False
    if any(w in _SMALL_TALK for w in words):
        return False

    # Alan terimi içermeyen serbest sohbet: korpusun katkısı düşük, atla
    return False


def compose_chat_message(message: str, passages: list[dict],
                         memory: str = "", chart: str = "",
                         sky: str = "", relationship: str = "",
                         lang: str | None = None) -> str:
    """Bilgi tabanı pasajlarını, kullanıcı hafızasını, haritasını ve bugünün
    gökyüzünü mesaja iliştirir.

    İkisi de "arka plan fısıltısı" olarak verilir: model bunları blok halinde
    aktarmaz, en fazla tek bir ilgili ayrıntıyı kendi cümlesine sindirir.
    Hafızayı olduğu gibi döktürmek, kullanıcıya "hakkında tuttuğum notlar"
    okumak gibi olur ve ürkütücüdür.

    ``relationship`` (R4-2): kullanıcı bir ARKADAŞ bağlamında soruyorsa
    sunucunun ölçtüğü ilişki eksenleri buradan girer. Cihaz bulgusuydu:
    bağlam olmadan model arkadaşı tanımadan kullanıcının kendi haritasından
    GENEL cevap uyduruyordu ("ikimiz özelinde cevap vermesi gerekirken").

    Hiçbiri yoksa mesaj olduğu gibi döner; API şeması ve model arayüzü değişmez.
    """
    whispers = []
    for passage in passages[:MAX_PASSAGES]:
        text = re.sub(r"\s+", " ", passage.get("text", "")).strip()
        if len(text) > MAX_PASSAGE_CHARS:
            text = text[:MAX_PASSAGE_CHARS].rsplit(" ", 1)[0] + "…"
        if text:
            whispers.append(f"- {text}")

    memory = (memory or "").strip()
    chart = (chart or "").strip()
    sky = (sky or "").strip()
    relationship = (relationship or "").strip()
    if (not whispers and not memory and not chart and not sky
            and not relationship):
        return message

    # Etiketler dile göre gelir: İngilizce sohbette Türkçe başlık görmek modeli
    # dil karıştırmaya iter.
    labels = prompts.get(lang)
    parts = []
    # İlişki bağlamı EN ÖNDE: soru o arkadaş hakkındaysa modelin merkezi
    # bu ölçüm olmalı, kullanıcının kendi haritası destekleyici kalmalı.
    if relationship:
        parts.append(labels.WHISPER_RELATIONSHIP + "\n" + relationship)
    if chart:
        parts.append(labels.WHISPER_CHART + "\n" + chart)
    if sky:
        parts.append(labels.WHISPER_SKY + "\n" + sky)
    if whispers:
        parts.append(labels.WHISPER_RAG + "\n" + "\n".join(whispers))
    if memory:
        parts.append(labels.WHISPER_MEMORY + "\n" + memory)

    return ("\n\n".join(parts)
            + f"\n\n{labels.USER_MESSAGE_LABEL}: {message}")
