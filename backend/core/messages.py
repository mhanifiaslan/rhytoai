"""Kullanıcıya dönen hata ve kilit mesajları — dile göre.

Neden ayrı bir modül: istemci (`friendlyError`, apps/mobile/lib/core/api.dart)
sunucunun `detail` alanını **olduğu gibi** ekrana basar. Yani buradaki her
metin doğrudan kullanıcı arayüzüdür ve kullanıcının dilinde olmak zorundadır.
Faz 3'te uç yanıtları iki dile taşındı ama hata yolu Türkçe kalmıştı; İngilizce
kullanan biri kilitli bir ekrana geldiğinde Türkçe metin görüyordu.

İkinci kural burada uygulanır: **ham istisna metni kullanıcıya gösterilmez.**
Uçlar eskiden `detail=str(e)` döndürüyordu; bu hem anlaşılmaz (kullanıcı
"KeyError: 'sun'" görüyordu) hem de sunucunun iç yapısını dışarı sızdırıyordu.
Artık istisna sunucu tarafında loglanır, kullanıcıya sabit bir metin döner.
"""
from __future__ import annotations

import logging

from core.i18n import DEFAULT, SUPPORTED

logger = logging.getLogger(__name__)

#: anahtar -> {dil: metin}. İngilizce metinler Türkçenin birebir çevirisi
#: değildir; aynı bilgiyi o dilde doğal duran bir tonla verir.
_MESSAGES: dict[str, dict[str, str]] = {
    # --- Kimlik ---
    "auth_required": {
        "tr": "Devam etmek için oturum açman gerekiyor.",
        "en": "You need to be signed in to continue.",
    },
    "auth_invalid": {
        "tr": "Oturumun geçerliliğini yitirmiş. Lütfen tekrar giriş yap.",
        "en": "Your session is no longer valid. Please sign in again.",
    },

    # --- Abonelik kilidi (HTTP 402 -> istemci paywall açar) ---
    "paywall.personal_daily": {
        "tr": "Kişiye özel günlük okuma Rytho+ aboneliğine dahildir.",
        "en": "Your personalised daily reading is part of Rytho+.",
    },
    "paywall.natal_report": {
        "tr": "Derinlemesine doğum haritası raporu Rytho+ aboneliğine dahildir.",
        "en": "The in-depth birth chart report is part of Rytho+.",
    },
    "paywall.dyad": {
        "tr": "Arkadaşınla günlük ikili dinamik Rytho+ aboneliğine dahildir.",
        "en": "Your daily dynamic with a friend is part of Rytho+.",
    },
    "paywall.synastry": {
        "tr": "Sinastri raporu Rytho+ aboneliğine dahildir.",
        "en": "The synastry report is part of Rytho+.",
    },
    "paywall.bazi": {
        "tr": "BaZi analizi Rytho+ aboneliğine dahildir.",
        "en": "BaZi analysis is part of Rytho+.",
    },
    "paywall.default": {
        "tr": "Bu özellik Rytho+ aboneliğine dahildir.",
        "en": "This feature is part of Rytho+.",
    },

    # --- Günlük ücretsiz kota ---
    "quota.chat": {
        "tr": "Bugünlük ücretsiz sohbet hakkın doldu ({limit} mesaj). "
              "Rytho+ ile sınırsız konuşabilirsin.",
        "en": "You've used today's free messages ({limit}). "
              "Rytho+ removes the limit.",
    },
    "quota.iching": {
        "tr": "Bugünlük çekilişini yaptın. Yarın yeni bir heksagram seni "
              "bekliyor; Rytho+ ile istediğin kadar çekebilirsin.",
        "en": "You've cast today's hexagram. A new one waits tomorrow — "
              "or cast as often as you like with Rytho+.",
    },
    "quota.default": {
        "tr": "Bugünlük ücretsiz hakkın doldu.",
        "en": "You've used today's free allowance.",
    },

    # --- İkili dinamik ---
    "dyad.self": {
        "tr": "Kendinle ikili okuma yapılamaz.",
        "en": "A dyad reading needs two different people.",
    },
    "dyad.not_friends": {
        "tr": "Bu okuma yalnızca karşılıklı olarak eklenmiş arkadaşlar için "
              "üretilir.",
        "en": "This reading is only produced for people who have added each "
              "other as friends.",
    },
    "dyad.profile_missing": {
        "tr": "Okuma için gereken doğum kaydı bulunamadı.",
        "en": "The birth details needed for this reading are missing.",
    },

    # --- Genel ---
    "internal": {
        "tr": "Hesap yapılırken bir sorun çıktı. Lütfen biraz sonra tekrar dene.",
        "en": "Something went wrong while calculating this. Please try again "
              "in a moment.",
    },
    "llm_unavailable": {
        "tr": "Kozmik bağlantıda geçici bir parazit var; yıldız haritaların ve "
              "kadim kaynaklar her zamanki yerinde. Lütfen birkaç saniye sonra "
              "tekrar sor.",
        "en": "There's a little static on the line right now — your charts and "
              "the old sources are exactly where they were. Try again in a "
              "few seconds.",
    },
    "rate_limited": {
        "tr": "Gökyüzü biraz nefes istiyor: kısa sürede çok fazla istek "
              "gönderdin. Lütfen bir dakika sonra tekrar dene.",
        "en": "The sky needs a breath: that's a lot of requests in a short "
              "time. Please try again in a minute.",
    },
    "hexagram_not_found": {
        "tr": "Böyle bir heksagram yok (1-64 arası olmalı).",
        "en": "No such hexagram (it must be between 1 and 64).",
    },
}


def text(key: str, lang: str = DEFAULT, *, fallback: str | None = None,
         **biçim: object) -> str:
    """Anahtarın verilen dildeki karşılığı.

    Dil desteklenmiyorsa veya anahtar o dile henüz çevrilmemişse varsayılan
    dile düşer — eksik çeviri yüzünden istek patlamaz.

    ``fallback``: anahtar tabloda yoksa denenecek ikinci anahtar. Özelliğe
    özel paywall/kota metinleri için kullanılır (``paywall.dyad`` yoksa
    ``paywall.default``). O da yoksa genel hata metni döner; sessizce boş
    string dönmek, kullanıcıya boş bir hata kutusu göstermek olurdu.
    """
    if lang not in SUPPORTED:
        lang = DEFAULT

    seçenekler = _MESSAGES.get(key)
    if seçenekler is None and fallback is not None:
        seçenekler = _MESSAGES.get(fallback)
    if seçenekler is None:
        logger.warning("Bilinmeyen mesaj anahtarı: %s", key)
        seçenekler = _MESSAGES["internal"]

    metin = seçenekler.get(lang) or seçenekler.get(DEFAULT) or ""
    return metin.format(**biçim) if biçim else metin
