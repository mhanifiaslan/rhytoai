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
    # S-turu: kullanıcının konuşulmasını İSTEMEDİĞİ konu. "Bunu konuşmak
    # istemiyorum" bir kez söylenir ve kalıcı olmalı; her açılışta aynı
    # yaraya dokunmak "seni tanıyorum" değil, tam tersi.
    "sensitivity",
)

#: Sınırlar — hem Firestore doküman boyutu hem prompt bütçesi için.
MAX_FACTS = 40
MAX_FACT_CHARS = 240
MAX_MOOD_ENTRIES = 30
MAX_TONE_CHARS = 200

#: Günlük (R2-G1) sınırları. Girdiler KULLANICININ kendi cümleleridir
#: ("bugün patronumla tartıştım") — tek satır, tarih damgalı, temalı.
#: Analizin "astrolojik günlük" fikri: kullanıcı yaşadığını yazar, sohbet
#: "son bir ayda ne oldu?" sorusunu bu kayıtlar + gökyüzüyle cevaplar.
MAX_DIARY_ENTRIES = 90
MAX_DIARY_CHARS = 200

#: Günlük girişinin bağlanabileceği temalar — sinyal temalarıyla AYNI küme
#: (signal_service.THEMES); tema vermeden de yazılabilir.
DIARY_THEMES = ("career", "relationships", "inner", "finance")

_EMPTY: dict[str, Any] = {
    "version": SCHEMA_VERSION,
    "facts": [],
    "moodTrail": [],
    "toneHint": None,
    "diary": [],
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
        "diary": data.get("diary", []),
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


#: Ruh hali yoğunluğu (S-turu). Tek kelimelik ruh hali yetmiyordu: "biraz
#: kaygılıyım" ile "dağılmak üzereyim" aynı satıra düşüyor ve model ikisine
#: de aynı tonda cevap veriyordu.
INTENSITIES = ("low", "medium", "high")

#: Kullanıcının o turda ARADIĞI şey. Aynı soru farklı ihtiyaçla sorulabilir:
#: "ne yapmalıyım" bazen yön ister, bazen sadece anlaşılmak.
NEEDS = ("information", "direction", "understanding", "rest")


def record_mood(uid: str, mood: str, note: str = "",
                intensity: str = "", needs: str = "") -> None:
    """Günlük ruh hali izini ekler (gün başına tek kayıt; aynı gün üzerine yazar).

    ``intensity`` ve ``needs`` (S-turu) isteğe bağlı: tanınmayan değer
    sessizce düşer — modelin uydurduğu bir etiket şemaya giremez.
    """
    mood = mood.strip()[:60]
    if not mood:
        return

    memory = get_memory(uid)
    today = dt.date.today().isoformat()
    trail = [entry for entry in memory["moodTrail"] if entry.get("date") != today]
    kayit: dict[str, Any] = {
        "date": today, "mood": mood,
        "note": note.strip()[:MAX_FACT_CHARS],
    }
    if intensity in INTENSITIES:
        kayit["intensity"] = intensity
    if needs in NEEDS:
        kayit["needs"] = needs
    trail.append(kayit)
    memory["moodTrail"] = trail[-MAX_MOOD_ENTRIES:]
    _write(uid, memory)


def set_tone_hint(uid: str, hint: str) -> None:
    """Kullanıcının tercih ettiği anlatım tonunu kaydeder."""
    memory = get_memory(uid)
    memory["toneHint"] = hint.strip()[:MAX_TONE_CHARS] or None
    _write(uid, memory)


# ---------------------------------------------------------------------------
# Günlük (R2-G1)
# ---------------------------------------------------------------------------

def add_diary_entry(uid: str, text: str, theme: str | None = None,
                    date: str | None = None) -> dict[str, Any] | None:
    """Tek satırlık günlük girişi ekler; eklenen girişi döndürür.

    Kimlik zaman damgasından türetilir (silme ucu bununla adresler).
    Metin boşsa ya da tema tanınmıyorsa None döner — uydurma tema yazılmaz.
    """
    text = text.strip()[:MAX_DIARY_CHARS]
    if not text:
        return None
    if theme is not None:
        theme = str(theme).strip().lower()
        if theme not in DIARY_THEMES:
            return None

    simdi = dt.datetime.now(dt.timezone.utc)
    giris = {
        "id": f"d{int(simdi.timestamp() * 1000)}",
        "date": date or simdi.date().isoformat(),
        "text": text,
        "theme": theme,
    }
    memory = get_memory(uid)
    memory["diary"] = (memory["diary"] + [giris])[-MAX_DIARY_ENTRIES:]
    _write(uid, memory)
    return giris


def delete_diary_entry(uid: str, entry_id: str) -> bool:
    """Girişi kimliğiyle siler; bulunamadıysa False."""
    memory = get_memory(uid)
    kalan = [g for g in memory["diary"] if g.get("id") != entry_id]
    if len(kalan) == len(memory["diary"]):
        return False
    memory["diary"] = kalan
    _write(uid, memory)
    return True


def get_diary(uid: str) -> list[dict[str, Any]]:
    """Günlük girişleri, yeniden eskiye."""
    return sorted(get_memory(uid)["diary"],
                  key=lambda g: (g.get("date") or "", g.get("id") or ""),
                  reverse=True)


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

    # Ruh hali SEYRİ — tek fotoğraf değil eğilim (S-turu). Yoğunluk da
    # yazılıyor: modelin "üç gündür ağırlaşıyor" ile "dün biraz yorgundu"
    # arasındaki farkı görmesi, tonunu ona göre kurmasının tek yolu.
    trail = memory["moodTrail"][-5:]
    if trail:
        def _yaz(e: dict[str, Any]) -> str:
            metin = f"{e['date']}: {e['mood']}"
            if e.get("intensity"):
                metin += f"({e['intensity']})"
            return metin
        parts.append("- (ruh hali seyri) " + ", ".join(_yaz(e) for e in trail))
        # En son turda kullanıcının ne aradığı, tonun en güçlü ipucu.
        son = trail[-1]
        if son.get("needs"):
            parts.append(f"- (son turda aradığı) {son['needs']}")

    # Günlük (R2-G1): son girişler sohbetin gözüne girer — "son ayda ne
    # oldu?" sorusu bu satırlar + gökyüzü verisiyle cevaplanabilir.
    gunluk = memory.get("diary") or []
    for g in gunluk[-6:]:
        parts.append(f"- (günlük {g.get('date')}) {g.get('text')}")

    if memory.get("toneHint"):
        parts.append(f"- (ton tercihi) {memory['toneHint']}")

    # `continue`, `break` DEĞİL (KA9): eski döngü sığmayan İLK parçada
    # duruyordu — olgular bütçeyi doldurunca ruh hali seyri, günlük ve
    # ton tercihi TAMAMEN düşüyordu (hepsi olgulardan sonra geliyor).
    # Şimdi sığmayan parça atlanır, sonraki kısa parçalar yine girer.
    # Tek parça tek başına bütçeden büyükse ve henüz hiçbir şey
    # eklenmediyse kelime sınırından kırpılır — hafıza fısıltısı hiç
    # boş kalmasın.
    context = ""
    for part in parts:
        kalan = max_chars - len(context) - 1
        if len(part) > kalan:
            if not context and kalan > 40:
                context += part[:kalan].rsplit(" ", 1)[0] + "…\n"
            continue
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
            "diary": memory.get("diary", []),
            "updatedAt": dt.datetime.now(dt.timezone.utc),
        })
    except Exception as exc:
        logger.warning("Hafıza yazılamadı (%s): %s", uid, exc)
