"""Astroloji hesaplama motoru — Kerykeion 5.x / Swiss Ephemeris.

Natal, transit ve sinastri hesaplamaları; Tropikal + Sidereal (Lahiri) destek;
SVG harita üretimi. Tüm konum çözümlemesi offline gazetteer/GeoNames ile yapılır
(kerykeion'un online modu kullanılmaz — deterministik ve ağ bağımsız).
"""
from __future__ import annotations

import datetime as dt
from typing import Any, Literal

from services.geo_service import resolve_city

# `kerykeion` MODUL DUZEYINDE ICE AKTARILMIYOR.
#
# Olculen bedel 212 ms ve bu sure her SOGUK BASLATMADA odeniyordu; Cloud Run
# konteyneri sifira inip geri kalktiginda kullanicinin gordugu bekleme buydu.
# Ice aktarma ilk hesaba ertelendi ve sonuc onbelleklendi.
#
# `warm_up()` acilista arka planda cagriliyor: acilis beklemiyor, ilk istek de
# bedeli odemiyor.
_ker = None


def _kerykeion():
    """Kerykeion modulunu ilk ihtiyac aninda ice aktarir."""
    global _ker
    if _ker is None:
        # Efemeris veri dosyaları kerykeion'dan ÖNCE yerine konur (T0):
        # sepl/semo yoksa Swiss Ephemeris sessizce Moshier'e düşüyordu.
        from core import ephemeris

        ephemeris.ensure()
        import kerykeion

        _ker = kerykeion
    return _ker


def warm_up() -> None:
    """Kerykeion'u arka planda yukler — acilisi bekletmez."""
    import threading

    threading.Thread(target=_kerykeion, daemon=True,
                     name="kerykeion-warmup").start()

ZodiacType = Literal["Tropical", "Sidereal"]

SIGN_TR = {
    "Ari": "Koç", "Tau": "Boğa", "Gem": "İkizler", "Can": "Yengeç",
    "Leo": "Aslan", "Vir": "Başak", "Lib": "Terazi", "Sco": "Akrep",
    "Sag": "Yay", "Cap": "Oğlak", "Aqu": "Kova", "Pis": "Balık",
}
SIGN_SYMBOL = {
    "Ari": "♈", "Tau": "♉", "Gem": "♊", "Can": "♋", "Leo": "♌", "Vir": "♍",
    "Lib": "♎", "Sco": "♏", "Sag": "♐", "Cap": "♑", "Aqu": "♒", "Pis": "♓",
}
PLANET_TR = {
    "Sun": "Güneş", "Moon": "Ay", "Mercury": "Merkür", "Venus": "Venüs",
    "Mars": "Mars", "Jupiter": "Jüpiter", "Saturn": "Satürn", "Uranus": "Uranüs",
    "Neptune": "Neptün", "Pluto": "Plüton", "Chiron": "Kiron",
    "Mean_Lilith": "Lilith", "True_North_Lunar_Node": "Kuzey Ay Düğümü",
    "True_South_Lunar_Node": "Güney Ay Düğümü", "Ascendant": "Yükselen",
    "Medium_Coeli": "Tepe Noktası (MC)", "Descendant": "Alçalan",
    "Imum_Coeli": "IC",
}
ASPECT_TR = {
    "conjunction": "Kavuşum", "opposition": "Karşıt", "trine": "Üçgen",
    "square": "Kare", "sextile": "Altmışlık", "quintile": "Beşlik",
    "quincunx": "Yüzelli",
}

_PLANET_NAMES = [
    "sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn",
    "uranus", "neptune", "pluto", "chiron", "mean_lilith",
    "true_north_lunar_node", "true_south_lunar_node",
]

#: Burç kodu -> element/nitelik (T4). Sayım dile bağımsız anahtarlarla
#: yapılır; adlandırma prompts katmanında (chart_context ile aynı kural).
_ELEMENT_BY_SIGN = {
    "Ari": "fire", "Leo": "fire", "Sag": "fire",
    "Tau": "earth", "Vir": "earth", "Cap": "earth",
    "Gem": "air", "Lib": "air", "Aqu": "air",
    "Can": "water", "Sco": "water", "Pis": "water",
}
_MODALITY_BY_SIGN = {
    "Ari": "cardinal", "Can": "cardinal", "Lib": "cardinal", "Cap": "cardinal",
    "Tau": "fixed", "Leo": "fixed", "Sco": "fixed", "Aqu": "fixed",
    "Gem": "mutable", "Vir": "mutable", "Sag": "mutable", "Pis": "mutable",
}

