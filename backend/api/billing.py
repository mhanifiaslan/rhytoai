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
        active=bool(subscription.get("active")),
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

    if not uid:
        raise HTTPException(status_code=400, detail="app_user_id eksik.")

    # Bilmedigimiz olay tiplerinde mevcut durumu bozmadan onaylayip geciyoruz;
    # aksi halde RevenueCat tekrar tekrar denerdi.
    if event_type not in (_ACTIVATING_EVENTS | _DEACTIVATING_EVENTS | _CANCELLATION_EVENTS):
        logger.info("Islenmeyen RevenueCat olayi: %s", event_type)
        return {"status": "ignored", "event": event_type}

    client = firestore_client.get_client()
    if client is None:
        # 500 donersek RevenueCat tekrar dener — gecici Firestore sorununda
        # istedigimiz davranis budur.
        raise HTTPException(status_code=500, detail="Firestore erisilemiyor.")

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

    (client.collection("users").document(uid)
        .collection("private").document("subscription").set(record))

    logger.info("Abonelik guncellendi: uid=%s olay=%s aktif=%s", uid, event_type, active)
    return {"status": "ok", "event": event_type, "active": active}
