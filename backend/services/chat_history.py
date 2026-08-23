"""Sohbet arşivi — konu bazlı, sunucu yazımlı, süreli (Revize R4).

## Politika değişikliği — açıkça

Bu modül, `memory_extractor.py` başındaki "Ham sohbet metni SAKLANMAZ"
duruşunun ÜRÜN KARARIYLA revizyonudur. Kullanıcı isteği: konuşmalar konu
konu saklansın, kaldığı yerden sürdürülebilsin (diğer AI uygulamaları
gibi). Gizlilik politikası (legal_texts.dart) aynı fazda güncellendi;
mağaza formları R9 listesinde.

Duruşun korunan yarısı: serbest metne İSTEMCİ yazamaz (rules'ta
conversations `write: false`) — yazan tek el burası, moderasyon kapısının
ARKASI. Engellenen konular ne düşülür ne saklanır.

## Sınırlar

* Kullanıcı başına **20 konu** — yenisi açılırken en eskisi silinir.
* Konu başına **400 mesaj** — dolunca sunucu devam konusu açar; istemci
  dönen kimliği izlediği için kesintisiz sürer.
* Mesaj **2000 karakter** — kırpılır, 422 atılmaz (uzun yazan kullanıcının
  mesajını reddetmek yerine kısaltmak; LLM bağlam penceresi de zaten
  sınırlı).
* `expireAt` her mesajda 30 gün ileri itilir: kullanılan konu yaşar,
  bırakılan konu zamanlanmış temizlikte silinir (bkz. api/maintenance.py).
"""
from __future__ import annotations

import datetime as dt
import logging
from typing import Any

from core import firestore as firestore_client

logger = logging.getLogger(__name__)

MAX_CONVERSATIONS = 20
MAX_MESSAGES_PER_CONVERSATION = 400
MAX_MESSAGE_CHARS = 2000
RETENTION_DAYS = 30
TITLE_CHARS = 60

#: Prompt'a giren geçmişin tavanları (K4 — maliyet üst sınırı).
#:
#: Arşiv kırpması (MAX_MESSAGE_CHARS) ile prompt kırpması AYRI işler:
#: arşivde 2.000 karakter saklanır (kullanıcı kendi mesajını tam görür),
#: prompt'a ise son 12 mesaj × 1.200 karakter girer. Eski hâlde en kötü
#: tur girdisi ~18 bin token'a çıkabiliyordu (20 × 2.000 kr geçmiş);
#: tavanla ~9 bin token'ın altına iner ve tur başına LLM maliyeti her
#: koşulda yarılanır. 12 mesaj ≈ 6 soru-cevap turu — konuşma bağlamı
#: için yeterli; daha eski bağlam zaten hafıza özetinden geliyor.
PROMPT_HISTORY_MESSAGES = 12
PROMPT_MESSAGE_CHARS = 1200


def _conversations(client, uid: str):
    return (client.collection("users").document(uid)
            .collection("conversations"))


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def clip_message(text: str) -> str:
    """Mesajı üst sınıra kırpar — reddetmek yerine."""
    return text[:MAX_MESSAGE_CHARS]


def clip_for_prompt(text: str) -> str:
    """Prompt'a giren geçmiş mesajını maliyet tavanına kırpar (K4)."""
    return text[:PROMPT_MESSAGE_CHARS]


def title_from(text: str) -> str:
    """Konu başlığı = ilk kullanıcı mesajının başı. LLM YOK: başlık için
    ücretli bir çağrı yapmak, maliyet ilkesinin tam tersi olurdu."""
    tek_satir = " ".join(text.split())
    if len(tek_satir) <= TITLE_CHARS:
        return tek_satir
    return tek_satir[:TITLE_CHARS - 1].rstrip() + "…"


