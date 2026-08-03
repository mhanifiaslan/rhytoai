"""Yetki (entitlement) katmani — kim neye erisebilir, ucretsiz kotalar ne kadar.

Urunun birim ekonomisi buradan yonetilir. Temel kural:

**Ucretsiz katman kullanici sayisindan bagimsiz maliyetle calisir.** Ucretsiz
icerik (burc yorumu, gokyuzu) paylasimli onbellekten servis edilir; kullanici
basina LLM cagrisi gerektiren her sey ya aboneliğe ya da gunluk bir kotaya
baglidir. Aksi halde kullanici arttikca maliyet dogrusal buyur ve urun batar.

Abonelik durumu **yalnizca sunucu tarafindan** yazilir
(``users/{uid}/private/subscription``); istemcinin o yola yazma izni yoktur
(bkz. infra/firestore.rules). Kaynak su an RevenueCat webhook'udur ama katman
kaynaktan bagimsizdir: baska bir saglayiciya gecilirse yalnizca yazan taraf
degisir.

Kota sayaclari da Firestore'da tutulur. Bellek ici sayac Cloud Run'da
instance basina ayri olurdu ve kullanici instance degistirerek kotayi
sifirlayabilirdi.
"""
from __future__ import annotations

import datetime as dt
import logging
import os
from typing import Any

from fastapi import Depends, Header, HTTPException

from core import firestore as firestore_client
from core.auth import AuthUser, get_current_user
from core.i18n import DEFAULT as DEFAULT_LANG, get_language
from core.messages import text

logger = logging.getLogger(__name__)

#: Kilitli ozellik icin donen HTTP kodu. Istemci bunu gorunce paywall acar.
PAYWALL_STATUS = 402

#: Gelistirme/otomasyon icin tum ozellikleri acar. Uretimde ASLA 1 olmamali.
FORCE_PLUS: bool = os.getenv("RYTHO_FORCE_PLUS", "0") == "1"

# ---------------------------------------------------------------------------
# Ucretsiz katman kotalari
# ---------------------------------------------------------------------------

#: Ucretsiz kullanicinin gunluk sohbet mesaji hakki. Abonede sinirsizdir.
FREE_CHAT_PER_DAY = 5

#: I Ching "hafif gunluk ritual" olarak ucretsiz kalir ama gunde bir cekilis.
#: Sinirsiz olsa kullanici basina acik uclu LLM maliyeti olusurdu.
FREE_ICHING_PER_DAY = 1

#: Kilitli uclarda ve dolu kotalarda donen metinler artik core/messages.py'de,
#: dile gore tutuluyor: bu metinler istemcide dogrudan kullaniciya gosteriliyor
#: (bkz. friendlyError) ve Ingilizce kullanan biri Turkce paywall metni
#: gormemeli. Anahtarlar "paywall.<ozellik>" ve "quota.<anahtar>" bicimindedir.


def _private_doc(uid: str, name: str):
    client = firestore_client.get_client()
    if client is None:
        return None
    return client.collection("users").document(uid).collection("private").document(name)


# ---------------------------------------------------------------------------
# Abonelik durumu
# ---------------------------------------------------------------------------

def get_subscription(uid: str) -> dict[str, Any]:
    """Kullanicinin abonelik kaydi. Okunamazsa ucretsiz kabul edilir.

    Firestore erisilemedigi icin kullaniciya ucretli icerik ACMAYIZ; hata
    durumunda guvenli taraf ucretsizdir.
    """
    doc_ref = _private_doc(uid, "subscription")
    if doc_ref is None:
        return {"active": False, "reason": "firestore-yok"}
    try:
        snapshot = doc_ref.get()
    except Exception as exc:
        logger.warning("Abonelik okunamadi (%s): %s", uid, exc)
        return {"active": False, "reason": "okuma-hatasi"}

    if not snapshot.exists:
        return {"active": False}

    data = snapshot.to_dict() or {}
    expires_at = data.get("expiresAt")
    if expires_at is not None:
        try:
            if expires_at.timestamp() < dt.datetime.now(dt.timezone.utc).timestamp():
                # Webhook gecikmis olabilir; suresi gecmis kaydi aktif sayma.
                return {"active": False, "expired": True,
                        "productId": data.get("productId")}
        except AttributeError:
            pass

    return {
        "active": bool(data.get("active")),
        "productId": data.get("productId"),
        "expiresAt": expires_at,
        "willRenew": data.get("willRenew"),
        "isTrial": data.get("isTrial"),
    }


