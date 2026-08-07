"""Yorum/rapor uçları: hesaplama + RAG + Gemini + önbellek tek çağrıda."""
import datetime as dt
import logging
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from core.auth import AuthUser, get_current_user
from core.i18n import get_language
from core.messages import text
from core.entitlements import (
    FREE_ICHING_PER_DAY,
    require_plus,
)
from core import device, entitlements, wallet
from services import (astro_service, bazi_service, birth_hexagram_service,
                      chart_context, notification_service, profile_service,
                      prompts, report_service)
from services.bazi_service import get_bazi_chart
from services.iching_service import cast_iching, enrich_cast
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

    # Doğum saati gerçekten biliniyor mu (Revize B1). `hour`'ı Optional
    # yapmak yerine ayrı bayrak: bu şema natal/sinastri uçlarıyla PAYLAŞIMLI
    # ve Batı haritası saatsiz ev hesabı ayrı bir ürün kararı. BaZi bayrağı
    # False görünce saat sütununu HİÇ kurmaz; diğer uçlar 12:00'la sürer.
    hour_known: bool = True


class IChingReportRequest(BaseModel):
    # None = soru verilmedi; varsayılan metin İSTEĞİN DİLİNDE uçta doldurulur
    # (Revize İ0). Şemadaki Türkçe sabit ("Geleceğim") İngilizce prompt'a
    # sızıyordu. Uzunluk sınırı da yeni: soru prompt'a ham giriyor.
    question: str | None = Field(default=None, max_length=280)
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
    sky = prompts.localize_sky(lang, get_sky_now())
    # Gün kovası isteğin sahibinin yerel gününden (D2): sunucu UTC'de ve
    # gece yarısından sonra kullanıcı dünkü yorumu görüyordu.
    report = report_service.horoscope_reading(
        sign, period, sky, lang=lang,
        today=entitlements.user_local_date(user.uid))
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
        sky = prompts.localize_sky(lang, get_sky_now())
        # birth: bugünün transitlerinin haritaya değdiği noktalar da okumaya
        # girsin (Revize R8) — ek LLM çağrısı yok, hesap yerel efemeris.
        report = report_service.daily_reading(
            user.uid, natal, sky, lang=lang, birth=_natal_kwargs(data),
            today=entitlements.user_local_date(user.uid))
        return {"status": "success", "data": {
            "reading": report["text"], "cached": report.get("cached", False),
            "sun_sign": natal["sun_sign"], "moon_sign": natal["moon_sign"],
            "ascendant": natal["ascendant"],
            "moon_phase": sky["moon_phase"],
            "retrogrades": sky["retrogrades"],
        }}
    except HTTPException:
        # Cuzdan 402'si dahil kasitli HTTP hatalari 500'e sarilmasin.
        raise
    except Exception as e:
        raise _internal(e, "daily", lang)


@router.post("/natal")
def natal(data: BirthData,
          user: AuthUser = Depends(require_plus("natal_report")),
          lang: str = Depends(get_language)):
    try:
        chart = astro_service.get_natal_chart(**_natal_kwargs(data))
        # Token düşümü önbellek kaçırıldığında, LLM çağrısından hemen önce
        # (bkz. _cached_generate): aynı rapora ikinci bakış ücretsiz.
        report = report_service.natal_report(
            user.uid, chart, lang=lang,
            spend=wallet.spender(user.uid, "natal", lang=lang),
            refund=lambda: wallet.refund_spend(user.uid, "natal"))
        return {"status": "success", "data": {
            "chart": prompts.localize_chart(lang, chart),
            "report": report["text"],
        }}
    except HTTPException:
        # Cuzdan 402'si dahil kasitli HTTP hatalari 500'e sarilmasin.
        raise
    except Exception as e:
        raise _internal(e, "natal", lang)


