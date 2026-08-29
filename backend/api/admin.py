"""Admin uçları (W5): istatistik toplama ve okuma.

Panel (/rytho-admin) Firestore'a hiç dokunmaz — her veri buradan geçer ve
her uç `require_admin` (custom claim) ister. Tek istisna `collect`: gecelik
Cloud Scheduler işi claim taşıyamayacağı için scheduler sırrı da geçerli
(bkz. api/notify.py `_verify_scheduler` deseni — ÇİFT KAPI).
"""
from __future__ import annotations

import datetime as dt
import logging
import secrets as py_secrets
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from core import config, firestore as firestore_client
from core import wallet
from core.auth import AuthUser, get_current_user, require_admin
from core.i18n import get_language
from services import admin_service, partner_service, stats_service

logger = logging.getLogger(__name__)
router = APIRouter()


def _audit(user: AuthUser, action: str, target_uid: str | None = None,
           params: dict[str, Any] | None = None) -> None:
    """Denetim izi (AP-turu): admin'in YAZAN eylemleri kalıcı kayda düşer.

    Salt-okur uçlar audit'lenmez (gürültü). Best-effort — iz yazılamadı
    diye eylem geri alınmaz; tek sahipli üründe iz "kim"den çok "ne
    zaman/ne" sorusuna cevaptır ve ileride çoklu admin gelirse hazırdır.
    """
    try:
        client = firestore_client.get_client()
        if client is None:
            return
        client.collection("adminAudit").document().set({
            "adminUid": user.uid,
            "adminEmail": getattr(user, "email", None),
            "action": action,
            "targetUid": target_uid,
            "params": params or {},
            "at": dt.datetime.now(dt.timezone.utc),
        })
    except Exception as exc:
        logger.warning("Denetim izi yazılamadı (%s): %s", action, exc)


def _scheduler_gecerli(authorization: str | None) -> bool:
    """Scheduler sırrı doğru mu — yoksa/uyuşmuyorsa sessizce False.

    notify.py'deki `_verify_scheduler`dan farkı: burada hata FIRLATMAZ,
    çünkü ikinci kapı (admin claim) hâlâ denenecek.
    """
    return bool(
        config.NOTIFY_SCHEDULER_SECRET
        and authorization
        and py_secrets.compare_digest(authorization,
                                      config.NOTIFY_SCHEDULER_SECRET)
    )


@router.post("/collect")
async def collect(
    date: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    authorization: str | None = Header(default=None),
    lang: str = Depends(get_language),
):
    """Günün istatistiklerini toplar — ÇİFT KAPI: scheduler sırrı VEYA admin.

    `Depends(get_current_user)` BİLEREK yok: scheduler'ın başlığı Bearer
    değil ham sır taşır ve dependency zinciri isteği kapıya gelmeden 401'lerdi
    (üretimde yaşandı). Sıra: önce sır denenir; tutmazsa başlık Bearer olarak
    ayrıştırılıp admin claim'i aranır.

    İdempotent: aynı günün tekrarı dokümanı ezer, birikmez.
    """
    kullanici: AuthUser | None = None
    if not _scheduler_gecerli(authorization):
        kimlik_bilgisi = None
        if authorization and authorization.startswith("Bearer "):
            kimlik_bilgisi = HTTPAuthorizationCredentials(
                scheme="Bearer", credentials=authorization[7:])
        kullanici = await get_current_user(credentials=kimlik_bilgisi,
                                           lang=lang)
        if not kullanici.admin:
            raise HTTPException(status_code=403, detail="Yetkisiz.")

    tarih = dt.date.fromisoformat(date) if date else None
    try:
        dokuman = stats_service.collect(tarih)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    if kullanici is not None:
        # Yalnız admin kapısından geçen elle tetikleme iz bırakır;
        # scheduler'ın gecelik koşusu rutindir, denetim izi değil.
        _audit(kullanici, "stats.collect", params={"date": dokuman["date"]})
    return {"status": "ok", "date": dokuman["date"],
            "durationMs": dokuman["durationMs"]}


@router.get("/stats")
def stats(days: int = Query(default=30, ge=1, le=365),
          user: AuthUser = Depends(require_admin)):
    """Son N günün hazır adminStats dokümanları (yeniden eskiye)."""
    return {"status": "ok", "days": stats_service.read_days(days)}