def _evict_oldest_if_needed(client, uid: str) -> None:
    """20. konudan sonrasını (en eskiyi) mesajlarıyla birlikte siler."""
    koleksiyon = _conversations(client, uid)
    try:
        konular = list(koleksiyon.order_by("updatedAt", direction="DESCENDING")
                       .offset(MAX_CONVERSATIONS - 1).stream())
    except Exception as exc:
        logger.warning("Konu tahliyesi sorgusu düştü (%s): %s", uid, exc)
        return
    for konu in konular:
        _delete_conversation_doc(koleksiyon.document(konu.id))


def _delete_conversation_doc(conv_ref) -> int:
    """Mesajlar ÖNCE, konu SONRA: ters sıra yarıda kalırsa yetim mesaj
    bırakır (sonsuza dek faturalanır, sahibi silemez)."""
    silinen = 0
    try:
        for parti in _batches(conv_ref.collection("messages")):
            for anlik in parti:
                anlik.reference.delete()
                silinen += 1
        conv_ref.delete()
    except Exception as exc:
        logger.warning("Konu silinemedi: %s", exc)
    return silinen


def _batches(collection, page: int = 200):
    while True:
        docs = list(collection.limit(page).stream())
        if not docs:
            return
        yield docs
        if len(docs) < page:
            return


class PreparedConversation:
    """Senkron çözülmüş konu hedefi.

    İki aşamalı tasarımın sebebi: yanıt `conversation_id` DÖNDÜRMEK zorunda
    (istemci onu izliyor) ama mesaj yazımı arka planda — kullanıcı Firestore
    yazımını beklememeli. Kimlik çözümü ucuz (tek okuma; yeni kimlik üretimi
    Firestore'da YEREL, ağa çıkmaz), yazım pahalı kısım.
    """

    def __init__(self, conversation_id: str, create: bool,
                 title_prefix: str | None, message_count: int,
                 friend_uid: str | None = None,
                 person_id: str | None = None):
        self.conversation_id = conversation_id
        self.create = create
        self.title_prefix = title_prefix
        self.message_count = message_count
        #: KA7: konuya yapışmış bağlam. İstemci konuşmayı listeden yeniden
        #: açınca friend/person kimliğini geri gönderemiyordu ve bağlam
        #: KALICI kayboluyordu; artık konu dokümanında durur ve `prepare`
        #: mevcut okumadan bedavaya geri getirir.
        self.friend_uid = friend_uid
        self.person_id = person_id


def prepare(uid: str, requested_id: str | None) -> PreparedConversation | None:
    """Turun yazılacağı konuyu SENKRON çözer; Firestore yoksa `None`.

    Üç durum:
    * kimlik yok            → yeni konu (yerel üretilen kimlik)
    * kimlik var + yer var  → devam
    * kimlik var ama DOLU   → devam konusu (yeni kimlik, başlık "eski ↪")
    """
    client = firestore_client.get_client()
    if client is None:
        return None

    try:
        koleksiyon = _conversations(client, uid)
        if requested_id:
            anlik = koleksiyon.document(requested_id).get()
            if anlik.exists:
                veri = anlik.to_dict() or {}
                adet = int(veri.get("messageCount", 0))
                if adet + 2 <= MAX_MESSAGES_PER_CONVERSATION:
                    return PreparedConversation(
                        requested_id, False, None, adet,
                        friend_uid=veri.get("friendUid"),
                        person_id=veri.get("personId"))
                # Konu doldu: devam konusu. İstemci dönen kimliği izlediği
                # için konuşma kesintisiz sürer; eski konu arşivde kalır.
                # Bağlam da devam konusuna taşınır.
                return PreparedConversation(
                    koleksiyon.document().id, True,
                    str(veri.get("title", "")), 0,
                    friend_uid=veri.get("friendUid"),
                    person_id=veri.get("personId"))
            # İstemcinin elindeki kimlik silinmiş (temizlik/tahliye): aynı
            # kimliğe YENİ doküman kurulur, istemci fark etmez.
            return PreparedConversation(requested_id, True, None, 0)
        return PreparedConversation(koleksiyon.document().id, True, None, 0)
    except Exception as exc:
        logger.warning("Konu çözülemedi (%s): %s", uid, exc)
        return None


