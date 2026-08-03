"""Sohbetten şemalı olgu çıkarımı — uygulamanın kullanıcıyı tanıma mekanizması.

Konuşmadan yalnızca `memory_service.CATEGORIES` içindeki kapalı kümeye
oturan kısa olgular damıtılır; prompt'a enjekte edilecek bağlam böylece
öngörülebilir boyutta kalır.

NOT (Revize R4): Bu dosyanın eski "Ham sohbet metni SAKLANMAZ" duruşu ürün
kararıyla revize edildi — konuşmalar artık konu bazlı arşivleniyor
(`chat_history.py`, 30 gün kullanılmayan silinir, gizlilik politikası
güncellendi). Bu çıkarıcı DEĞİŞMEDİ ve arşivin yerini tutmaz: arşiv
"kaldığın yerden devam", buradaki olgular "seni tanıyorum" — iki ayrı iş.

**Maliyet kontrolü:** çıkarım kullanıcı başına ek bir LLM çağrısıdır. Her
mesajda çalıştırılırsa sohbetin maliyeti ikiye katlanır. Bu yüzden iki şart
birlikte aranır: konuşmanın anlamlı bir uzunluğa gelmesi ve o gün daha önce
çıkarım yapılmamış olması. Böylece aktif kullanıcı başına günde en fazla bir
ek çağrı olur.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from core import entitlements
from services import gemini_service, memory_service

logger = logging.getLogger(__name__)

#: Çıkarımın tetiklenmesi için konuşmada en az kaç kullanıcı mesajı olmalı.
#: Kısa "merhaba" turlarından olgu çıkarmaya çalışmak boşa çağrıdır.
MIN_USER_TURNS = 3

#: Günlük çıkarım hakkı (kullanıcı başına). Kota altyapısı entitlements'ta.
DAILY_EXTRACTIONS = 1

#: Modelin döndürmesi gereken şema. response_schema ile zorlanır; yine de
#: dönen veri `memory_service` tarafından ayrıca doğrulanır — modele güvenip
#: şemasız yazmak, hafızayı serbest metin çöplüğüne çevirir.
_SCHEMA = {
    "type": "object",
    "properties": {
        "facts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "enum": list(memory_service.CATEGORIES)},
                    "key": {"type": "string"},
                    "value": {"type": "string"},
                    "confidence": {"type": "number"},
                },
                "required": ["category", "key", "value"],
            },
        },
        "mood": {"type": "string"},
    },
    "required": ["facts"],
}

_PROMPT = """\
GÖREV: Aşağıdaki konuşmadan kullanıcı hakkında KALICI olgular çıkar.

KURALLAR:
- Yalnızca kullanıcının KENDİSİ hakkında söylediği, ilerideki konuşmalarda
  işine yarayacak kalıcı bilgileri al.
- Geçici ayrıntıları ALMA (bugün yağmur yağmış, kahve içmiş gibi).
- Kullanıcının sorduğu soruları olgu sayma; yalnızca anlattıklarını.
- Astroloji verisi (burcu, yükseleni) ALMA — o zaten profilde var.
- Sağlık durumu, tanı veya ilaç bilgisi ALMA. Bu veriyi hiç tutmuyoruz.
- Her olgu en fazla bir cümle olsun.
- `key` sabit ve yeniden kullanılabilir bir anahtar olsun (ör. "work.transition",
  "relationship.status"); böylece aynı olgu sonradan güncellenebilir.
- `confidence`: kullanıcı açıkça söylediyse 0.9, ima ettiyse 0.5.
- Çıkarılacak kalıcı bir şey yoksa boş liste döndür. Uydurma.
- `mood`: kullanıcının bu konuşmadaki baskın ruh hali, tek kelime. Belirsizse
  boş bırak.

KATEGORİLER: {kategoriler}

KONUŞMA:
{konusma}
"""


def _conversation_text(history: list[dict[str, Any]], last_message: str) -> str:
    parts = []
    for item in history[-12:]:
        who = "Kullanıcı" if str(item.get("sender", "")).upper() == "USER" else "Rytho"
        text = str(item.get("text", "")).strip()
        if text:
            parts.append(f"{who}: {text}")
    parts.append(f"Kullanıcı: {last_message.strip()}")
    return "\n".join(parts)


def _user_turns(history: list[dict[str, Any]]) -> int:
    return sum(1 for i in history if str(i.get("sender", "")).upper() == "USER")


def should_extract(history: list[dict[str, Any]]) -> bool:
    """Konuşma olgu çıkarımına değecek kadar ilerledi mi?"""
    return _user_turns(history) + 1 >= MIN_USER_TURNS


def extract_and_store(uid: str, history: list[dict[str, Any]],
                      last_message: str) -> dict[str, Any] | None:
    """Konuşmadan olgu çıkarıp hafızaya yazar. Arka planda çağrılmak üzeredir.

    Hiçbir hata isteği etkilemez: çıkarım en iyi çaba (best effort) bir
    zenginleştirmedir, sohbetin çalışması ona bağlı değildir.
    """
    try:
        if not should_extract(history):
            return None

        # Günlük çıkarım kotası: aktif kullanıcı başına en fazla bir ek çağrı.
        if not entitlements.consume_quota(uid, "memory_extract", DAILY_EXTRACTIONS):
            return None

        prompt = _PROMPT.format(
            kategoriler=", ".join(memory_service.CATEGORIES),
            konusma=_conversation_text(history, last_message),
        )
        raw = gemini_service.extract_json(prompt, schema=_SCHEMA)
        if not raw:
            return None

        data = json.loads(raw)
        facts = data.get("facts") or []
        if not isinstance(facts, list):
            return None

        memory = memory_service.upsert_facts(uid, facts)

        mood = str(data.get("mood") or "").strip()
        if mood:
            memory_service.record_mood(uid, mood)

        logger.info("Hafıza güncellendi: uid=%s olgu=%d", uid, len(facts))
        return memory
    except Exception as exc:
        logger.warning("Olgu çıkarımı başarısız (%s): %s", uid, exc)
        return None