#: Denge sayımına giren geleneksel yedili (chart_context.TRADITIONAL ile
#: aynı kanon; Yükselen ayrıca eklenir).
_BALANCE_PLANETS = ("Sun", "Moon", "Mercury", "Venus", "Mars",
                    "Jupiter", "Saturn")

#: kerykeion ev adı -> numara (chart_context._HOUSE_NUMBER'ın motor kopyası;
#: yığılma artık API'de de döndüğü için sayım burada yapılıyor).
_HOUSE_NO = {ad: i + 1 for i, ad in enumerate((
    "First_House", "Second_House", "Third_House", "Fourth_House",
    "Fifth_House", "Sixth_House", "Seventh_House", "Eighth_House",
    "Ninth_House", "Tenth_House", "Eleventh_House", "Twelfth_House"))}

#: Deklinasyon paraleli eşiği (derece) — klasik ±0.5°.
_DECLINATION_ORB = 0.5


def _declination_aspects(points: list[dict[str, Any]],
                         limit: int = 6) -> list[dict[str, Any]]:
    """Paralel / kontra-paralel çiftleri (T4).

    Aynı işaretli deklinasyonlar ±0.5° içindeyse PARALEL (kavuşum
    gücünde), zıt işaretliler mutlak değerce ±0.5° içindeyse
    KONTRA-PARALEL (karşıt gücünde) sayılır. Ay düğümleri hesaba girmez:
    ikisi tanım gereği her zaman zıt deklinasyondadır — "açı" değil
    geometri kaçınılmazlığıdır.
    """
    adaylar = [p for p in points
               if p.get("declination") is not None
               and not p["name"].endswith("Lunar_Node")]
    çiftler: list[dict[str, Any]] = []
    for i, p1 in enumerate(adaylar):
        for p2 in adaylar[i + 1:]:
            d1, d2 = p1["declination"], p2["declination"]
            fark = abs(d1 - d2)
            toplam = abs(d1 + d2)
            if fark <= _DECLINATION_ORB and (d1 >= 0) == (d2 >= 0):
                çiftler.append({"p1": p1["name"], "p2": p2["name"],
                                "type": "parallel",
                                "delta": round(fark, 2)})
            elif toplam <= _DECLINATION_ORB and (d1 >= 0) != (d2 >= 0):
                çiftler.append({"p1": p1["name"], "p2": p2["name"],
                                "type": "contraparallel",
                                "delta": round(toplam, 2)})
    çiftler.sort(key=lambda c: c["delta"])
    return çiftler[:limit]


def _build_subject(
    name: str, year: int, month: int, day: int, hour: int, minute: int,
    city: str, nation: str | None, zodiac_type: ZodiacType = "Tropical",
):
    """Özne + konum çözümü döner.

    Konum da dönüyor (T0) çünkü `loc.fallback` bayrağı BEYAN üretmek için
    gerekli: çözülemeyen şehir İstanbul'a düşüyor ve bu, Yükselen'i ve tüm
    ev sistemini değiştiriyor. BaZi bunu baştan beri beyan ediyordu
    (bazi_service tst_fallback_city); Batı tarafı sessizdi.
    """
    loc = resolve_city(city, nation)
    kwargs: dict[str, Any] = dict(
        name=name, year=year, month=month, day=day, hour=hour, minute=minute,
        city=loc.city, nation=loc.nation, lat=loc.lat, lng=loc.lng,
        tz_str=loc.tz_str, online=False, zodiac_type=zodiac_type,
        suppress_geonames_warning=True,
    )
    if zodiac_type == "Sidereal":
        kwargs["sidereal_mode"] = "LAHIRI"
    subject = _kerykeion().AstrologicalSubjectFactory.from_birth_data(**kwargs)
    return subject, loc


