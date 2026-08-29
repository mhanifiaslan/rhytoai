"""Hesap uçları — silme, rıza, telefon eşleme, günlük.

Silme mağaza zorunluluğudur (Apple 5.1.1(v), Google Play). İstemci tarafında
Firestore kurallarıyla yapılamaz: kullanıcı BAŞKA kullanıcıların dokümanlarına
(karşılıklı arkadaşlık kaydı, gönderdiği tepkiler) ve sunucuya kapalı
koleksiyonlara (hafıza, abonelik, önbellek) dokunamaz. Bu yüzden sunucuda.

Günlük (R2-G1) de burada: kayıtlar hafıza dokümanında (``private/memory``)
yaşar — istemci o dokümanı doğrudan okuyamaz, uçlar tek kapıdır. Hesap
silindiğinde hafızayla birlikte günlük de silinir (mevcut akış).
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.auth import AuthUser, get_current_user
from core.i18n import get_language
from core.messages import text
from services import (account_service, consent_service, memory_service,
                      phone_service)

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


class ConsentRequest(BaseModel):
    #: İstemcinin GÖSTERDİĞİ metin sürümü — kayıt bunu tutar (eski istemci
    #: eski metni göstermiş olabilir; ispat gördüğü şeye bağlanmalı).
    version: int = consent_service.TERMS_CONSENT_VERSION


@router.post("/consent")
def record_consent(req: ConsentRequest,
                   user: AuthUser = Depends(get_current_user),
                   lang: str = Depends(get_language)):
    """Kullanım şartları + gizlilik kabulünü kaydeder (O3).

    Sihirbazın karşılama adımı çağırır. Google/Apple girişlerinde bugüne
    dek HİÇBİR onay kutusu yoktu; bu uç her sağlayıcı için ispatlanabilir
    clickwrap kaydı üretir. Uçlarda ZORLANMAZ — eski kullanıcılar
    kilitlenmez, kayıt yalnız tutulur.
    """
    if not consent_service.grant_terms_consent(user.uid, req.version, lang):
        raise HTTPException(status_code=500, detail=text("internal", lang))

    # OT6: deneme hoş geldin jetonu — onboarding bitişinde bir kez.
    # Defter kimliği hesap başına sabit (idempotent): yasal metin sürümü
    # yükselince yeniden onay veren ESKİ kullanıcı ikinci kez alamaz;
    # `in_trial` kapısı da yalnız yeni hesaplara açar. Jeton yazılamazsa
    # onay kaydı yine başarılıdır — deneme jetonu bir ek, onayın kendisi
    # değil.
    from core import entitlements, wallet
    try:
        if entitlements.in_trial(user.uid):
            wallet.credit_promo(user.uid, wallet.TRIAL_PROMO_CODE,
                                wallet.TRIAL_TOKENS)
    except Exception as exc:
        logger.warning("Deneme jetonu yazilamadi (%s): %s", user.uid, exc)

    return {"status": "success",
            "version": consent_service.TERMS_CONSENT_VERSION}


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


# ---------------------------------------------------------------------------
# Günlük (R2-G1)
# ---------------------------------------------------------------------------

class DiaryEntryRequest(BaseModel):
    text: str = Field(min_length=1, max_length=memory_service.MAX_DIARY_CHARS)
    #: signal_service.THEMES kümesinden; verilmezse temasız kayıt.
    theme: str | None = Field(default=None, max_length=20)


@router.get("/diary")
def diary(user: AuthUser = Depends(get_current_user),
          lang: str = Depends(get_language)):
    """Günlük girişleri, yeniden eskiye. LLM yok, jeton yok."""
    try:
        return {"status": "success",
                "data": {"entries": memory_service.get_diary(user.uid),
                         "themes": list(memory_service.DIARY_THEMES)}}
    except Exception as exc:
        logger.exception("Günlük okunamadı (%s)", user.uid, exc_info=exc)
        raise HTTPException(status_code=500, detail=text("internal", lang))


@router.post("/diary")
def add_diary(req: DiaryEntryRequest,
              user: AuthUser = Depends(get_current_user),
              lang: str = Depends(get_language)):
    """Tek satırlık giriş ekler; giriş sohbetin hafıza fısıltısına da girer.

    Böylece "son bir ayda ne oldu?" sorusuna Rytho, kullanıcının KENDİ
    kayıtları + o günlerin gökyüzüyle cevap verebilir — analizdeki
    "astrolojik günlük" fikrinin çekirdeği.
    """
    try:
        giris = memory_service.add_diary_entry(
            user.uid, req.text, theme=req.theme)
    except Exception as exc:
        logger.exception("Günlük yazılamadı (%s)", user.uid, exc_info=exc)
        raise HTTPException(status_code=500, detail=text("internal", lang))
    if giris is None:
        raise HTTPException(status_code=400, detail=text("internal", lang))
    return {"status": "success", "data": giris}


@router.delete("/diary/{entry_id}")
def delete_diary(entry_id: str,
                 user: AuthUser = Depends(get_current_user),
                 lang: str = Depends(get_language)):
    """Girişi siler. Günlük kullanıcının kendi sesi — silmek de onun hakkı."""
    try:
        silindi = memory_service.delete_diary_entry(user.uid, entry_id)
    except Exception as exc:
        logger.exception("Günlük silinemedi (%s)", user.uid, exc_info=exc)
        raise HTTPException(status_code=500, detail=text("internal", lang))
    if not silindi:
        raise HTTPException(status_code=404, detail=text("internal", lang))
    return {"status": "success"}
