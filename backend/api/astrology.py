import logging
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field

from core.auth import get_current_user
from core.i18n import get_language
from core.messages import text
from services import astro_service, prompts

logger = logging.getLogger(__name__)
router = APIRouter(dependencies=[Depends(get_current_user)])


def _internal(exc: Exception, uç: str, lang: str) -> HTTPException:
    """İstisnayı loglar, kullanıcıya sabit metinle döner (bkz. api/reports.py)."""
    logger.exception("%s ucunda hata", uç, exc_info=exc)
    return HTTPException(status_code=500, detail=text("internal", lang))


class BirthData(BaseModel):
    name: str = "Gezgin"
    year: int = Field(ge=1200, le=2100)
    month: int = Field(ge=1, le=12)
    day: int = Field(ge=1, le=31)
    hour: int = Field(default=12, ge=0, le=23)
    minute: int = Field(default=0, ge=0, le=59)
    city: str = "Istanbul"
    nation: Optional[str] = None


class NatalChartRequest(BirthData):
    zodiac_type: Literal["Tropical", "Sidereal"] = "Tropical"


class SynastryRequest(BaseModel):
    person1: BirthData
    person2: BirthData


def _birth_kwargs(d: BirthData) -> dict:
    return dict(
        name=d.name, year=d.year, month=d.month, day=d.day,
        hour=d.hour, minute=d.minute, city=d.city, nation=d.nation,
    )


@router.post("/natal-chart")
def natal_chart(data: NatalChartRequest, lang: str = Depends(get_language)):
    try:
        chart = astro_service.get_natal_chart(
            **_birth_kwargs(data), zodiac_type=data.zodiac_type
        )
        return {"status": "success", "data": prompts.localize_chart(lang, chart)}
    except Exception as e:
        raise _internal(e, "natal-chart", lang)


@router.post("/natal-chart/svg")
def natal_chart_svg(
    data: NatalChartRequest,
    theme: str = Query("dark", pattern="^(classic|dark|dark-high-contrast|light)$"),
    lang: str = Depends(get_language),
):
    try:
        svg = astro_service.get_natal_chart_svg(
            **_birth_kwargs(data), zodiac_type=data.zodiac_type, theme=theme
        )
        return Response(content=svg, media_type="image/svg+xml")
    except Exception as e:
        raise _internal(e, "natal-chart/svg", lang)


@router.post("/transits")
def transits(data: BirthData, lang: str = Depends(get_language)):
    try:
        result = astro_service.get_transits(**_birth_kwargs(data))
        return {"status": "success", "data": result}
    except Exception as e:
        raise _internal(e, "transits", lang)


@router.post("/synastry")
def synastry(req: SynastryRequest, lang: str = Depends(get_language)):
    try:
        result = astro_service.get_synastry(
            _birth_kwargs(req.person1), _birth_kwargs(req.person2)
        )
        return {"status": "success", "data": result}
    except Exception as e:
        raise _internal(e, "synastry", lang)


@router.post("/synastry/svg")
def synastry_svg(
    req: SynastryRequest,
    theme: str = Query("dark", pattern="^(classic|dark|dark-high-contrast|light)$"),
    lang: str = Depends(get_language),
):
    try:
        svg = astro_service.get_synastry_svg(
            _birth_kwargs(req.person1), _birth_kwargs(req.person2), theme=theme
        )
        return Response(content=svg, media_type="image/svg+xml")
    except Exception as e:
        raise _internal(e, "synastry/svg", lang)
