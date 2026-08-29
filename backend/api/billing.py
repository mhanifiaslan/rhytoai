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
from pydantic import BaseModel, Field

from core import config, entitlements, wallet
from core import firestore as firestore_client
from core.auth import AuthUser, get_current_user
from core.i18n import get_language
from core.messages import text

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

#: Parasal anlami olan olaylar — append-only gelir defterine yazilir (W3).
#: TRIAL_STARTED bilerek yok: deneme baslangicinda para el degistirmez.
_REVENUE_EVENTS = {
    "INITIAL_PURCHASE", "RENEWAL", "TRIAL_CONVERTED",
    "NON_RENEWING_PURCHASE", "REFUND",
}

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
    #: OT6: sunucu taraflı 3 günlük deneme — paywall'daki geri sayım.
    #: Yalnız deneme aktifken dolu; mağaza aboneliğinde None.
    trial_days_left: int | None = None


@router.get("/status", response_model=SubscriptionStatus)
def status(user: AuthUser = Depends(get_current_user)):
    """Istemcinin arayuzu kilitlemek icin sordugu durum.

    Istemci RevenueCat SDK'sinin yerel durumunu da gorur; bu uc sunucunun
    gordugu gercegi doner ve ikisi ayrisirsa sunucu esas alinir.
    """
    subscription = entitlements.get_subscription(user.uid)
    expires_at = subscription.get("expiresAt")
    # OT6: mağaza aboneliği yokken deneme dönemi de "açık" sayılır
    # (is_subscriber zaten öyle diyor); istemci geri sayımı buradan okur.
    deneme_kalan = (None if subscription.get("active")
                    else entitlements.trial_days_left(user.uid))
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
        is_trial=subscription.get("isTrial") or (deneme_kalan is not None),
        trial_days_left=deneme_kalan,
    )


class WalletStatus(BaseModel):
    allowance: int
    purchased: int
    total: int
    monthly_allowance: int
    allowance_resets_at: str | None = None
    costs: dict[str, int]


@router.get("/wallet", response_model=WalletStatus)
def wallet_status(user: AuthUser = Depends(get_current_user)):
    """İstemcinin bakiye göstergesi ve token mağazası için tek gerçek.

    İstemci paket adetlerini de buradan öğrenmez — yalnızca bedel tablosunu
    görür; paket içerikleri satın alma sonrası webhook'la sunucuda yüklenir.
    """
    cuzdan = wallet.get_wallet(user.uid)
    resets_at = cuzdan.get("allowance_resets_at")
    return WalletStatus(
        allowance=cuzdan["allowance"],
        purchased=cuzdan["purchased"],
        total=cuzdan["allowance"] + cuzdan["purchased"],
        monthly_allowance=cuzdan["monthly_allowance"],
        allowance_resets_at=(resets_at.isoformat()
                             if hasattr(resets_at, "isoformat") else None),
        costs=cuzdan["costs"],
    )


class RedeemCodeRequest(BaseModel):
    code: str = Field(min_length=2, max_length=32)


@router.post("/redeem-code")
def redeem_code(req: RedeemCodeRequest,
                user: AuthUser = Depends(get_current_user),
                lang: str = Depends(get_language)):
    """Ortak kodu kullanımı (W7): atıf + jeton bonusu.

    Her hesapta TEK kod geçer (attribution tek sefer); kod satın almadan
    ÖNCE girilmiş olmalı ki sonraki gelir ortağa atfedilsin.
    """
    from services import partner_service
    try:
        sonuc = partner_service.redeem(user.uid, req.code)
    except partner_service.RedeemError as e:
        anahtar = {"not_found": "promo.not_found",
                   "inactive": "promo.expired",
                   "expired": "promo.expired",
                   "exhausted": "promo.exhausted",
                   "already_redeemed": "promo.already_redeemed",
                   }.get(e.reason, "promo.invalid")
        raise HTTPException(status_code=e.status,
                            detail=text(anahtar, lang,
                                        fallback="promo.invalid"))
    return {"status": "ok", "bonusTokens": sonuc["bonusTokens"]}


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

    # Cüzdan da taşınır: satın alınmış bakiye kullanıcının parası, kimlik
    # değişiminde kaybolamaz.
    wallet.transfer_wallet(client, kaynaklar, hedefler)

    logger.info("Abonelik devredildi: %s -> %s aktif=%s",
                kaynaklar, hedefler, kayit.get("active"))
    return {"status": "ok", "event": _TRANSFER_EVENT,
            "active": bool(kayit.get("active"))}