@router.get("/live")
def live(user: AuthUser = Depends(require_admin)):
    """Hafif canlı satır: bugünkü doküman var mı + bugünkü kayıt sayısı.

    Ağır tarama YOK — gecelik collect'in işi; burada yalnız tek doküman
    okuması ve tek count() var.
    """
    client = firestore_client.get_client()
    if client is None:
        raise HTTPException(status_code=500, detail="Firestore erişilemiyor.")

    bugun = dt.datetime.now(dt.timezone.utc).date().isoformat()
    anlik = client.collection("adminStats").document(bugun).get()
    bugunku: dict[str, Any] | None = (anlik.to_dict()
                                      if getattr(anlik, "exists", False)
                                      else None)

    gun_bas = dt.datetime.combine(dt.date.fromisoformat(bugun), dt.time.min,
                                  tzinfo=dt.timezone.utc)
    try:
        from google.cloud.firestore_v1.base_query import FieldFilter
        yeni_kayit = (client.collection("users")
                      .where(filter=FieldFilter("createdAt", ">=", gun_bas))
                      .count().get())
        bugun_yeni = int(yeni_kayit[0][0].value)
    except Exception:
        bugun_yeni = -1

    return {"status": "ok", "today": bugunku, "newUsersToday": bugun_yeni,
            "serverTime": dt.datetime.now(dt.timezone.utc).isoformat()}


@router.get("/revenue")
def revenue(days: int = Query(default=90, ge=1, le=365),
            user: AuthUser = Depends(require_admin)):
    """Gelir olaylarının tarih aralıklı özeti (revenueEvents'ten).

    Günlük brüt (USD normalize `price`), ürün/mağaza/para birimi kırılımı
    ve olay sayıları. `at` tek alan indeksi otomatiktir.
    """
    client = firestore_client.get_client()
    if client is None:
        raise HTTPException(status_code=500, detail="Firestore erişilemiyor.")

    from google.cloud.firestore_v1.base_query import FieldFilter

    baslangic = (dt.datetime.now(dt.timezone.utc)
                 - dt.timedelta(days=days))
    gunler: dict[str, float] = {}
    urun: dict[str, float] = {}
    magaza: dict[str, float] = {}
    para_birimi: dict[str, float] = {}
    olaylar: dict[str, int] = {}
    for anlik in (client.collection("revenueEvents")
                  .where(filter=FieldFilter("at", ">=", baslangic))
                  .stream()):
        veri = anlik.to_dict() or {}
        tip = str(veri.get("eventType") or "-")
        olaylar[tip] = olaylar.get(tip, 0) + 1
        fiyat = float(veri.get("price") or 0)
        if tip == "REFUND":
            fiyat = -abs(fiyat)
        at = veri.get("at")
        gun = (at.date().isoformat()
               if hasattr(at, "date") else "-")
        gunler[gun] = round(gunler.get(gun, 0.0) + fiyat, 2)
        u = str(veri.get("productId") or "-")
        urun[u] = round(urun.get(u, 0.0) + fiyat, 2)
        m = str(veri.get("store") or "-")
        magaza[m] = round(magaza.get(m, 0.0) + fiyat, 2)
        pb = str(veri.get("currency") or "-")
        para_birimi[pb] = round(
            para_birimi.get(pb, 0.0)
            + float(veri.get("priceInPurchasedCurrency") or 0), 2)

    return {"status": "ok", "days": days,
            "byDay": gunler, "byProduct": urun, "byStore": magaza,
            "byCurrency": para_birimi, "events": olaylar,
            "grossUsd": round(sum(gunler.values()), 2)}


# ---------------------------------------------------------------------------
# Kullanıcılar + kullanım + sistem okumaları (AP-turu) — hepsi require_admin
# ---------------------------------------------------------------------------

class CreditCreate(BaseModel):
    """Elle kredi: tutar pozitif, gerekçe ZORUNLU (denetim + defter)."""
    amount: int = Field(gt=0, le=5000)
    reason: str = Field(min_length=3, max_length=300)


