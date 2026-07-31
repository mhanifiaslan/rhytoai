import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.auth import get_current_user
from core.i18n import get_language
from core.messages import text
from services import prompts
from services.bazi_service import get_bazi_chart

logger = logging.getLogger(__name__)
router = APIRouter(dependencies=[Depends(get_current_user)])


class BaziRequest(BaseModel):
    name: str = "Gezgin"
    year: int = Field(ge=1900, le=2100)
    month: int = Field(ge=1, le=12)
    day: int = Field(ge=1, le=31)
    hour: int = Field(default=12, ge=0, le=23)
    minute: int = Field(default=0, ge=0, le=59)
    city: str = "Istanbul"
    nation: Optional[str] = None
    gender: str = "female"


@router.post("/chart")
def bazi_chart(data: BaziRequest, lang: str = Depends(get_language)):
    try:
        chart = get_bazi_chart(
            year=data.year, month=data.month, day=data.day,
            hour=data.hour, minute=data.minute,
            city=data.city, nation=data.nation,
            gender=data.gender, name=data.name,
        )
        return {"status": "success", "data": prompts.localize_bazi(lang, chart)}
    except Exception as e:
        logger.exception("BaZi ucunda hata", exc_info=e)
        raise HTTPException(status_code=500, detail=text("internal", lang))
