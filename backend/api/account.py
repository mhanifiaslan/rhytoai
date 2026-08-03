"""Hesap uçları — şimdilik yalnızca silme.

Silme mağaza zorunluluğudur (Apple 5.1.1(v), Google Play). İstemci tarafında
Firestore kurallarıyla yapılamaz: kullanıcı BAŞKA kullanıcıların dokümanlarına
(karşılıklı arkadaşlık kaydı, gönderdiği tepkiler) ve sunucuya kapalı
koleksiyonlara (hafıza, abonelik, önbellek) dokunamaz. Bu yüzden sunucuda.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.auth import AuthUser, get_current_user
from core.i18n import get_language
from core.messages import text
from services import account_service, phone_service

logger = logging.getLogger(__name__)
router = APIRouter()


class DeleteResult(BaseModel):
    status: str
    #: Neyin kaç adet silindiği. İstemci göstermez; destek ve test için.
    deleted: dict[str, int]


@router.delete("/me", response_model=DeleteResult)
def delete_me(user: AuthUser = Depends(get_current_user),
              lang: str = Depends(get_language)) -> DeleteResult:
    """Oturum açmış kullanıcının hesabını ve tüm verisini siler.

    Yalnızca **kendi** hesabını siler: hedef kimlik gövdeden değil, doğrulanmış
    oturumdan alınır. İstemcinin uid göndermesine izin verilseydi, geçerli bir
    oturumu olan herkes başkasının hesabını silebilirdi.

    Geri alınamaz. Onay akışı istemcide (Profil > Hesabı sil).
    """
    if user.anonymous:
        # Geliştirme modundaki anonim kullanıcı; silinecek gerçek hesap yok.
        raise HTTPException(status_code=400, detail=text("auth_required", lang))

    try:
        sayim = account_service.delete_account(user.uid)
    except Exception as exc:
        logger.exception("Hesap silinemedi (%s)", user.uid, exc_info=exc)
        raise HTTPException(status_code=500, detail=text("internal", lang))

    return DeleteResult(status="deleted", deleted=dict(sayim))


@router.post("/phone/sync")
def sync_phone(user: AuthUser = Depends(get_current_user),
               lang: str = Depends(get_language)):
    """Doğrulanmış telefonu eşleme dizinine kaydeder (Revize R2).

    Numara İSTEMCİDEN ALINMAZ: Firebase Phone Auth doğrulaması bitmiş numara
    ID token'ının `phone_number` claim'inde gelir. Gövdesiz bir uç — istemci
    yalnızca "bağladım, kaydet" der.
    """
    if not user.phone:
        # Token'da numara yok: istemci bağlamayı bitirmeden çağırmış ya da
        # token henüz tazelenmemiş (istemci linkten sonra getIdToken(true)
        # çağırmalı).
        raise HTTPException(status_code=400,
                            detail=text("phone.not_verified", lang))
    try:
        sonuc = phone_service.sync_phone(user.uid, user.phone)
    except phone_service.PhoneTakenError:
        raise HTTPException(status_code=409,
                            detail=text("phone.taken", lang))
    except Exception as exc:
        logger.exception("Telefon kaydı yazılamadı (%s)", user.uid,
                         exc_info=exc)
        raise HTTPException(status_code=500, detail=text("internal", lang))

    return {"status": "success", **sonuc}
