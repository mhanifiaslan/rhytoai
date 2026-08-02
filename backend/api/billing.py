"""Abonelik uclari: RevenueCat webhook'u ve istemci icin durum sorgusu.

Abonelik durumunun **tek yazma yolu** buradaki webhook'tur. Istemci kendi
abonelik kaydini yazamaz (``users/{uid}/private/**`` Firestore kurallarinda
istemciye kapalidir), cunku aksi halde ucretli icerik istemci tarafindan
acilabilirdi.

RevenueCat'in `app_user_id` alani Firebase uid'sidir; istemci satin alma
oncesi `Purchases.logIn(uid)` cagirir.
"""
from __future__ import annotations

import datetime as dt
import logging
import secrets
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from core import config, entitlements
from core import firestore as firestore_client
from core.auth import AuthUser, get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

#: Aboneligi baslatan/surduren olaylar.
_ACTIVATING_EVENTS = {
    "INITIAL_PURCHASE", "RENEWAL", "TRIAL_STARTED", "TRIAL_CONVERTED",
    "UNCANCELLATION", "PRODUCT_CHANGE", "SUBSCRIPTION_EXTENDED",
}

#: Erisimi hemen bitiren olaylar.
_DEACTIVATING_EVENTS = {"EXPIRATION", "SUBSCRIPTION_PAUSED", "REFUND"}

#: Otomatik yenilemeyi kapatan ama erisimi SURDUREN olaylar.
#: RevenueCat'te CANCELLATION "iptal edildi" degil "yenilenmeyecek" demektir;
#: kullanici odedigi donemin sonuna kadar erisimini korur.
_CANCELLATION_EVENTS = {"CANCELLATION", "BILLING_ISSUE"}

#: Aboneligi bir kimlikten digerine tasiyan olay.
#:
#: Anonim bir kimlikle satin alma yapilip sonra oturum acildiginda RevenueCat
#: kaydi devreder ve bu olayi gonderir. Islenmezse abonelik anonim dokumanda
#: kalir, kullanicinin uid'i altinda hicbir sey olmaz ve odeme yapmis kullanici
#: kilitli ekranla kalir.
#:
#: Bu olayin yukunde `app_user_id` YOKTUR; kimlikler `transferred_from` ve
#: `transferred_to` listelerinde gelir.
_TRANSFER_EVENT = "TRANSFER"


class SubscriptionStatus(BaseModel):
    active: bool
    product_id: str | None = None
    expires_at: str | None = None
    will_renew: bool | None = None
    is_trial: bool | None = None


@router.get("/status", response_model=SubscriptionStatus)
def status(user: AuthUser = Depends(get_current_user)):
    """Istemcinin arayuzu kilitlemek icin sordugu durum.

    Istemci RevenueCat SDK'sinin yerel durumunu da gorur; bu uc sunucunun
    gordugu gercegi doner ve ikisi ayrisirsa sunucu esas alinir.
    """
    subscription = entitlements.get_subscription(user.uid)
    expires_at = subscription.get("expiresAt")
    return SubscriptionStatus(
        # `is_subscriber` ile aynı kaynağa bakar — ham `active` alanına DEĞİL.
        #
        # İkisi ayrışabiliyordu: `RYTHO_FORCE_PLUS=1` ile uçlar açılıyor ama
        # bu uç "kapalı" diyordu, dolayısıyla istemci kilitli kart gösterip
        # kullanıcıyı çalışan bir özelliğe sokmuyordu. Bu ucun sözleşmesi
        # "sunucunun gördüğü gerçek"; sunucu çağrıyı kabul edecekse burada da
        # açık görünmeli, aksi halde istemci ile sunucu ayrışır.
        active=entitlements.is_subscriber(user.uid),
        product_id=subscription.get("productId"),
        expires_at=expires_at.isoformat() if hasattr(expires_at, "isoformat") else None,
        will_renew=subscription.get("willRenew"),
        is_trial=subscription.get("isTrial"),
    )


def _verify_secret(authorization: str | None) -> None:
    """Webhook'un gercekten RevenueCat'ten geldigini dogrular."""
    if not config.REVENUECAT_WEBHOOK_SECRET:
        # Gizli anahtar tanimsizken ucu acik birakmak, herkesin kendine
        # abonelik yazabilmesi demek olurdu.
        logger.error("REVENUECAT_WEBHOOK_SECRET tanimsiz; webhook reddedildi.")
        raise HTTPException(status_code=503, detail="Webhook yapilandirilmamis.")

    if not authorization or not secrets.compare_digest(
        authorization, config.REVENUECAT_WEBHOOK_SECRET
    ):
        raise HTTPException(status_code=401, detail="Gecersiz webhook imzasi.")