@router.post("/bazi")
def bazi(data: BirthData,
         user: AuthUser = Depends(require_plus("bazi")),
         lang: str = Depends(get_language)):
    try:
        chart = get_bazi_chart(
            year=data.year, month=data.month, day=data.day,
            # Saat bilinmiyorsa None: motor saat sütununu HİÇ kurmaz
            # (12:00 varsaymak öğle doğumu uydurmaktı — Revize B1).
            hour=data.hour if data.hour_known else None,
            minute=data.minute, city=data.city, nation=data.nation,
            gender=data.gender, name=data.name,
        )
        report = report_service.bazi_report(
            user.uid, chart, lang=lang,
            spend=wallet.spender(user.uid, "bazi", lang=lang),
            refund=lambda: wallet.refund_spend(user.uid, "bazi"))
        # Ekranda gosterilen element/hayvan/On Tanri adlari da dile gore.
        return {"status": "success", "data": {
            "chart": prompts.localize_bazi(lang, chart),
            "report": report["text"],
        }}
    except HTTPException:
        # Cuzdan 402'si dahil kasitli HTTP hatalari 500'e sarilmasin.
        raise
    except Exception as e:
        raise _internal(e, "bazi", lang)


@router.post("/iching")
def iching(req: IChingReportRequest,
           user: AuthUser = Depends(get_current_user),
           lang: str = Depends(get_language),
           x_device_id: str | None = Header(default=None)):
    """I Ching hafif gunluk ritual olarak ucretsiz kalir, ama gunde bir cekilis.

    Sinirsiz olsaydi ucretsiz kullanici basina acik uclu LLM maliyeti olusurdu;
    gunde bir cekilis hem ritueli korur hem maliyeti ongorulur tutar.
    """
    # Tek cihaz kilidi (yalnızca abonede etkili) harcamadan önce.
    device.enforce_single_device(user.uid, x_device_id, lang=lang)

    # Soru kapısı (R10→R11): niyetsiz girişler günde tek çekim hakkını
    # harcamadan çevrilir. Hüküm LLM'de (kelime listesi yalnız bariz
    # durumlarda ön filtre): "beni seviyor musun" uygulamaya yöneltilmiş
    # sayılır ve Sohbet'e yönlendirilir, "beni seviyor mu" geçer.
    if req.question:
        hukum = report_service.iching_question_verdict(req.question, lang)
        if hukum != "VALID":
            raise HTTPException(
                status_code=422,
                detail=text("iching.question_chat" if hukum == "CHAT"
                            else "iching.question_invalid", lang))

    # Günlük ücretsiz hak + cüzdan tek kapıda. Peşin harcama YOK: dönen
    # geri çağrılar önbellek kaçırıldığında çalışır — abone, saatlik
    # önbellekteki aynı çekilişe ikinci bakışında ödemez.
    spend_cb, refund_cb = wallet.metered_callbacks(
        user, "iching", FREE_ICHING_PER_DAY, lang=lang)
    try:
        # Soru verilmediyse varsayılan metin İSTEĞİN DİLİNDE (Revize İ0).
        soru = req.question or prompts.get(lang).ICHING_DEFAULT_QUESTION
        cast = cast_iching(soru, method=req.method)

        # Çekim günü bağlamı (İ2): günün/ayın sütunları + kullanıcının Day
        # Master'ı. Klasik danışma çekimi, çekildiği günün İÇİNDE okunur.
        # Gün, kullanıcının senkronlanan saat diliminden alınır (bildirim
        # altyapısının alanı); yoksa UTC — temel beyanla taşınır.
        profile = profile_service.get_profile(user.uid)
        tz = notification_service.user_timezone(profile or {})
        bugun = dt.datetime.now(dt.timezone.utc).astimezone(tz).date()
        basis = "profile_tz" if (profile or {}).get("timezone") else "utc"
        dm_element = None
        if profile and chart_context.has_birth_data(profile):
            bazi_ozet = chart_context.bazi_facts(user.uid, profile)
            dm_element = ((bazi_ozet or {}).get("day_master")
                          or {}).get("element")
        cast = enrich_cast(
            cast,
            day_pillar=bazi_service.day_pillar_for_date(bugun),
            month_pillar=bazi_service.month_pillar_for_date(bugun),
            day_master_element=dm_element,
            basis=basis)
        report = report_service.iching_reading(user.uid, cast, lang=lang,
                                               spend=spend_cb,
                                               refund=refund_cb)
        return {"status": "success", "data": {
            "cast": prompts.localize_iching(lang, cast),
            "report": report["text"],
        }}
    except HTTPException:
        # Cuzdan 402'si dahil kasitli HTTP hatalari 500'e sarilmasin.
        raise
    except Exception as e:
        raise _internal(e, "iching", lang)