def _point_dict(point) -> dict[str, Any]:
    # declination ve speed kerykeion tarafından ZATEN hesaplanıyor (T0):
    # atmak, ödenmiş bedeli çöpe atmaktı. Deklinasyon paralel/kontra-paralel
    # açıların, hız da yaklaşan/ayrılan ayrımının ham maddesi.
    dec = getattr(point, "declination", None)
    speed = getattr(point, "speed", None)
    return {
        "name": point.name,
        "name_tr": PLANET_TR.get(point.name, point.name),
        "sign": point.sign,
        "sign_tr": SIGN_TR.get(point.sign, point.sign),
        "symbol": SIGN_SYMBOL.get(point.sign, ""),
        "position": round(point.position, 2),
        "abs_position": round(point.abs_pos, 2),
        "house": getattr(point, "house", None),
        "retrograde": bool(getattr(point, "retrograde", False)),
        "element": getattr(point, "element", None),
        "declination": round(dec, 2) if dec is not None else None,
        "speed": round(speed, 4) if speed is not None else None,
    }


def _subject_points(subject) -> list[dict[str, Any]]:
    points = []
    for attr in _PLANET_NAMES:
        p = getattr(subject, attr, None)
        if p is not None:
            points.append(_point_dict(p))
    return points


def _aspects_list(aspects, limit: int | None = None) -> list[dict[str, Any]]:
    result = []
    for a in aspects:
        # `movement` (T0): yaklaşan açı güçlenir, ayrılan söner — klasik
        # yorum farkı. kerykeion `aspect_movement` alanını zaten üretiyor;
        # anahtar olarak taşınır, ad prompts katmanında çözülür.
        movement = getattr(a, "aspect_movement", None)
        result.append({
            "p1": a.p1_name, "p1_tr": PLANET_TR.get(a.p1_name, a.p1_name),
            "p2": a.p2_name, "p2_tr": PLANET_TR.get(a.p2_name, a.p2_name),
            "aspect": a.aspect,
            "aspect_tr": ASPECT_TR.get(a.aspect, a.aspect),
            "orbit": round(a.orbit, 2),
            "movement": str(movement).lower() if movement else None,
        })
    if limit:
        result = result[:limit]
    return result


def get_natal_chart(
    name: str, year: int, month: int, day: int, hour: int, minute: int,
    city: str, nation: str | None = None, zodiac_type: ZodiacType = "Tropical",
) -> dict[str, Any]:
    subject, loc = _build_subject(name, year, month, day, hour, minute,
                                  city, nation, zodiac_type)
    aspects = _kerykeion().NatalAspects(subject).relevant_aspects

    # Beyanlar (T0): şehir çözülemeyip İstanbul'a düşüldüyse bu SÖYLENİR.
    # Yükselen ve tüm ev sistemi konuma bağlı — sessiz kalınamaz.
    disclosures: list[str] = []
    if loc.fallback:
        disclosures.append("geo_fallback_city")

    houses = []
    for i, house_attr in enumerate([
        "first_house", "second_house", "third_house", "fourth_house",
        "fifth_house", "sixth_house", "seventh_house", "eighth_house",
        "ninth_house", "tenth_house", "eleventh_house", "twelfth_house",
    ], start=1):
        h = getattr(subject, house_attr)
        houses.append({
            "house": i, "sign": h.sign, "sign_tr": SIGN_TR.get(h.sign, h.sign),
            "position": round(h.position, 2),
            "abs_position": round(h.abs_pos, 2),
        })

    asc = subject.first_house

    # Denge sayımı (T4): geleneksel yedili + Yükselen — chart_context'in
    # sohbet fısıltısındaki kanonla aynı; artık API/rapor da görüyor.
    puanlar = _subject_points(subject)
    sayilacak = [p["sign"] for p in puanlar
                 if p["name"] in _BALANCE_PLANETS] + [asc.sign]
    elementler = {"fire": 0, "earth": 0, "air": 0, "water": 0}
    nitelikler = {"cardinal": 0, "fixed": 0, "mutable": 0}
    for kod in sayilacak:
        elementler[_ELEMENT_BY_SIGN[kod]] += 1
        nitelikler[_MODALITY_BY_SIGN[kod]] += 1

    ev_sayimi: dict[int, int] = {}
    for p in puanlar:
        if p["name"] not in _BALANCE_PLANETS:
            continue
        ev = _HOUSE_NO.get(p.get("house"))
        if ev:
            ev_sayimi[ev] = ev_sayimi.get(ev, 0) + 1
    yigilmalar = sorted(
        ({"house": ev, "count": adet} for ev, adet in ev_sayimi.items()
         if adet >= 3),
        key=lambda y: (-y["count"], y["house"]))

    return {
        "zodiac_type": zodiac_type,
        # Eski istemci uyumluluğu icin duz alanlar:
        "sun_sign": f"{SIGN_TR.get(subject.sun.sign)} {SIGN_SYMBOL.get(subject.sun.sign, '')}".strip(),
        "moon_sign": f"{SIGN_TR.get(subject.moon.sign)} {SIGN_SYMBOL.get(subject.moon.sign, '')}".strip(),
        "ascendant": f"{SIGN_TR.get(asc.sign)} {SIGN_SYMBOL.get(asc.sign, '')}".strip(),
        "sun": _point_dict(subject.sun),
        "moon": _point_dict(subject.moon),
        "asc": {"sign": asc.sign, "sign_tr": SIGN_TR.get(asc.sign), "position": round(asc.position, 2)},
        "points": puanlar,
        "houses": houses,
        "aspects": _aspects_list(aspects),
        "element_distribution": elementler,
        "modality_distribution": nitelikler,
        "stelliums": yigilmalar,
        "declination_aspects": _declination_aspects(puanlar),
        "disclosures": disclosures,
        "lunar_phase": {
            "emoji": getattr(subject.lunar_phase, "moon_emoji", None),
            "name": getattr(subject.lunar_phase, "moon_phase_name", None),
        } if getattr(subject, "lunar_phase", None) else None,
        "location": {"city": city, "lat": subject.lat, "lng": subject.lng, "tz": subject.tz_str},
    }


