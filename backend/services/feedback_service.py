"""Uygulama içi geri bildirim kanalı (GB-turu) — kullanıcı tarafı.

Kullanıcı Profil'den hata / öneri / diğer yazar; kayıt `feedback/{autoId}`
dokümanına düşer, panel okur ve yanıtlar (services/admin_service
`feedback_*`). Koleksiyon istemciye TAMAMEN kapalıdır (firestore.rules):
tek kapı `POST /api/v1/account/feedback`.

Neden sunucuda: istemci kuralla yazabilseydi bile bağlam (build, platform,
dil) istemci beyanı olurdu ve günlük sınır uygulanamazdı. Burada bağlam
isteğin başlıklarından okunur; sınır `count()` ile sayılır — doküman
taşınmaz.
"""
from __future__ import annotations

import datetime as dt
import logging
from typing import Any

from core import firestore as firestore_client

logger = logging.getLogger(__name__)

#: Kabul edilen türler — panel süzgeci ve pydantic Literal ile aynı küme.
TYPES = ("bug", "suggestion", "other")

#: Kayıt durumları; yeni kayıt `new`, yanıtlanan `in_review`, kapatılan
#: `closed`.
STATUSES = ("new", "in_review", "closed")

#: Bir kullanıcının bir UTC gününde gönderebileceği en fazla kayıt.
DAILY_LIMIT = 10

MAX_TEXT = 2000
MAX_SCREEN = 60
MAX_PLATFORM = 16


class LimitError(Exception):
    """Günlük sınır doldu — uç 429'a çevirir."""


def _client():
    client = firestore_client.get_client()
    if client is None:
        raise RuntimeError("Firestore erişilemiyor.")
    return client


def _gun_basi(simdi: dt.datetime) -> dt.datetime:
    return dt.datetime.combine(simdi.date(), dt.time.min,
                               tzinfo=dt.timezone.utc)


def count_today(uid: str, simdi: dt.datetime | None = None) -> int:
    """Kullanıcının bugün (UTC) yazdığı kayıt sayısı; sayım düşerse 0 —
    sayım hatası kullanıcıyı kilitlemez (fail-open, yalnız sınır için)."""
    from google.cloud.firestore_v1.base_query import FieldFilter

    simdi = simdi or dt.datetime.now(dt.timezone.utc)
    try:
        sonuc = (_client().collection("feedback")
                 .where(filter=FieldFilter("uid", "==", uid))
                 .where(filter=FieldFilter("createdAt", ">=",
                                           _gun_basi(simdi)))
                 .count().get())
        return int(sonuc[0][0].value)
    except Exception as exc:
        logger.warning("Geri bildirim sayımı düştü (%s): %s", uid, exc)
        return 0


def submit(uid: str, *, type_: str, text: str, screen: str | None,
           app_build: int | None, platform: str | None,
           language: str) -> str:
    """Kaydı yazar, doküman kimliğini döndürür. Sınır aşıldıysa LimitError.

    Metin/tür doğrulaması uçtaki pydantic modelinde; burada yalnız kırpma.
    """
    if type_ not in TYPES:
        raise ValueError(f"Bilinmeyen tür: {type_}")
    simdi = dt.datetime.now(dt.timezone.utc)
    if count_today(uid, simdi) >= DAILY_LIMIT:
        raise LimitError()

    ekran = (screen or "").strip()[:MAX_SCREEN] or None
    plat = (platform or "").strip().lower()[:MAX_PLATFORM] or None
    kayit: dict[str, Any] = {
        "uid": uid,
        "type": type_,
        "text": text.strip()[:MAX_TEXT],
        "screen": ekran,
        "appBuild": int(app_build) if app_build else None,
        "platform": plat,
        "language": language,
        "createdAt": simdi,
        "status": "new",
        "notes": [],
        "reply": None,
        "updatedAt": simdi,
    }
    ref = _client().collection("feedback").document()
    ref.set(kayit)
    return ref.id
