"""Yorum/rapor uçları: hesaplama + RAG + Gemini + önbellek tek çağrıda."""
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.auth import AuthUser, get_current_user
from services import astro_service, report_service
from services.bazi_service import get_bazi_chart
from services.iching_service import cast_iching
from services.sky_service import get_sky_now

router = APIRouter()


class BirthData(BaseModel):
    name: str = "Gezgin"
    year: int = Field(ge=1900, le=2100)
    month: int = Field(ge=1, le=12)
    day: int = Field(ge=1, le=31)
    hour: int = Field(default=12, ge=0, le=23)
    minute: int = Field(default=0, ge=0, le=59)
    city: str = "Istanbul"
    nation: Optional[str] = None
    gender: str = "female"


class IChingReportRequest(BaseModel):
    question: str = "Geleceğim"
    method: Literal["coins", "yarrow"] = "coins"


class SynastryReportRequest(BaseModel):
    person1: BirthData
    person2: BirthData


def _natal_kwargs(d: BirthData) -> dict:
    return dict(name=d.name, year=d.year, month=d.month, day=d.day,
                hour=d.hour, minute=d.minute, city=d.city, nation=d.nation)


@router.post("/daily")
def daily(data: BirthData, user: AuthUser = Depends(get_current_user)):
    try:
        natal = astro_service.get_natal_chart(**_natal_kwargs(data))
        sky = get_sky_now()
        report = report_service.daily_reading(user.uid, natal, sky)
        return {"status": "success", "data": {
            "reading": report["text"], "cached": report.get("cached", False),
            "sun_sign": natal["sun_sign"], "moon_sign": natal["moon_sign"],
            "ascendant": natal["ascendant"],
            "moon_phase": sky["moon_phase"], "retrogrades": sky["retrogrades"],
        }}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/natal")
def natal(data: BirthData, user: AuthUser = Depends(get_current_user)):
    try:
        chart = astro_service.get_natal_chart(**_natal_kwargs(data))
        report = report_service.natal_report(user.uid, chart)
        return {"status": "success", "data": {"chart": chart, "report": report["text"]}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bazi")
def bazi(data: BirthData, user: AuthUser = Depends(get_current_user)):
    try:
        chart = get_bazi_chart(
            year=data.year, month=data.month, day=data.day, hour=data.hour,
            minute=data.minute, city=data.city, nation=data.nation,
            gender=data.gender, name=data.name,
        )
        report = report_service.bazi_report(user.uid, chart)
        return {"status": "success", "data": {"chart": chart, "report": report["text"]}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/iching")
def iching(req: IChingReportRequest, user: AuthUser = Depends(get_current_user)):
    try:
        cast = cast_iching(req.question, method=req.method)
        report = report_service.iching_reading(user.uid, cast)
        return {"status": "success", "data": {"cast": cast, "report": report["text"]}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/synastry")
def synastry(req: SynastryReportRequest, user: AuthUser = Depends(get_current_user)):
    try:
        result = astro_service.get_synastry(
            _natal_kwargs(req.person1), _natal_kwargs(req.person2)
        )
        report = report_service.synastry_report(user.uid, result)
        return {"status": "success", "data": {"synastry": result, "report": report["text"]}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
