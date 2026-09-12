"""Cihaz kilidi uçları: durum, açık devralma, serbest bırakma.

Kilidin kendisi uçlarda değil, `core/device.enforce_single_device`'ta —
ücretli yollara `require_plus`'tan bağlanır. Buradaki üç uç devralma
akışının konuşma yüzeyi:

* `GET /status` — kilit bu kullanıcıda etkin mi, kayıt kimde (teşhis).
* `POST /claim` — "Bu cihazda kullan": kayıt bu cihaza geçer, öbür cihaz
  bir sonraki isteğinde 409 alır.
* `DELETE /claim` — çıkışta serbest bırakma; yalnız kayıt bu cihazınsa.

ÜÇÜ DE `get_current_user` ile korunur, `require_plus` ile DEĞİL: 409'a
düşen cihaz devralmak için buraya gelir — kapı arkasında olsalardı
devralma imkânsız olurdu (test_device_api sabitler).
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
    """Cihazı bu kimliğe devreder — kapı ekranındaki "Bu cihazda kullan".

    `auth_time` token'dan: kayıt bu oturumun giriş anını taşır. `claimed`
    dürüst — yazılamadıysa False, istemci kapıyı kapatmaz. Başlıksız çağrı
    400: kimliği olmayan bir cihaza devir anlamsız ve muhtemelen istemci
    hatası.
    """
    if x_device_id is None or not x_device_id.strip():
        raise HTTPException(status_code=400, detail=text("internal", lang))
    return {"status": "success",
            **device.claim_device(user.uid, x_device_id,
                                  auth_time=user.auth_time,
                                  platform=req.platform)}


@router.delete("/claim")
def release(
    user: AuthUser = Depends(get_current_user),
    x_device_id: str | None = Header(default=None),
):
    """Çıkışta serbest bırakma (K7): "eski cihazdan çıkış yeni cihazı açar".

    Yalnız kayıt BU cihazınsa silinir; değilse `released: false` ve kayıt
    durur — başka cihazın kilidi eski cihazın çıkışıyla düşmez. Başlıksız
    çağrı da false: kimliği olmayan cihaz hiçbir kaydın sahibi değildir.
    İstemci bunu best-effort çağırır (kısa zaman aşımı, hata yutulur).
    """
    return {"status": "success",
            **device.release_device(user.uid, x_device_id)}
