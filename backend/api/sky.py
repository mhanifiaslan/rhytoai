import logging

from fastapi import APIRouter, Depends, HTTPException

from core.auth import get_current_user
from core.i18n import get_language
from core.messages import text
from services.sky_service import get_sky_now

logger = logging.getLogger(__name__)
router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/now")
def sky_now(lang: str = Depends(get_language)):
    try:
        return {"status": "success", "data": get_sky_now()}
    except Exception as e:
        # Ham istisna metni kullanıcıya gösterilmez (bkz. core/messages.py).
        logger.exception("Gökyüzü ucunda hata", exc_info=e)
        raise HTTPException(status_code=500, detail=text("internal", lang))