class SolarReturnRequest(BirthData):
    #: Belirli bir SR yılı istenirse (varsayılan: aktif yıl).
    target_year: int | None = Field(default=None, ge=1900, le=2100)


@router.post("/solar-return")
def solar_return(data: SolarReturnRequest,
                 user: AuthUser = Depends(require_plus("solar_return")),
                 lang: str = Depends(get_language)):
    """Yıl haritası (T1): aktif güneş dönüşü + LLM yıl okuması.

    Harita, kayıtlıysa kullanıcının YAŞADIĞI şehre kurulur (D3): yıl
    haritası doğum gününde bulunulan yere kurulur ve konum Yükselen'i
    tamamen değiştirir. Şehir istekten değil PROFİLDEN okunur — "senin
    haritan" iddiası kullanıcının kaydına dayanmalı (chart_context kuralı).
    """
    try:
        from services import predict_service
        profil = profile_service.get_profile(user.uid) or {}
        sr = predict_service.solar_return(
            data.name, data.year, data.month, data.day,
            data.hour, data.minute, data.city, data.nation,
            hour_known=data.hour_known, target_year=data.target_year,
            relocation_city=(profil.get("residenceCity") or "").strip() or None,
            relocation_nation=profil.get("residenceNation"))
        report = report_service.solar_return_report(
            user.uid, sr, lang=lang,
            spend=wallet.spender(user.uid, "solar_return", lang=lang),
            refund=lambda: wallet.refund_spend(user.uid, "solar_return"))
        return {"status": "success", "data": {
            "solar_return": prompts.localize_chart(lang, sr),
            "report": report["text"],
        }}
    except HTTPException:
        raise
    except Exception as e:
        raise _internal(e, "solar-return", lang)


@router.post("/progressions")
def progressions(data: BirthData,
                 user: AuthUser = Depends(require_plus("progressions")),
                 lang: str = Depends(get_language)):
    """İç Takvim (T2): ikincil progresyon + solar arc + LLM okuması."""
    try:
        from services import predict_service
        prog = predict_service.secondary_progressions(
            data.name, data.year, data.month, data.day,
            data.hour, data.minute, data.city, data.nation,
            hour_known=data.hour_known)
        hits = predict_service.solar_arc_hits(
            data.name, data.year, data.month, data.day,
            data.hour, data.minute, data.city, data.nation,
            hour_known=data.hour_known)
        report = report_service.progressions_report(
            user.uid, prog, hits, lang=lang,
            spend=wallet.spender(user.uid, "progressions", lang=lang),
            refund=lambda: wallet.refund_spend(user.uid, "progressions"))
        return {"status": "success", "data": {
            "progressions": prompts.localize_progressions(lang, prog, hits),
            "report": report["text"],
        }}
    except HTTPException:
        raise
    except Exception as e:
        raise _internal(e, "progressions", lang)


