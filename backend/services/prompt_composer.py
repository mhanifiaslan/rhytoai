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

# Pasaj başına karakter sınırı ve en fazla pasaj sayısı
MAX_PASSAGES = 2
MAX_PASSAGE_CHARS = 280

# Bilgi tabanının kapsadığı kadim sistem terimleri (kök bazlı, küçük harf).
# Mesajda bunlardan biri geçiyorsa korpus araması değerlidir.
_DOMAIN_TERMS = (
    "burc", "burç", "yükselen", "yukselen", "astroloji", "gezegen", "retro",
    "merkür", "merkur", "venüs", "venus", "mars", "jüpiter", "jupiter",
    "satürn", "saturn", "plüton", "pluton", "neptün", "neptun", "uranüs",
    "uranus", "natal", "harita", "transit", "sinastri", "nakshatra", "dasha",
    "bazi", "day master", "on tanrı", "on tanri", "heksagram", "i ching",
    "iching", "yin", "yang", "element", "mizaç", "mizac", "kıyafetname",
    "kiyafetname", "sima", "mian xiang", "yüz okuma", "yuz okuma", "ay evresi",
    "dolunay", "yeniay", "tutulma", "ev yerleş", "ev yerles", "açı", "orb",
    "koç", "boğa", "ikizler", "yengeç", "yengec", "aslan", "başak", "basak",
    "terazi", "akrep", "yay", "oğlak", "oglak", "kova", "balık",
)

# Derinlemesine açıklama isteyen soru kalıpları (tam kelime olarak aranır ki
# "nasılsın" içindeki "nasıl" tetiklemesin).
_QUESTION_WORDS = {"neden", "nasıl", "nasil", "niye", "anlat", "anlatır",
                   "anlatir", "nedir", "açıkla", "acikla", "ne demek"}

# Selamlaşma / duygu / kısa onay işaretleri — RAG'e gerek yok.
_SMALL_TALK = {"selam", "merhaba", "günaydın", "gunaydin", "nasılsın",
               "nasilsin", "naber", "teşekkür", "tesekkur", "teşekkürler",
               "tesekkurler", "sağol", "sagol", "evet", "hayır", "hayir",
               "tamam", "peki", "olur", "harika", "süper", "super", "eyvallah",
               "keyifsiz", "üzgün", "uzgun", "mutlu", "yorgun", "moral",
               "canım", "canim", "sıkıldım", "sikildim", "iyiyim", "kötüyüm",
               "kotuyum", "görüşürüz", "gorusuruz", "iyi geceler"}


def _words(message: str) -> list[str]:
    return re.findall(r"[a-zçğıöşü]+", message.lower())


def should_use_rag(message: str) -> bool:
    """Mesaj kadim bilgi gerektiriyorsa True; selamlaşma/duygu/onay ise False."""
    lowered = message.lower()
    words = _words(message)

    # Alan terimi geçiyorsa korpus her zaman değerli
    if any(term in lowered for term in _DOMAIN_TERMS):
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


def compose_chat_message(message: str, passages: list[dict]) -> str:
    """Pasajları kırpılmış arka plan fısıltısı olarak mesaja iliştirir.

    Pasaj yoksa mesaj olduğu gibi döner; API şeması ve model arayüzü değişmez.
    """
    if not passages:
        return message

    whispers = []
    for p in passages[:MAX_PASSAGES]:
        text = re.sub(r"\s+", " ", p.get("text", "")).strip()
        if len(text) > MAX_PASSAGE_CHARS:
            text = text[:MAX_PASSAGE_CHARS].rsplit(" ", 1)[0] + "…"
        if text:
            whispers.append(f"- {text}")

    if not whispers:
        return message

    return (
        "ARKA PLAN FISILTISI (yalnızca senin iç bilgin; kullanıcıya asla blok "
        "halinde aktarma, listeleme veya alıntılama — en fazla tek bir ilgili "
        "ayrıntıyı kendi cümlelerinle sohbetine sindir):\n"
        + "\n".join(whispers)
        + f"\n\nKULLANICININ MESAJI: {message}"
    )