def get_natal_chart_svg(
    name: str, year: int, month: int, day: int, hour: int, minute: int,
    city: str, nation: str | None = None, zodiac_type: ZodiacType = "Tropical",
    theme: str = "dark",
) -> str:
    subject, _ = _build_subject(name, year, month, day, hour, minute,
                                city, nation, zodiac_type)
    chart = _kerykeion().KerykeionChartSVG(subject, chart_type="Natal", theme=theme)
    return chart.makeTemplate()


def get_transits(
    name: str, year: int, month: int, day: int, hour: int, minute: int,
    city: str, nation: str | None = None,
) -> dict[str, Any]:
    """Şu anki gökyüzünün natal haritaya açıları (transit)."""
    natal, _ = _build_subject(name, year, month, day, hour, minute, city, nation)
    now = dt.datetime.now(dt.timezone.utc)
    transit_subject = _kerykeion().AstrologicalSubjectFactory.from_iso_utc_time(
        name="Transit", iso_utc_time=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        city="Greenwich", nation="GB", lng=0.0, lat=51.48, online=False,
    )
    cross = _kerykeion().SynastryAspects(transit_subject, natal)
    return {
        "timestamp_utc": now.isoformat(),
        "transiting_points": _subject_points(transit_subject),
        "aspects_to_natal": _aspects_list(cross.relevant_aspects, limit=25),
    }


def get_synastry(person1: dict[str, Any], person2: dict[str, Any]) -> dict[str, Any]:
    """İki kişi arasındaki sinastri (kozmik uyum) analizi."""
    s1, _ = _build_subject(**person1)
    s2, _ = _build_subject(**person2)
    aspects = _kerykeion().SynastryAspects(s1, s2).relevant_aspects

    score_data: dict[str, Any] = {}
    try:
        score = _kerykeion().RelationshipScoreFactory(s1, s2).get_relationship_score()
        score_data = {
            "score": score.score_value,
            "description": score.score_description,
            "is_destiny_sign": bool(getattr(score, "is_destiny_sign", False)),
        }
    except Exception:
        score_data = {"score": None, "description": None}

    return {
        "person1": {"name": s1.name, "sun": _point_dict(s1.sun), "moon": _point_dict(s1.moon)},
        "person2": {"name": s2.name, "sun": _point_dict(s2.sun), "moon": _point_dict(s2.moon)},
        "relationship_score": score_data,
        "aspects": _aspects_list(aspects, limit=30),
    }


def get_synastry_svg(person1: dict[str, Any], person2: dict[str, Any], theme: str = "dark") -> str:
    s1, _ = _build_subject(**person1)
    s2, _ = _build_subject(**person2)
    chart = _kerykeion().KerykeionChartSVG(s1, chart_type="Synastry", second_obj=s2, theme=theme)
    return chart.makeTemplate()
