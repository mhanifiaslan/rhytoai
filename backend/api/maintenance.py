"""Zamanlanmış bakım uçları — şimdilik yalnızca sohbet arşivi temizliği.

Cloud Scheduler günde bir çağırır (bkz. infra/create-scheduler.ps1,
`rytho-cleanup`). Güven modeli bildirim zamanlayıcısıyla AYNI: paylaşılan
gizli anahtar `Authorization` başlığında, anahtar tanımsızken uç kapalı
(fail-closed).

## Neden native Firestore TTL değil

TTL politikası yalnızca `conversations/{id}` dokümanını siler; `messages/*`
alt koleksiyonu YETİM kalır — sonsuza dek faturalanır ve `write: false`
kuralı yüzünden sahibi de silemez. Buradaki temizlik mesajları ÖNCE, konuyu
SONRA siler.
"""
from __future__ import annotations

import logging
import secrets

from fastapi import APIRouter, Header, HTTPException, Query

from core import config
from services import chat_history

logger = logging.getLogger(__name__)
router = APIRouter()


def _verify_scheduler(authorization: str | None) -> None:
    if not config.NOTIFY_SCHEDULER_SECRET:
        logger.error("NOTIFY_SCHEDULER_SECRET tanimsiz; bakim ucu reddedildi.")
        raise HTTPException(status_code=503,
                            detail="Bakim zamanlayicisi yapilandirilmamis.")
    if not authorization or not secrets.compare_digest(
        authorization, config.NOTIFY_SCHEDULER_SECRET
    ):
        raise HTTPException(status_code=401,
                            detail="Gecersiz zamanlayici anahtari.")


@router.post("/cleanup")
def cleanup(
    dry_run: bool = Query(default=False),
    limit: int = Query(default=300, ge=1, le=1000),
    authorization: str | None = Header(default=None),
):
    """30 gündür kullanılmayan konuşmaları mesajlarıyla siler.

    `dry_run=true` yalnızca sayar — politika değişikliklerinde "kaç konu
    gidecek" sorusuna silmeden cevap verir.
    """
    _verify_scheduler(authorization)
    try:
        sonuc = chat_history.purge_expired(limit=limit, dry_run=dry_run)
    except Exception as exc:
        logger.exception("Temizlik koşturulamadı", exc_info=exc)
        raise HTTPException(status_code=500, detail="Temizlik basarisiz.")
    return {"status": "success", "dry_run": dry_run, **sonuc}
