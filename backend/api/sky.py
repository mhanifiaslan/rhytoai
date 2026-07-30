import logging

from fastapi import APIRouter, Depends, HTTPException

from core.auth import get_current_user
from core.i18n import get_language
from core.messages import text
from services import prompts
from services.sky_service import get_sky_now

logger = logging.getLogger(__name__)
router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/now")
def sky_now(lang: str = Depends(get_language)):
    try:
        sky = get_sky_now()
        # Hesap paylaşımlı önbellekten geliyor ve dilden bağımsız; ay evresinin
        # adı isteğin dilinde burada ekleniyor.
        return {"status": "success", "data": {
            **sky,
            "moon_phase": prompts.localize_moon_phase(
                lang, sky.get("moon_phase")),
        }}
    except Exception as e:
        # Ham istisna metni kullanıcıya gösterilmez (bkz. core/messages.py).
        logger.exception("Gökyüzü ucunda hata", exc_info=e)
        raise HTTPException(status_code=500, detail=text("internal", lang))