def _record_revenue_event(event: dict[str, Any], event_type: str,
                          uid: str) -> None:
    """Parasal olayi append-only gelir defterine yazar (W3).

    Abonelik dokumani ``set()`` ile ezildigi icin gecmis tutmuyor; para
    cinsinden gelirin TEK gercegi ``revenueEvents`` koleksiyonudur. Dokuman
    kimligi RevenueCat ``event.id`` — ayni olayin tekrari ayni dokumani ezer
    (ledger deseniyle ayni dogal idempotency, bkz. core/wallet.py).

    Yazim EN-IYI-CABA: gelir kaydi dusse bile abonelik/cuzdan islemeye devam
    eder — muhasebe kaydi ugruna kullanicinin erisimi kesilmez.
    """
    event_id = str(event.get("id") or "")
    if not event_id:
        logger.warning("Gelir olayinda event.id yok; deftere yazilmadi: %s",
                       event_type)
        return
    client = firestore_client.get_client()
    if client is None:
        logger.warning("Gelir defteri yazilamadi (Firestore yok): %s", event_id)
        return
    try:
        # Ortak atfi (W7): kod kullanmis kullanicinin geliri ortagina islenir.
        # Kod sistemi kurulana kadar dokuman yoktur ve alan null kalir.
        partner_id = None
        attribution = (client.collection("users").document(uid)
                       .collection("private").document("attribution").get())
        if getattr(attribution, "exists", False):
            partner_id = (attribution.to_dict() or {}).get("partnerId")

        client.collection("revenueEvents").document(event_id).set({
            "uid": uid,
            "eventType": event_type,
            "productId": event.get("product_id"),
            "store": event.get("store"),
            # `price` RevenueCat'in USD normalize degeri; satin alinan para
            # birimindeki ham deger ayrica tasinir. REFUND'da isaret HAM
            # birakilir — yorum panelin isi (eventType zaten ayirt ediyor).
            "price": event.get("price"),
            "priceInPurchasedCurrency": event.get("price_in_purchased_currency"),
            "currency": event.get("currency"),
            "countryCode": event.get("country_code"),
            "isTrial": str(event.get("period_type") or "").upper() == "TRIAL",
            "partnerId": partner_id,
            "at": (_ms_to_datetime(event.get("event_timestamp_ms"))
                   or dt.datetime.now(dt.timezone.utc)),
            "recordedAt": dt.datetime.now(dt.timezone.utc),
        })
    except Exception as exc:
        logger.warning("Gelir defteri yazilamadi (%s): %s", event_id, exc)


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
    product_id = str(event.get("product_id") or "")

    # ---- TOKEN PAKETLERİ: abonelik borusundan ÖNCE ayrılır. ----
    #
    # Sıralama kritik ve iki doğrulanmış tuzağı kapatıyor:
    # 1. NON_RENEWING_PURCHASE "bilinen" kümede değildi — paket satışı
    #    sessizce yutulurdu.
    # 2. REFUND _DEACTIVATING_EVENTS içinde — paket iadesi aşağıdaki
    #    abonelik yazımına düşseydi kullanıcının AYRI ödediği ABONELİĞİNİ
    #    kapatırdı. Ürün kimliği paket listesindeyse abonelik dokümanına
    #    asla dokunulmaz.
    if product_id in wallet.TOKEN_PACKS:
        if not uid:
            raise HTTPException(status_code=400, detail="app_user_id eksik.")
        event_id = str(event.get("id") or "")
        if not event_id:
            # Kimliksiz olayda idempotency kurulamaz; RevenueCat yeniden
            # denesin diye 400 DEĞİL 500'e yakın davranmak yanlış — kimlik
            # yükün kalıcı özelliği, tekrar denemede de gelmez. Logla, geç.
            logger.warning("Paket olayında event.id yok; atlandı: %s", event_type)
            return {"status": "ignored", "event": event_type}
        if event_type == "NON_RENEWING_PURCHASE":
            wallet.credit_pack(uid, product_id, event_id)
            _record_revenue_event(event, event_type, uid)
            return {"status": "ok", "event": event_type, "pack": product_id}
        if event_type == "REFUND":
            wallet.debit_refund(uid, product_id, event_id)
            _record_revenue_event(event, event_type, uid)
            return {"status": "ok", "event": event_type, "pack": product_id}
        logger.info("Paket ürününde beklenmeyen olay: %s", event_type)
        return {"status": "ignored", "event": event_type}

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

    # Parasal abonelik olaylari gelir defterine de islenir (W3).
    if event_type in _REVENUE_EVENTS:
        _record_revenue_event(event, event_type, uid)

    # Yeni/yenilenen donem aylik token hakkini tazeler. Idempotent: ayni
    # donemin tekrarlanan webhook'u hakki iki kez veremez (isaret esitligi).
    #
    # K2 yedegi: webhook `expiration_at_ms` tasimadan gelirse eskiden
    # reset_allowance HIC yazmiyordu ve ilk alimda bakiye 0 gorunuyordu
    # (ic test bulgusu). Aktive eden olayda son kullanma yoksa 35 gunluk
    # emniyet penceresi kullanilir — bir sonraki RENEWAL gercek tarihi
    # yazar; hak hicbir durumda verilmemis kalmaz.
    if event_type in _ACTIVATING_EVENTS:
        wallet.reset_allowance(
            uid,
            expires_at
            or dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=35))

    logger.info("Abonelik guncellendi: uid=%s olay=%s aktif=%s", uid, event_type, active)
    return {"status": "ok", "event": event_type, "active": active}