def write_turn(uid: str, prepared: PreparedConversation,
               user_text: str, ai_text: str, lang: str,
               friend_uid: str | None = None,
               person_id: str | None = None) -> None:
    """Bir soru-cevap turunu arşive yazar — arka plan görevi.

    Başarısızlık yanıtı etkilemez; yalnızca o tur arşivden düşer.

    ``friend_uid``/``person_id`` (KA7): turun etkin bağlamı. Konu
    dokümanına yazılır ki listeden yeniden açılan konuşma bağlamını
    KAYBETMESİN (`prepare` geri getirir). Bağlam sonradan da gelebilir
    (kullanıcı konuşmanın ortasında kişi ekranından dönerse) — bu yüzden
    yalnız oluşturmada değil, doluysa her turda yazılır.
    """
    client = firestore_client.get_client()
    if client is None:
        return

    try:
        koleksiyon = _conversations(client, uid)
        conv_ref = koleksiyon.document(prepared.conversation_id)
        simdi = _now()
        son_kullanim = simdi + dt.timedelta(days=RETENTION_DAYS)

        if prepared.create:
            _evict_oldest_if_needed(client, uid)
            baslik = (f"{prepared.title_prefix} ↪" if prepared.title_prefix
                      else title_from(user_text))
            kayit = {
                "title": baslik,
                "createdAt": simdi,
                "updatedAt": simdi,
                "messageCount": 0,
                "expireAt": son_kullanim,
                "lang": lang,
            }
            if friend_uid:
                kayit["friendUid"] = friend_uid
            if person_id:
                kayit["personId"] = person_id
            conv_ref.set(kayit)

        mesajlar = conv_ref.collection("messages")
        # AI damgasına mikro fark: aynı anda yazılan çift, createdAt
        # sıralamasında yer değiştirmesin.
        mesajlar.document().set({
            "sender": "USER", "text": clip_message(user_text),
            "createdAt": simdi,
        })
        mesajlar.document().set({
            "sender": "AI", "text": ai_text,
            "createdAt": simdi + dt.timedelta(milliseconds=1),
        })
        guncelleme = {
            "updatedAt": simdi,
            "messageCount": prepared.message_count + 2,
            "expireAt": son_kullanim,
        }
        if friend_uid:
            guncelleme["friendUid"] = friend_uid
        if person_id:
            guncelleme["personId"] = person_id
        conv_ref.set(guncelleme, merge=True)
    except Exception as exc:
        # Arşiv yazımı yanıtın parçası değil; düşerse yalnızca loglanır.
        logger.warning("Sohbet arşivine yazılamadı (%s): %s", uid, exc)


def delete_conversation(uid: str, conversation_id: str) -> int:
    """Konuyu mesajlarıyla siler; silinen mesaj adedini döndürür."""
    client = firestore_client.get_client()
    if client is None:
        raise RuntimeError("Firestore erisilemiyor")
    conv_ref = _conversations(client, uid).document(conversation_id)
    if not conv_ref.get().exists:
        return 0
    return _delete_conversation_doc(conv_ref)


def purge_expired(limit: int = 300, dry_run: bool = False) -> dict[str, int]:
    """Süresi geçmiş konuşmaları siler (zamanlanmış temizlik çağırır).

    Native Firestore TTL BİLEREK kullanılmıyor: TTL yalnızca konu
    dokümanını siler, `messages/*` alt koleksiyonu YETİM kalır — sonsuza
    dek faturalanır ve `write: false` kuralı yüzünden sahibi de silemez.
    """
    client = firestore_client.get_client()
    if client is None:
        raise RuntimeError("Firestore erisilemiyor")

    sorgu = (client.collection_group("conversations")
             .where("expireAt", "<", _now()).limit(limit))
    konular = 0
    mesajlar = 0
    for anlik in sorgu.stream():
        konular += 1
        if dry_run:
            continue
        mesajlar += _delete_conversation_doc(anlik.reference)

    logger.info("Sohbet temizliği: konu=%d mesaj=%d dry_run=%s",
                konular, mesajlar, dry_run)
    return {"conversations": konular, "messages": mesajlar}