def is_subscriber(uid: str) -> bool:
    if FORCE_PLUS:
        return True
    return bool(get_subscription(uid).get("active"))


# ---------------------------------------------------------------------------
# Gunluk kotalar
# ---------------------------------------------------------------------------

def _today() -> str:
    return dt.date.today().isoformat()


def quota_state(uid: str, key: str, limit: int) -> tuple[int, int]:
    """(kullanilan, kalan) — sayaci artirmadan okur."""
    doc_ref = _private_doc(uid, "quota")
    if doc_ref is None:
        return 0, limit
    try:
        snapshot = doc_ref.get()
    except Exception:
        return 0, limit

    data = (snapshot.to_dict() or {}) if snapshot.exists else {}
    if data.get("date") != _today():
        return 0, limit
    used = int(data.get(key, 0))
    return used, max(limit - used, 0)


def consume_quota(uid: str, key: str, limit: int) -> bool:
    """Kotadan bir hak duser. Hak kalmadiysa ``False`` doner ve dusmez.

    Gun degistiginde sayaclar sifirlanir (dokumandaki ``date`` alani).
    """
    doc_ref = _private_doc(uid, "quota")
    if doc_ref is None:
        # Firestore yoksa kotayi zorlayamayiz; istegi dusurmek yerine gecir.
        # Lokal gelistirmede bu normaldir, uretimde Firestore her zaman vardir.
        return True

    try:
        snapshot = doc_ref.get()
        data = (snapshot.to_dict() or {}) if snapshot.exists else {}
        today = _today()
        if data.get("date") != today:
            data = {"date": today}

        used = int(data.get(key, 0))
        if used >= limit:
            return False

        data[key] = used + 1
        doc_ref.set(data)
        return True
    except Exception as exc:
        logger.warning("Kota guncellenemedi (%s/%s): %s", uid, key, exc)
        return True


# ---------------------------------------------------------------------------
# FastAPI bagimliliklari
# ---------------------------------------------------------------------------

def require_plus(feature: str):
    """Aboneliğe bagli uclar icin bagimlilik uretir.

    Kullanim:  ``user: AuthUser = Depends(require_plus("natal_report"))``

    Tek cihaz kilidi de BURADAN uygulanir: kilit yalnizca abonelere ait ve
    aboneli her yol bu bagimliliktan geciyor — ayri bir dependency her uca
    tek tek eklenmek zorunda kalirdi ve biri unutulurdu.
    """

    def dependency(user: AuthUser = Depends(get_current_user),
                   lang: str = Depends(get_language),
                   x_device_id: str | None = Header(default=None)) -> AuthUser:
        if not is_subscriber(user.uid):
            raise HTTPException(
                status_code=PAYWALL_STATUS,
                detail=text(f"paywall.{feature}", lang,
                            fallback="paywall.default"),
            )
        # Tembel import: core.device -> core.entitlements yonu zaten var,
        # modul duzeyinde geri bag dongusel import olurdu.
        from core import device
        device.enforce_single_device(user.uid, x_device_id, lang=lang)
        return user

    return dependency


def enforce_daily_quota(user: AuthUser, key: str, limit: int,
                        lang: str = DEFAULT_LANG) -> None:
    """Ucretsiz kullanici icin gunluk kotayi uygular; abone sinirsizdir.

    Kota dolduysa paywall koduyla (402) hata firlatir. ``lang`` yalnizca
    kullaniciya donen metni belirler; kotanin kendisi dilden bagimsizdir.
    """
    if is_subscriber(user.uid):
        return
    if not consume_quota(user.uid, key, limit):
        raise HTTPException(
            status_code=PAYWALL_STATUS,
            detail=text(f"quota.{key}", lang, fallback="quota.default",
                        limit=limit),
        )
