import logging
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field

from core import cache
from core.auth import AuthUser, get_current_user
from core.entitlements import require_plus
from core.i18n import get_language
from core.messages import text
from services import astro_service, chart_context, profile_service, prompts

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


#: Takvim ufku (R2-Z1): 30 → 90 gün. Analiz kararı — kullanıcı "önündeki
#: 90 günü" tek bakışta görmeli; hesap LLM'siz, maliyet yalnız CPU.
TRANSIT_CALENDAR_DAYS = 90


@router.get("/transit-calendar")
def transit_calendar(user: AuthUser = Depends(require_plus("transit_calendar")),
                     lang: str = Depends(get_language)):
    """Kişisel transit takvimi (T3/R2-Z1): 90 günün kesinleşmeleri ve
    istasyonları, tema + ton etiketiyle.

    Jeton YOK — LLM çağrısı olmayan ham hesap. Doğum verisi istekten değil
    PROFİLDEN gelir: takvim "senin haritan" iddiasında olduğu için yalnızca
    gerçekten girilmiş doğum kaydıyla üretilir (chart_context kuralı).
    Önbellek doğum verisine anahtarlı ve dilden bağımsız: aynı doğum
    bilgisine sahip herkes aynı ham takvimi paylaşır, adlar yanıt anında
    isteğin dilinde kurulur. Tema/ton (sinyal kartlarıyla aynı tablolar)
    determinist olduğu için önbelleğe zenginleştirilmiş HALİ girer.
    """
    try:
        profile = profile_service.get_profile(user.uid)
        if not chart_context.has_birth_data(profile):
            raise HTTPException(status_code=400,
                                detail=text("birth.missing", lang))
        birth = profile_service.birth_kwargs(profile)
        saat_biliniyor = bool(str(profile.get("birthTime") or "").strip())

        from services import predict_service, signal_service
        # Anahtarda BUGÜN de var: pencere takvim gününe sabitlenir; yalnız
        # TTL olsaydı gece 23:50'de dolan kayıt ertesi günü dünkü
        # pencereyle karşılardı. Sinyal sürümü de anahtarda: tema/ton
        # tabloları değişince 24 saatlik eski kayıt servis edilmesin.
        import datetime as dt
        anahtar = ("transit-cal-{calc}-s{sig}-{gun_sayisi}"
                   "-{year}{month:02d}{day:02d}"
                   "-{hour:02d}{minute:02d}-{city}-{nation}-{hk}"
                   "-{bugun}").format(
            calc=predict_service.PREDICT_CALC_VERSION,
            sig=signal_service.SIGNAL_CALC_VERSION,
            gun_sayisi=TRANSIT_CALENDAR_DAYS, hk=saat_biliniyor,
            bugun=dt.datetime.now(dt.timezone.utc).date().isoformat(),
            **{k: birth[k] for k in ("year", "month", "day", "hour",
                                     "minute", "city", "nation")})
        cal = cache.get(anahtar)
        if cal is None:
            cal = predict_service.transit_calendar(
                **birth, hour_known=saat_biliniyor,
                days=TRANSIT_CALENDAR_DAYS)
            # Tema/ton: natal olgular önbellekli (chart_facts, 180 gün);
            # üretilemezse olaylar temasız kalır — takvim yine çalışır.
            natal = chart_context.chart_facts(user.uid, profile)
            cal = {**cal, "events": signal_service.enrich_events(
                cal.get("events") or [], natal)}
            cache.set(anahtar, cal, ttl_seconds=24 * 3600)
        return {"status": "success",
                "data": prompts.localize_transit_calendar(lang, cal)}
    except HTTPException:
        raise
    except Exception as e:
        raise _internal(e, "transit-calendar", lang)


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