def _ms_to_datetime(value: Any) -> dt.datetime | None:
    if value is None:
        return None
    try:
        return dt.datetime.fromtimestamp(int(value) / 1000, tz=dt.timezone.utc)
    except (TypeError, ValueError):
        return None


def _subscription_ref(client, uid: str):
    return (client.collection("users").document(uid)
            .collection("private").document("subscription"))


def _handle_transfer(client, event: dict[str, Any]) -> dict[str, Any]:
    """Aboneligi eski kimlik(ler)den yeni kimlige tasir.

    Olayin yukunde urun ve bitis tarihi gelmiyor, bu yuzden kayit eski
    dokumandan KOPYALANIR. Sifirdan "aktif" yazsaydik bitis tarihini
    kaybeder ve suresi gecmis bir aboneligi sonsuza kadar acik birakirdik.
    """
    kaynaklar = [u for u in (event.get("transferred_from") or []) if u]
    hedefler = [u for u in (event.get("transferred_to") or []) if u]

    if not hedefler:
        logger.warning("TRANSFER olayinda hedef kimlik yok; atlandi.")
        return {"status": "ignored", "event": _TRANSFER_EVENT}

    kayit: dict[str, Any] | None = None
    for kaynak in kaynaklar:
        anlik = _subscription_ref(client, kaynak).get()
        if anlik.exists and kayit is None:
            kayit = anlik.to_dict() or None
        # Erisim iki kimlikte birden acik kalmamali.
        _subscription_ref(client, kaynak).set(
            {"active": False, "lastEvent": _TRANSFER_EVENT,
             "updatedAt": dt.datetime.now(dt.timezone.utc)},
            merge=True,
        )

    if kayit is None:
        # Kaynak dokuman yoksa devredecek bir sey de yok. Uydurma bir kayit
        # yazmak, odemesi olmayan kullaniciya erisim vermek olurdu.
        logger.info("TRANSFER: kaynak abonelik kaydi bulunamadi.")
        return {"status": "ok", "event": _TRANSFER_EVENT, "active": False}

    kayit = {**kayit, "lastEvent": _TRANSFER_EVENT,
             "updatedAt": dt.datetime.now(dt.timezone.utc)}
    for hedef in hedefler:
        _subscription_ref(client, hedef).set(kayit)

    logger.info("Abonelik devredildi: %s -> %s aktif=%s",
                kaynaklar, hedefler, kayit.get("active"))
    return {"status": "ok", "event": _TRANSFER_EVENT,
            "active": bool(kayit.get("active"))}


@router.post("/revenuecat")
async def revenuecat_webhook(
    payload: dict[str, Any],
    authorization: str | None = Header(default=None),
):
    """RevenueCat abonelik olaylarini kullanicinin gizli kaydina yazar."""
    _verify_secret(authorization)

    event = payload.get("event") or {}
    event_type = str(event.get("type") or "").upper()
    uid = event.get("app_user_id")

    bilinen = (_ACTIVATING_EVENTS | _DEACTIVATING_EVENTS
               | _CANCELLATION_EVENTS | {_TRANSFER_EVENT})
    # Bilmedigimiz olay tiplerinde mevcut durumu bozmadan onaylayip geciyoruz;
    # aksi halde RevenueCat tekrar tekrar denerdi.
    if event_type not in bilinen:
        logger.info("Islenmeyen RevenueCat olayi: %s", event_type)
        return {"status": "ignored", "event": event_type}

    # TRANSFER disindaki her olay tek bir kimlige yazilir. Bu kontrol Firestore
    # erisiminden ONCE yapilir: eksik kimlik istemci hatasidir (400), gecici
    # altyapi sorunu degil (500).
    if event_type != _TRANSFER_EVENT and not uid:
        raise HTTPException(status_code=400, detail="app_user_id eksik.")

    client = firestore_client.get_client()
    if client is None:
        # 500 donersek RevenueCat tekrar dener — gecici Firestore sorununda
        # istedigimiz davranis budur.
        raise HTTPException(status_code=500, detail="Firestore erisilemiyor.")

    if event_type == _TRANSFER_EVENT:
        return _handle_transfer(client, event)

    expires_at = _ms_to_datetime(event.get("expiration_at_ms"))
    active = event_type in (_ACTIVATING_EVENTS | _CANCELLATION_EVENTS)

    record = {
        "active": active,
        "productId": event.get("product_id"),
        "expiresAt": expires_at,
        "willRenew": event_type not in _CANCELLATION_EVENTS,
        "isTrial": str(event.get("period_type") or "").upper() == "TRIAL",
        "lastEvent": event_type,
        "store": event.get("store"),
        "updatedAt": dt.datetime.now(dt.timezone.utc),
    }

    _subscription_ref(client, uid).set(record)

    logger.info("Abonelik guncellendi: uid=%s olay=%s aktif=%s", uid, event_type, active)
    return {"status": "ok", "event": event_type, "active": active}