@router.get("/users")
def users(query: str = Query(default="", max_length=120),
          sort: str = Query(default="createdAt"),
          limit: int = Query(default=50, ge=1, le=200),
          user: AuthUser = Depends(require_admin)):
    try:
        satirlar = admin_service.list_users(query=query, sort=sort,
                                            limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return {"status": "ok", "users": satirlar}


@router.get("/users/{uid}")
def user_detail(uid: str, user: AuthUser = Depends(require_admin)):
    try:
        detay = admin_service.user_360(uid)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    if detay is None:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")
    return {"status": "ok", **detay}


@router.post("/users/{uid}/credit")
def user_credit(uid: str, req: CreditCreate,
                user: AuthUser = Depends(require_admin)):
    """Cüzdana admin kredisi — destek aracı ("paket geldi, bakiye gelmedi").

    Yalnız POZİTİF tutar: düşüm ayrı bir iştir ve bilerek yok (yanlışlıkla
    kullanıcı bakiyesi silinmesin). Defter + denetim izi birlikte yazılır.
    """
    try:
        wallet.credit_admin(uid, req.amount, req.reason, user.uid)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    _audit(user, "user.credit", target_uid=uid,
           params={"amount": req.amount, "reason": req.reason})
    return {"status": "ok", "wallet": wallet.get_wallet(uid)}


@router.get("/usage")
def usage(days: int = Query(default=30, ge=1, le=90),
          user: AuthUser = Depends(require_admin)):
    try:
        return {"status": "ok", **admin_service.usage_summary(days)}
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/notify-runs")
def notify_runs(days: int = Query(default=7, ge=1, le=30),
                user: AuthUser = Depends(require_admin)):
    try:
        return {"status": "ok", "runs": admin_service.notify_runs(days)}
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/audit")
def audit(limit: int = Query(default=50, ge=1, le=200),
          user: AuthUser = Depends(require_admin)):
    try:
        return {"status": "ok", "entries": admin_service.audit_list(limit)}
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Ortaklar (W7) — panel CRUD'u; hepsi require_admin
# ---------------------------------------------------------------------------

class PartnerCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    contact: str = Field(default="", max_length=160)
    sharePercent: float = Field(default=0, ge=0, le=90)
    notes: str = Field(default="", max_length=500)


class PartnerPatch(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=80)
    contact: str | None = Field(default=None, max_length=160)
    sharePercent: float | None = Field(default=None, ge=0, le=90)
    active: bool | None = None
    notes: str | None = Field(default=None, max_length=500)


class CodeCreate(BaseModel):
    #: Boş bırakılırsa okunaklı rastgele kod üretilir.
    code: str | None = Field(default=None, max_length=24)
    bonusTokens: int = Field(default=0, ge=0, le=5000)
    maxRedemptions: int | None = Field(default=None, ge=1)
    #: ISO tarih (YYYY-MM-DD) — gün sonu UTC kabul edilir.
    expiresAt: str | None = Field(default=None,
                                  pattern=r"^\d{4}-\d{2}-\d{2}$")


class PayoutCreate(BaseModel):
    amount: float = Field(gt=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    note: str = Field(default="", max_length=300)


def _servis_hatasi(e: partner_service.RedeemError) -> HTTPException:
    return HTTPException(status_code=e.status, detail=e.reason)


@router.get("/partners")
def partners(user: AuthUser = Depends(require_admin)):
    return {"status": "ok", "partners": partner_service.list_partners()}


@router.post("/partners")
def create_partner(req: PartnerCreate,
                   user: AuthUser = Depends(require_admin)):
    try:
        ortak = partner_service.create_partner(
            req.name, req.contact, req.sharePercent, req.notes)
    except partner_service.RedeemError as e:
        raise _servis_hatasi(e)
    _audit(user, "partner.create", params={"name": req.name})
    return {"status": "ok", "partner": ortak}


@router.patch("/partners/{partner_id}")
def patch_partner(partner_id: str, req: PartnerPatch,
                  user: AuthUser = Depends(require_admin)):
    try:
        partner_service.update_partner(
            partner_id, req.model_dump(exclude_none=True))
    except partner_service.RedeemError as e:
        raise _servis_hatasi(e)
    _audit(user, "partner.update",
           params={"partnerId": partner_id,
                   **req.model_dump(exclude_none=True)})
    return {"status": "ok"}


@router.get("/partners/{partner_id}")
def partner_detail(partner_id: str,
                   user: AuthUser = Depends(require_admin)):
    try:
        return {"status": "ok", **partner_service.partner_detail(partner_id)}
    except partner_service.RedeemError as e:
        raise _servis_hatasi(e)


@router.post("/partners/{partner_id}/codes")
def create_code(partner_id: str, req: CodeCreate,
                user: AuthUser = Depends(require_admin)):
    son = None
    if req.expiresAt:
        son = dt.datetime.combine(dt.date.fromisoformat(req.expiresAt),
                                  dt.time.max, tzinfo=dt.timezone.utc)
    try:
        kod = partner_service.create_code(
            partner_id, req.code, req.bonusTokens, req.maxRedemptions, son)
    except partner_service.RedeemError as e:
        raise _servis_hatasi(e)
    _audit(user, "partner.code",
           params={"partnerId": partner_id, "code": kod.get("code"),
                   "bonusTokens": req.bonusTokens})
    return {"status": "ok", "code": kod}


@router.post("/partners/{partner_id}/payouts")
def add_payout(partner_id: str, req: PayoutCreate,
               user: AuthUser = Depends(require_admin)):
    try:
        odeme = partner_service.add_payout(
            partner_id, req.amount, req.currency, req.note)
    except partner_service.RedeemError as e:
        raise _servis_hatasi(e)
    _audit(user, "partner.payout",
           params={"partnerId": partner_id, "amount": req.amount,
                   "currency": req.currency})
    return {"status": "ok", "payout": odeme}
