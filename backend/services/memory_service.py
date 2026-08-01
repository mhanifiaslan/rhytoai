"""Kullanıcı hafızası — sohbetten damıtılan kalıcı, şemalı olgular.

Uygulamanın "kullanıcıyı tanıması" natal veriden değil, zamanla biriken bu
katmandan gelir. Bu yüzden **ham sohbet metni saklanmaz**; yalnızca sınırlı bir
kategori kümesine oturan, kısa ve güncellenebilir olgular tutulur. Böylece hem
gizlilik yüzeyi küçük kalır hem de prompt'a enjekte edilecek bağlam öngörülebilir
boyutta olur.

Şema (Firestore: ``users/{uid}/private/memory`` tek doküman):

```
{
  "version": 1,
  "facts": [
    {"category": "work", "key": "work.transition",
     "value": "yeni bir işe geçme ihtimalini tartıyor",
     "confidence": 0.8, "updatedAt": <ts>}
  ],
  "moodTrail": [{"date": "2026-07-28", "mood": "kaygılı", "note": "..."}],
  "toneHint": "kısa ve doğrudan yanıt tercih ediyor",
  "updatedAt": <ts>
}
```

Bu modülde yalnızca **şema ve okuma/yazma API'si** vardır. Olguların sohbetten
çıkarılması Faz 4'te `prompt_composer` ile birlikte eklenecek.

Firestore erişilemezse tüm okumalar boş hafıza döner ve yazmalar sessizce
yok sayılır — hafıza katmanı hiçbir koşulda isteği düşürmez.
"""
from __future__ import annotations

import datetime as dt
import logging
from typing import Any

from core import firestore as firestore_client

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 1

#: Olguların oturabileceği kategoriler. Serbest kategori kabul edilmez —
#: çıkarım katmanı bu listeye uymak zorundadır.
#:
#: Sağlık bilinçli olarak yoktur: sağlık/hastalık yorumu ürünün yasak
#: alanlarındandır, dolayısıyla o veriyi saklamak da istemiyoruz.
CATEGORIES = (
    "relationship",   # ilişki durumu ve tekrar eden ilişki temaları
    "work",           # iş / kariyer bağlamı
    "family",         # aile bağlamı
    "goal",           # kullanıcının dile getirdiği hedefler
    "concern",        # tekrar eden kaygılar
    "preference",     # ton, uzunluk, hitap tercihleri
    "milestone",      # kullanıcının önemsediği tarihler
)

#: Sınırlar — hem Firestore doküman boyutu hem prompt bütçesi için.
MAX_FACTS = 40
MAX_FACT_CHARS = 240
MAX_MOOD_ENTRIES = 30
MAX_TONE_CHARS = 200

_EMPTY: dict[str, Any] = {
    "version": SCHEMA_VERSION,
    "facts": [],
    "moodTrail": [],
    "toneHint": None,
}


def _doc(uid: str):
    """Kullanıcının hafıza dokümanı; Firestore yoksa ``None``.

    ``private`` alt koleksiyonu altında tutulur: istemcinin bu veriye doğrudan
    erişmesi gerekmiyor, yalnızca sunucu (Admin SDK) okur/yazar.
    """
    client = firestore_client.get_client()
    if client is None:
        return None
    return client.collection("users").document(uid).collection("private").document("memory")


def get_memory(uid: str) -> dict[str, Any]:
    """Kullanıcının hafızasını döndürür; yoksa boş şema."""
    doc_ref = _doc(uid)
    if doc_ref is None:
        return dict(_EMPTY)
    try:
        snapshot = doc_ref.get()
    except Exception as exc:
        logger.warning("Hafıza okunamadı (%s): %s", uid, exc)
        return dict(_EMPTY)

    if not snapshot.exists:
        return dict(_EMPTY)

    data = snapshot.to_dict() or {}
    return {
        "version": data.get("version", SCHEMA_VERSION),
        "facts": data.get("facts", []),
        "moodTrail": data.get("moodTrail", []),
        "toneHint": data.get("toneHint"),
    }


def _normalize_fact(fact: dict[str, Any]) -> dict[str, Any] | None:
    """Tek bir olguyu şemaya oturtur; kategorisi tanınmıyorsa ``None``."""
    category = str(fact.get("category", "")).strip().lower()
    if category not in CATEGORIES:
        return None

    value = str(fact.get("value", "")).strip()
    if not value:
        return None

    key = str(fact.get("key", "")).strip() or f"{category}.{abs(hash(value)) % 10**6}"

    try:
        confidence = float(fact.get("confidence", 0.5))
    except (TypeError, ValueError):
        confidence = 0.5

    return {
        "category": category,
        "key": key,
        "value": value[:MAX_FACT_CHARS],
        "confidence": min(max(confidence, 0.0), 1.0),
        "updatedAt": dt.datetime.now(dt.timezone.utc),
    }


