"""Cihaz kilidi uçları: durum sorgusu ve açık devralma.

Kilidin kendisi uçlarda değil, `core/device.enforce_single_device`'ta —
aboneli yollara oradan bağlanır. Buradaki iki uç yalnızca devralma
akışının konuşma yüzeyi:

* `GET /status` — giriş akışı "devralma onayı gösterilsin mi" diye sorar.
* `POST /claim` — kullanıcı onayladıktan sonra cihaz devralınır; eski
  cihaz bir sonraki isteğinde 409 alır.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from core import device
from core.auth import AuthUser, get_current_user
from core.i18n import get_language
from core.messages import text

logger = logging.getLogger(__name__)
router = APIRouter()


class ClaimRequest(BaseModel):
    platform: str | None = None


@router.get("/status")
def status(
    user: AuthUser = Depends(get_current_user),
    x_device_id: str | None = Header(default=None),
):
    return {"status": "success", **device.device_status(user.uid, x_device_id)}


@router.post("/claim")
def claim(
    req: ClaimRequest,
    user: AuthUser = Depends(get_current_user),
    lang: str = Depends(get_language),
    x_device_id: str | None = Header(default=None),
):
    """Cihazı bu kimliğe devreder — kullanıcı ONAYINDAN sonra çağrılmalı.

    Başlıksız çağrı 400: kimliği olmayan bir cihaza devir anlamsız ve
    muhtemelen istemci hatası.
    """
    if x_device_id is None or not x_device_id.strip():
        raise HTTPException(status_code=400, detail=text("internal", lang))
    return {"status": "success",
            **device.claim_device(user.uid, x_device_id, req.platform)}
