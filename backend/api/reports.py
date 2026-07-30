"""Yorum/rapor uçları: hesaplama + RAG + Gemini + önbellek tek çağrıda."""
import logging
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.auth import AuthUser, get_current_user
from core.i18n import get_language
from core.messages import text
from core.entitlements import (
    FREE_ICHING_PER_DAY,
    enforce_daily_quota,
    require_plus,
)
from services import astro_service, profile_service, prompts, report_service
from services.bazi_service import get_bazi_chart
from services.iching_service import cast_iching
from services.sky_service import get_sky_now

logger = logging.getLogger(__name__)
router = APIRouter()


def _internal(exc: Exception, uç: str, lang: str) -> HTTPException:
    """İstisnayı sunucuda loglar, kullanıcıya sabit bir metinle döner.

    Uçlar eskiden `detail=str(e)` döndürüyordu: istemci `detail` alanını
    doğrudan ekrana bastığı için kullanıcı Python istisna metni görüyordu ve
    sunucunun iç yapısı dışarı sızıyordu.
    """
    logger.exception("%s ucunda hata", uç, exc_info=exc)
    return HTTPException(status_code=500, detail=text("internal", lang))


# İngilizce burç anahtarı -> Türkçe ad (Koç→Balık sırası korunur).
SIGN_TR = {
    "aries": "Koç", "taurus": "Boğa", "gemini": "İkizler", "cancer": "Yengeç",
    "leo": "Aslan", "virgo": "Başak", "libra": "Terazi", "scorpio": "Akrep",
    "sagittarius": "Yay", "capricorn": "Oğlak", "aquarius": "Kova",
    "pisces": "Balık",
}

SignName = Literal[
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]


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


class DyadRequest(BaseModel):
    friend_uid: str = Field(min_length=1, max_length=128)


def _natal_kwargs(d: BirthData) -> dict:
    return dict(name=d.name, year=d.year, month=d.month, day=d.day,
                hour=d.hour, minute=d.minute, city=d.city, nation=d.nation)


@router.get("/horoscope/{sign}")
def horoscope(
    sign: SignName,
    period: Literal["daily", "weekly", "monthly"] = "daily",
    user: AuthUser = Depends(get_current_user),
    lang: str = Depends(get_language),
):
    """Burç bazlı genel yorum — ücretsiz katmanın omurgası.

    Kullanıcıdan bağımsızdır: yorum (burç, dönem, tarih kovası) anahtarıyla
    paylaşımlı önbellekte tutulur, yani dönem başına burç başına en fazla bir
    LLM çağrısı yapılır. Kullanıcı sayısı arttıkça maliyet artmaz.

    Kimlik doğrulaması istemci tarafında zaten mevcut (anonim Firebase oturumu
    dahil) ve ucu kötüye kullanıma karşı korur; abonelik gerektirmez.
    """
    sky = get_sky_now()
    report = report_service.horoscope_reading(sign, period, sky, lang=lang)
    return {"status": "success", "data": {
        "sign": sign,
        "sign_tr": SIGN_TR[sign],
        "sign_name": prompts.sign_name(lang, sign),
        "lang": lang,
        "period": period,
        "reading": report["text"],
        "cached": report.get("cached", False),
        "fallback": report.get("fallback", False),
        "generated_for": report.get("generated_for"),
        "moon_phase": sky["moon_phase"],
        "retrogrades": sky["retrogrades"],
    }}


@router.post("/daily")
def daily(data: BirthData,
          user: AuthUser = Depends(require_plus("personal_daily")),
          lang: str = Depends(get_language)):
    """Kisiye ozel gunluk okuma — Rytho+ .

    Ucretsiz katmanin gunluk icerigi /horoscope'tur: o, kullanicidan bagimsiz
    ve paylasimli onbellekten servis edilir. Buradaki okuma ise kullanicinin
    natal haritasiyla uretildigi icin kullanici basina bir LLM cagrisi
    gerektirir; abonelik siniri tam olarak bu maliyet farkindan geciyor.
    """
    try:
        natal = astro_service.get_natal_chart(**_natal_kwargs(data))
        sky = get_sky_now()
        report = report_service.daily_reading(user.uid, natal, sky, lang=lang)
        return {"status": "success", "data": {
            "reading": report["text"], "cached": report.get("cached", False),
            "sun_sign": natal["sun_sign"], "moon_sign": natal["moon_sign"],
            "ascendant": natal["ascendant"],
            "moon_phase": sky["moon_phase"], "retrogrades": sky["retrogrades"],
        }}
    except Exception as e:
        raise _internal(e, "daily", lang)