def _prune_facts(facts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sınır aşıldığında önce düşük güvenli, sonra eski olguları düşürür."""
    if len(facts) <= MAX_FACTS:
        return facts
    epoch = dt.datetime.min.replace(tzinfo=dt.timezone.utc)
    ordered = sorted(
        facts,
        key=lambda f: (f.get("confidence", 0.0), f.get("updatedAt") or epoch),
        reverse=True,
    )
    return ordered[:MAX_FACTS]


def upsert_facts(uid: str, facts: list[dict[str, Any]]) -> dict[str, Any]:
    """Olguları ``key`` üzerinden birleştirir (aynı anahtar güncellenir).

    Şemaya uymayan olgular sessizce atılır. Güncellenmiş hafızayı döndürür.
    """
    normalized = [n for n in (_normalize_fact(f) for f in facts) if n is not None]
    memory = get_memory(uid)
    if not normalized:
        return memory

    by_key = {f.get("key"): f for f in memory["facts"]}
    for fact in normalized:
        by_key[fact["key"]] = fact

    memory["facts"] = _prune_facts(list(by_key.values()))
    _write(uid, memory)
    return memory


def record_mood(uid: str, mood: str, note: str = "") -> None:
    """Günlük ruh hali izini ekler (gün başına tek kayıt; aynı gün üzerine yazar)."""
    mood = mood.strip()[:60]
    if not mood:
        return

    memory = get_memory(uid)
    today = dt.date.today().isoformat()
    trail = [entry for entry in memory["moodTrail"] if entry.get("date") != today]
    trail.append({"date": today, "mood": mood, "note": note.strip()[:MAX_FACT_CHARS]})
    memory["moodTrail"] = trail[-MAX_MOOD_ENTRIES:]
    _write(uid, memory)


def set_tone_hint(uid: str, hint: str) -> None:
    """Kullanıcının tercih ettiği anlatım tonunu kaydeder."""
    memory = get_memory(uid)
    memory["toneHint"] = hint.strip()[:MAX_TONE_CHARS] or None
    _write(uid, memory)


def memory_context(uid: str, max_chars: int = 600) -> str:
    """Hafızayı prompt'a iliştirilebilecek kompakt bir özete indirger.

    Faz 4'te `prompt_composer` bunu "arka plan fısıltısı" olarak kullanacak;
    bilgi tabanı pasajlarında olduğu gibi modele blok halinde aktarılmaz.
    """
    memory = get_memory(uid)
    parts: list[str] = []

    for fact in sorted(memory["facts"],
                       key=lambda f: f.get("confidence", 0.0), reverse=True):
        parts.append(f"- ({fact['category']}) {fact['value']}")

    trail = memory["moodTrail"][-5:]
    if trail:
        moods = ", ".join(f"{e['date']}: {e['mood']}" for e in trail)
        parts.append(f"- (ruh hali seyri) {moods}")

    if memory.get("toneHint"):
        parts.append(f"- (ton tercihi) {memory['toneHint']}")

    context = ""
    for part in parts:
        if len(context) + len(part) + 1 > max_chars:
            break
        context += part + "\n"
    return context.strip()


def delete_memory(uid: str) -> None:
    """Kullanıcının tüm hafızasını siler.

    Hesap silme akışının (KVKK/GDPR ve mağaza zorunluluğu) parçasıdır.
    """
    doc_ref = _doc(uid)
    if doc_ref is None:
        return
    try:
        doc_ref.delete()
    except Exception as exc:
        logger.warning("Hafıza silinemedi (%s): %s", uid, exc)


def _write(uid: str, memory: dict[str, Any]) -> None:
    doc_ref = _doc(uid)
    if doc_ref is None:
        return
    try:
        doc_ref.set({
            "version": SCHEMA_VERSION,
            "facts": memory["facts"],
            "moodTrail": memory["moodTrail"],
            "toneHint": memory.get("toneHint"),
            "updatedAt": dt.datetime.now(dt.timezone.utc),
        })
    except Exception as exc:
        logger.warning("Hafıza yazılamadı (%s): %s", uid, exc)
