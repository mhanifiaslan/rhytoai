"""Astroloji hesaplama motoru — Kerykeion 5.x / Swiss Ephemeris.

Natal, transit ve sinastri hesaplamaları; Tropikal + Sidereal (Lahiri) destek;
SVG harita üretimi. Tüm konum çözümlemesi offline gazetteer/GeoNames ile yapılır
(kerykeion'un online modu kullanılmaz — deterministik ve ağ bağımsız).
"""
from __future__ import annotations

import datetime as dt
from typing import Any, Literal

from kerykeion import (
    AstrologicalSubjectFactory,
    KerykeionChartSVG,
    NatalAspects,
    RelationshipScoreFactory,
    SynastryAspects,
)

from services.geo_service import resolve_city

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


def _build_subject(
    name: str, year: int, month: int, day: int, hour: int, minute: int,
    city: str, nation: str | None, zodiac_type: ZodiacType = "Tropical",
):
    loc = resolve_city(city, nation)
    kwargs: dict[str, Any] = dict(
        name=name, year=year, month=month, day=day, hour=hour, minute=minute,
        city=loc.city, nation=loc.nation, lat=loc.lat, lng=loc.lng,
        tz_str=loc.tz_str, online=False, zodiac_type=zodiac_type,
        suppress_geonames_warning=True,
    )
    if zodiac_type == "Sidereal":
        kwargs["sidereal_mode"] = "LAHIRI"
    return AstrologicalSubjectFactory.from_birth_data(**kwargs)


def _point_dict(point) -> dict[str, Any]:
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
        result.append({
            "p1": a.p1_name, "p1_tr": PLANET_TR.get(a.p1_name, a.p1_name),
            "p2": a.p2_name, "p2_tr": PLANET_TR.get(a.p2_name, a.p2_name),
            "aspect": a.aspect,
            "aspect_tr": ASPECT_TR.get(a.aspect, a.aspect),
            "orbit": round(a.orbit, 2),
        })
    if limit:
        result = result[:limit]
    return result


def get_natal_chart(
    name: str, year: int, month: int, day: int, hour: int, minute: int,
    city: str, nation: str | None = None, zodiac_type: ZodiacType = "Tropical",
) -> dict[str, Any]:
    subject = _build_subject(name, year, month, day, hour, minute, city, nation, zodiac_type)
    aspects = NatalAspects(subject).relevant_aspects

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
    return {
        "zodiac_type": zodiac_type,
        # Eski istemci uyumluluğu icin duz alanlar:
        "sun_sign": f"{SIGN_TR.get(subject.sun.sign)} {SIGN_SYMBOL.get(subject.sun.sign, '')}".strip(),
        "moon_sign": f"{SIGN_TR.get(subject.moon.sign)} {SIGN_SYMBOL.get(subject.moon.sign, '')}".strip(),
        "ascendant": f"{SIGN_TR.get(asc.sign)} {SIGN_SYMBOL.get(asc.sign, '')}".strip(),
        "sun": _point_dict(subject.sun),
        "moon": _point_dict(subject.moon),
        "asc": {"sign": asc.sign, "sign_tr": SIGN_TR.get(asc.sign), "position": round(asc.position, 2)},
        "points": _subject_points(subject),
        "houses": houses,
        "aspects": _aspects_list(aspects),
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
    subject = _build_subject(name, year, month, day, hour, minute, city, nation, zodiac_type)
    chart = KerykeionChartSVG(subject, chart_type="Natal", theme=theme)
    return chart.makeTemplate()


def get_transits(
    name: str, year: int, month: int, day: int, hour: int, minute: int,
    city: str, nation: str | None = None,
) -> dict[str, Any]:
    """Şu anki gökyüzünün natal haritaya açıları (transit)."""
    natal = _build_subject(name, year, month, day, hour, minute, city, nation)
    now = dt.datetime.now(dt.timezone.utc)
    transit_subject = AstrologicalSubjectFactory.from_iso_utc_time(
        name="Transit", iso_utc_time=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        city="Greenwich", nation="GB", lng=0.0, lat=51.48, online=False,
    )
    cross = SynastryAspects(transit_subject, natal)
    return {
        "timestamp_utc": now.isoformat(),
        "transiting_points": _subject_points(transit_subject),
        "aspects_to_natal": _aspects_list(cross.relevant_aspects, limit=25),
    }


def get_synastry(person1: dict[str, Any], person2: dict[str, Any]) -> dict[str, Any]:
    """İki kişi arasındaki sinastri (kozmik uyum) analizi."""
    s1 = _build_subject(**person1)
    s2 = _build_subject(**person2)
    aspects = SynastryAspects(s1, s2).relevant_aspects

    score_data: dict[str, Any] = {}
    try:
        score = RelationshipScoreFactory(s1, s2).get_relationship_score()
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
    s1 = _build_subject(**person1)
    s2 = _build_subject(**person2)
    chart = KerykeionChartSVG(s1, chart_type="Synastry", second_obj=s2, theme=theme)
    return chart.makeTemplate()