@router.post("/natal")
def natal(data: BirthData,
          user: AuthUser = Depends(require_plus("natal_report")),
          lang: str = Depends(get_language)):
    try:
        chart = astro_service.get_natal_chart(**_natal_kwargs(data))
        report = report_service.natal_report(user.uid, chart, lang=lang)
        return {"status": "success", "data": {"chart": chart, "report": report["text"]}}
    except Exception as e:
        raise _internal(e, "natal", lang)


@router.post("/bazi")
def bazi(data: BirthData,
         user: AuthUser = Depends(require_plus("bazi")),
         lang: str = Depends(get_language)):
    try:
        chart = get_bazi_chart(
            year=data.year, month=data.month, day=data.day, hour=data.hour,
            minute=data.minute, city=data.city, nation=data.nation,
            gender=data.gender, name=data.name,
        )
        report = report_service.bazi_report(user.uid, chart, lang=lang)
        return {"status": "success", "data": {"chart": chart, "report": report["text"]}}
    except Exception as e:
        raise _internal(e, "bazi", lang)


@router.post("/iching")
def iching(req: IChingReportRequest,
           user: AuthUser = Depends(get_current_user),
           lang: str = Depends(get_language)):
    """I Ching hafif gunluk ritual olarak ucretsiz kalir, ama gunde bir cekilis.

    Sinirsiz olsaydi ucretsiz kullanici basina acik uclu LLM maliyeti olusurdu;
    gunde bir cekilis hem ritueli korur hem maliyeti ongorulur tutar.
    """
    enforce_daily_quota(user, "iching", FREE_ICHING_PER_DAY, lang=lang)
    try:
        cast = cast_iching(req.question, method=req.method)
        report = report_service.iching_reading(user.uid, cast, lang=lang)
        return {"status": "success", "data": {"cast": cast, "report": report["text"]}}
    except Exception as e:
        raise _internal(e, "iching", lang)


@router.post("/dyad")
def dyad(req: DyadRequest,
         user: AuthUser = Depends(require_plus("dyad")),
         lang: str = Depends(get_language)):
    """İki arkadaşın BUGÜNE özgü ilişki dinamiği.

    İstemci yalnızca arkadaşın kimliğini gönderir; iki doğum verisini de sunucu
    Firestore'dan okur ve yanıtta **döndürmez**. Böylece arkadaşın doğum
    tarihi/saati/yeri hiçbir zaman karşı istemciye ulaşmaz.
    """
    if req.friend_uid == user.uid:
        raise HTTPException(status_code=400, detail=text("dyad.self", lang))

    if not profile_service.are_friends(user.uid, req.friend_uid):
        raise HTTPException(status_code=403,
                            detail=text("dyad.not_friends", lang))

    me = profile_service.get_profile(user.uid)
    friend = profile_service.get_profile(req.friend_uid)
    if not me or not friend:
        raise HTTPException(status_code=404,
                            detail=text("dyad.profile_missing", lang))

    synastry = astro_service.get_synastry(
        profile_service.birth_kwargs(me), profile_service.birth_kwargs(friend)
    )
    sky = get_sky_now()
    report = report_service.dyad_reading(
        user.uid, req.friend_uid,
        me.get("displayName") or "Gezgin", friend.get("displayName") or "Gezgin",
        synastry, sky, lang=lang,
    )

    return {"status": "success", "data": {
        "reading": report["text"],
        "cached": report.get("cached", False),
        "fallback": report.get("fallback", False),
        "generated_for": report.get("generated_for"),
        # Yalnızca türetilmiş, hassas olmayan alanlar döner — ham doğum verisi asla.
        "friend_sun_sign": synastry["person2"]["sun"].get("sign_tr"),
        "my_sun_sign": synastry["person1"]["sun"].get("sign_tr"),
    }}


@router.post("/synastry")
def synastry(req: SynastryReportRequest,
             user: AuthUser = Depends(require_plus("synastry")),
             lang: str = Depends(get_language)):
    try:
        result = astro_service.get_synastry(
            _natal_kwargs(req.person1), _natal_kwargs(req.person2)
        )
        report = report_service.synastry_report(user.uid, result, lang=lang)
        return {"status": "success", "data": {"synastry": result, "report": report["text"]}}
    except Exception as e:
        raise _internal(e, "synastry", lang)