@router.post("/birth-hexagram")
def birth_hexagram(data: BirthData,
                   user: AuthUser = Depends(require_plus("birth_hexagram")),
                   lang: str = Depends(get_language)):
    """Doğum Heksagramı — kalıcı kimlik katmanı (Revize İ5).

    Çekim değil: doğum anındaki Güneş boylamının 64 kapı çarkındaki yeri.
    Natal raporla aynı sınıf — Rytho+ + 5 token, 30 gün önbellek.
    """
    try:
        konum = birth_hexagram_service.birth_hexagram(
            year=data.year, month=data.month, day=data.day,
            hour=data.hour if data.hour_known else None,
            minute=data.minute, city=data.city, nation=data.nation,
        )
        report = report_service.birth_hexagram_report(
            user.uid, konum, lang=lang,
            spend=wallet.spender(user.uid, "birth_hexagram", lang=lang),
            refund=lambda: wallet.refund_spend(user.uid, "birth_hexagram"))
        return {"status": "success", "data": {
            "position": {
                "gate": konum["gate"],
                "line": konum["line"] if konum["hour_known"] else None,
                "longitude": konum["longitude"],
                "hour_known": konum["hour_known"],
                "alternate_gate": konum.get("alternate_gate"),
            },
            "hexagram": prompts.localize_hexagram(lang, konum["hexagram"]),
            "alternate_hexagram": prompts.localize_hexagram(
                lang, konum["alternate_hexagram"])
            if konum.get("alternate_hexagram") else None,
            # Kapı pasajı (İ8): ekran "Kapının Dokusu" kartını buradan kurar.
            "gate_text": (konum.get("gate_passage") or {}).get(
                "gate_en" if lang == "en" else "gate_tr"),
            "report": report["text"],
        }}
    except HTTPException:
        raise
    except Exception as e:
        raise _internal(e, "birth_hexagram", lang)


@router.get("/iching/status")
def iching_status(user: AuthUser = Depends(get_current_user)):
    """Çekim hakkı durumu — SALT OKUR, hak düşmez (Revize İ6).

    UI "bugünkü hak: 1/1" rozetini buradan kurar; eskiden kota yalnız
    402'de, yani hak BİTİNCE görünür oluyordu. Abone bilgisi de döner:
    abonede rozet günlük hak yerine token bedelini gösterir.
    """
    _, kalan = entitlements.quota_state(user.uid, "iching",
                                        FREE_ICHING_PER_DAY)
    return {"status": "success", "data": {
        "free_limit": FREE_ICHING_PER_DAY,
        "free_remaining": kalan,
        "token_cost": wallet.TOKEN_COSTS["iching"],
        "subscriber": entitlements.is_subscriber(user.uid),
    }}


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
    sky = prompts.localize_sky(lang, get_sky_now())
    # Bedeli İSTEYEN taraf öder; arkadaş aynı gün içinde aynı okumayı
    # önbellekten ücretsiz görür (anahtar çift bazlı).
    report = report_service.dyad_reading(
        user.uid, req.friend_uid,
        me.get("displayName") or "Gezgin", friend.get("displayName") or "Gezgin",
        synastry, sky, lang=lang,
        spend=wallet.spender(user.uid, "dyad", lang=lang),
        refund=lambda: wallet.refund_spend(user.uid, "dyad"),
    )

    return {"status": "success", "data": {
        "reading": report["text"],
        "cached": report.get("cached", False),
        "fallback": report.get("fallback", False),
        "generated_for": report.get("generated_for"),
        # Yalnızca türetilmiş, hassas olmayan alanlar döner — ham doğum verisi asla.
        "friend_sun_sign": prompts.sign_from_point(
            lang, synastry["person2"].get("sun")),
        "my_sun_sign": prompts.sign_from_point(
            lang, synastry["person1"].get("sun")),
    }}


@router.post("/synastry")
def synastry(req: SynastryReportRequest,
             user: AuthUser = Depends(require_plus("synastry")),
             lang: str = Depends(get_language)):
    try:
        result = astro_service.get_synastry(
            _natal_kwargs(req.person1), _natal_kwargs(req.person2)
        )
        report = report_service.synastry_report(
            user.uid, result, lang=lang,
            spend=wallet.spender(user.uid, "synastry", lang=lang),
            refund=lambda: wallet.refund_spend(user.uid, "synastry"))
        return {"status": "success", "data": {"synastry": result, "report": report["text"]}}
    except HTTPException:
        # Cuzdan 402'si dahil kasitli HTTP hatalari 500'e sarilmasin.
        raise
    except Exception as e:
        raise _internal(e, "synastry", lang)
