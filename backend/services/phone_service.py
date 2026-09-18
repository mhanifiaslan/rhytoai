"""Telefon numarası eşleme kaydı — hash tabanlı, sunucu yazımlı.

## Güven zinciri

Numara istemcinin BEYANI değil: Firebase Phone Auth SMS doğrulamasını
bitirir, numara ID token'ına `phone_number` claim'i olarak girer ve buraya
`AuthUser.phone` üzerinden gelir. İstemciden numara parametresi ALINMAZ —
alınsaydı herkes istediği numarayı "doğrulanmış" gösterebilirdi.

## Neden hash, neden sunucuda

Rehber eşleşmesi (R3) iki tarafın numara HASH'lerini karşılaştırır; ham
numara Firestore'a hiç yazılmaz (Firebase Auth kendi içinde zaten tutuyor;
ikinci bir kopya yeni bir sızıntı yüzeyi olurdu). Hash SUNUCUDA hesaplanır:
istemciler farklı normalizasyon yapsaydı aynı numara iki farklı hash'e
düşer ve eşleşme sessizce çalışmazdı. Firebase E.164 verdiği için
normalizasyon derdi de yok.

## Yazılan yerler

* ``phoneHashes/{hash}`` = ``{uid, createdAt}`` — benzersizlik + eşleşme
  dizini. İstemciye tamamen kapalı (rules'ta match bloğu yok → varsayılan
  red); tek yazan Admin SDK.
* ``users/{uid}/private/phone`` = ``{hash, updatedAt}`` — ters bakış:
  numara değişince eski hash'i serbest bırakmak için. `private/**` zaten
  kapalı ve hesap silinince temizleniyor.

`users/{uid}` ana dokümanına BİLEREK yazılmıyor: oradaki `hasOnly` kuralı
sonuç dokümanı denetler ve sunucunun eklediği alan, istemcinin sonraki tüm
merge yazımlarını düşürürdü — `faceConsent` bunu bir kez yaşattı.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import logging

from core import firestore as firestore_client

logger = logging.getLogger(__name__)


def phone_hash(e164: str) -> str:
    """E.164 numaranın SHA-256'sı. Girdi Firebase'den geldiği için zaten
    normalize; yine de boşluk kırpılır."""
    return hashlib.sha256(e164.strip().encode("utf-8")).hexdigest()


class PhoneTakenError(Exception):
    """Numara başka bir hesaba kayıtlı."""


def sync_phone(uid: str, e164: str) -> dict:
    """Doğrulanmış numarayı eşleme dizinine yazar.

    İdempotent: aynı kullanıcı aynı numarayla tekrar çağırırsa hiçbir şey
    değişmez. Kullanıcının ÖNCEKİ numarası varsa eski hash serbest kalır
    (kullanıcı adı deseninin aynısı).
    """
    client = firestore_client.get_client()
    if client is None:
        raise RuntimeError("Firestore erisilemiyor")

    yeni_hash = phone_hash(e164)
    hash_ref = client.collection("phoneHashes").document(yeni_hash)
    ozel_ref = (client.collection("users").document(uid)
                .collection("private").document("phone"))

    mevcut = hash_ref.get()
    if mevcut.exists:
        sahibi = (mevcut.to_dict() or {}).get("uid")
        if sahibi == uid:
            return {"linked": True, "changed": False}
        # Bir numara TEK hesaba bağlanır. Aksi halde rehber eşleşmesi aynı
        # numara için iki kişi döndürür ve "hangi hesap benim arkadaşım"
        # sorusu cevapsız kalır.
        raise PhoneTakenError(sahibi)

    onceki = ozel_ref.get()
    eski_hash = ((onceki.to_dict() or {}).get("hash")
                 if onceki.exists else None)

    simdi = dt.datetime.now(dt.timezone.utc)
    hash_ref.set({"uid": uid, "createdAt": simdi})
    ozel_ref.set({"hash": yeni_hash, "updatedAt": simdi})

    if eski_hash and eski_hash != yeni_hash:
        try:
            client.collection("phoneHashes").document(eski_hash).delete()
        except Exception as exc:
            # Kritik değil: sarkan eski hash yalnızca eşleşmede yanlış
            # pozitif üretebilir ve numaranın yeni sahibi kaydolunca ezilir.
            logger.warning("Eski telefon hash'i silinemedi (%s): %s", uid, exc)

    logger.info("Telefon eşleme kaydı güncellendi: uid=%s", uid)
    return {"linked": True, "changed": eski_hash != yeni_hash}


def release_phone(uid: str) -> None:
    """Hesap silinirken numara dizin kaydını serbest bırakır."""
    client = firestore_client.get_client()
    if client is None:
        return
    try:
        ozel_ref = (client.collection("users").document(uid)
                    .collection("private").document("phone"))
        anlik = ozel_ref.get()
        h = (anlik.to_dict() or {}).get("hash") if anlik.exists else None
        if h:
            client.collection("phoneHashes").document(h).delete()
    except Exception as exc:
        logger.warning("Telefon kaydı serbest bırakılamadı (%s): %s", uid, exc)

# Teşhis kaydında tutulan aşamalar. Serbest metin kabul edilmez: istemci
# ne gönderirse göndersin kayda yalnız bunlar girer.
ATTEMPT_STAGES = {"sent", "failed", "auto", "verified"}


def _maske_kirp(masked: str) -> str:
    """Maskenin SON HANELERİNİ atar: "+90532***4567" → "+90532***".

    ⚠️ Kapalı test denetiminde (2026-09-18) bulundu: ilk 3 + *** + son 4
    biçiminde 10 haneli bir numaranın yalnızca ÜÇ hanesi gizliydi, yani
    kayıt pratikte numaranın kendisiydi. Teşhiste işe yarayan kısım son
    haneler değil ÜLKE + OPERATÖR ÖNEKİ; onu tutup gerisini atıyoruz.

    Kırpma neden sunucuda: alanı istemci gönderiyor ve sahadaki eski
    sürümler tam maskeyi göndermeye devam ediyor. İstemciyi düzeltmek
    onları kapsamaz, burası kapsar.

    Yıldız yoksa istemci maskelemeden göndermiş demektir (ham numara
    olabilir): o değer HİÇ yazılmaz.
    """
    ham = (masked or "")[:24]
    yildiz = ham.find("*")
    return f"{ham[:yildiz]}***" if yildiz > 0 else ""


def record_attempt(uid: str, stage: str, iso2: str, masked: str,
                   code: str | None = None) -> None:
    """SMS doğrulama denemesini teşhis için yazar (best-effort).

    Neden var (2026-09-08 canlı olayı): bir kullanıcı SMS alamadı ve
    Google tarafında her şey sağlıklı görünüyordu — istek 200 döndü, SMS
    faturalandı, engellenmedi. Ama "numara doğruydu da operatör mü
    düşürdü, yoksa numara yanlış mı derlendi" sorusunu AYIRT EDEMEDİK,
    çünkü gönderdiğimiz numarayı hiçbir yere yazmıyorduk.

    Yazılan yalnızca ÜLKE KODU + OPERATÖR ÖNEKİDİR ("+90532***"): istemci
    tam maskeyi ("+90532***4567") yollasa bile son haneler `_maske_kirp`
    ile atılır. Sebep: son dört hane maskeyi üç hanelik bir arama uzayına
    indiriyordu — maskeli numara da kişisel veridir. Ham numara Firestore'a
    hiç girmez; hash dizini doktrini (`sync_phone`) bozulmaz.

    Asla fırlatmaz: telemetri doğrulama akışını düşüremez.
    """
    if stage not in ATTEMPT_STAGES:
        return
    try:
        client = firestore_client.get_client()
        if client is None:
            return
        client.collection("phoneAttempts").document().set({
            "uid": uid,
            "stage": stage,
            "iso2": (iso2 or "")[:2].upper(),
            "masked": _maske_kirp(masked),
            "code": (code or "")[:64] or None,
            "at": dt.datetime.now(dt.timezone.utc),
        })
    except Exception as exc:  # pragma: no cover - telemetri
        logger.warning("Telefon denemesi yazilamadi (%s): %s", uid, exc)
