"""Günlük gökyüzü durumu servisi.

İki veri kaynağı birleştirilir:
1. Swiss Ephemeris (lokal, milisaniyelik): gezegen konumları, retro durumları,
   Ay evresi, günün önemli açıları.
2. NASA JPL Horizons REST API (ağ, günlük önbellekli): gezegenlerin Dünya'ya
   anlık uzaklıkları (AU) — "canlı NASA verisi" zenginleştirmesi.

Sonuç 1 saat önbelleklenir; Horizons erişilemezse yalnız swisseph verisi döner.
"""
from __future__ import annotations

import datetime as dt
import logging
from typing import Any

import httpx
import swisseph as swe

from core import cache

logger = logging.getLogger(__name__)

_PLANETS = [
    ("Sun", "Güneş", swe.SUN, "10"),
    ("Moon", "Ay", swe.MOON, "301"),
    ("Mercury", "Merkür", swe.MERCURY, "199"),
    ("Venus", "Venüs", swe.VENUS, "299"),
    ("Mars", "Mars", swe.MARS, "499"),
    ("Jupiter", "Jüpiter", swe.JUPITER, "599"),
    ("Saturn", "Satürn", swe.SATURN, "699"),
    ("Uranus", "Uranüs", swe.URANUS, "799"),
    ("Neptune", "Neptün", swe.NEPTUNE, "899"),
    ("Pluto", "Plüton", swe.PLUTO, "999"),
]

_SIGNS = [
    ("Koç", "♈"), ("Boğa", "♉"), ("İkizler", "♊"), ("Yengeç", "♋"),
    ("Aslan", "♌"), ("Başak", "♍"), ("Terazi", "♎"), ("Akrep", "♏"),
    ("Yay", "♐"), ("Oğlak", "♑"), ("Kova", "♒"), ("Balık", "♓"),
]

_MAJOR_ASPECTS = [
    (0, "Kavuşum", 6), (60, "Altmışlık", 4), (90, "Kare", 6),
    (120, "Üçgen", 6), (180, "Karşıt", 8),
]


def _julday_now() -> float:
    now = dt.datetime.now(dt.timezone.utc)
    return swe.julday(now.year, now.month, now.day,
                      now.hour + now.minute / 60 + now.second / 3600)


def _moon_phase(jd: float) -> dict[str, Any]:
    sun_lon = swe.calc_ut(jd, swe.SUN)[0][0]
    moon_lon = swe.calc_ut(jd, swe.MOON)[0][0]
    angle = (moon_lon - sun_lon) % 360
    phases = [
        (22.5, "Yeni Ay", "🌑"), (67.5, "Hilal (Büyüyen)", "🌒"),
        (112.5, "İlk Dördün", "🌓"), (157.5, "Şişkin Ay (Büyüyen)", "🌔"),
        (202.5, "Dolunay", "🌕"), (247.5, "Şişkin Ay (Küçülen)", "🌖"),
        (292.5, "Son Dördün", "🌗"), (337.5, "Hilal (Küçülen)", "🌘"),
        (360.1, "Yeni Ay", "🌑"),
    ]
    for limit, name, emoji in phases:
        if angle < limit:
            return {"angle": round(angle, 1), "name": name, "emoji": emoji,
                    "illumination": round((1 - abs(angle - 180) / 180) * 100)}
    return {"angle": round(angle, 1), "name": "Yeni Ay", "emoji": "🌑", "illumination": 0}


def _horizons_distances() -> dict[str, float]:
    """NASA JPL Horizons'tan gezegenlerin Dünya'ya uzaklığı (AU). Günlük önbellek."""
    cache_key = f"horizons-distances-{dt.date.today().isoformat()}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    distances: dict[str, float] = {}
    now = dt.datetime.now(dt.timezone.utc)
    start = now.strftime("%Y-%m-%d %H:%M")
    stop = (now + dt.timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M")
    try:
        with httpx.Client(timeout=15) as client:
            for name, _, _, horizons_id in _PLANETS:
                if name == "Moon":
                    continue
                resp = client.get(
                    "https://ssd.jpl.nasa.gov/api/horizons.api",
                    params={
                        "format": "text", "COMMAND": f"'{horizons_id}'",
                        "OBJ_DATA": "'NO'", "MAKE_EPHEM": "'YES'",
                        "EPHEM_TYPE": "'OBSERVER'", "CENTER": "'500@399'",
                        "START_TIME": f"'{start}'", "STOP_TIME": f"'{stop}'",
                        "STEP_SIZE": "'1m'", "QUANTITIES": "'20'",
                    },
                )
                text = resp.text
                if "$$SOE" in text:
                    line = text.split("$$SOE")[1].split("$$EOE")[0].strip().splitlines()[0]
                    parts = line.split()
                    # delta (AU) sondan ikinci kolon (delta, deldot)
                    distances[name] = float(parts[-2])
        if distances:
            cache.set(cache_key, distances, ttl_seconds=24 * 3600)
    except Exception as exc:
        logger.warning("Horizons API erişilemedi: %s", exc)
    return distances


def get_sky_now(include_nasa: bool = True) -> dict[str, Any]:
    cached = cache.get("sky-now")
    if cached is not None:
        return cached

    jd = _julday_now()
    nasa_distances = _horizons_distances() if include_nasa else {}

    planets = []
    positions: dict[str, float] = {}
    retrogrades = []
    for name, name_tr, planet_id, _ in _PLANETS:
        pos, _flags = swe.calc_ut(jd, planet_id, swe.FLG_SPEED)
        lon, speed = pos[0] % 360, pos[3]
        sign_idx = int(lon // 30)
        sign_name, sign_symbol = _SIGNS[sign_idx]
        retro = speed < 0
        if retro:
            retrogrades.append(name_tr)
        positions[name] = lon
        planets.append({
            "name": name, "name_tr": name_tr,
            "longitude": round(lon, 2),
            "sign": sign_name, "symbol": sign_symbol,
            "degree_in_sign": round(lon % 30, 1),
            "retrograde": retro,
            "speed": round(speed, 4),
            "distance_au": nasa_distances.get(name),
        })

    # Günün önemli açıları (Ay hariç dış gezegenler arası)
    aspects = []
    names = [p for p in _PLANETS if p[0] != "Moon"]
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            n1, n2 = names[i], names[j]
            diff = abs(positions[n1[0]] - positions[n2[0]])
            diff = min(diff, 360 - diff)
            for angle, aspect_tr, orb in _MAJOR_ASPECTS:
                if abs(diff - angle) <= orb:
                    aspects.append({
                        "p1": n1[1], "p2": n2[1], "aspect": aspect_tr,
                        "orb": round(abs(diff - angle), 1),
                    })
                    break

    result = {
        "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "julian_day": round(jd, 5),
        "planets": planets,
        "retrogrades": retrogrades,
        "moon_phase": _moon_phase(jd),
        "aspects": sorted(aspects, key=lambda a: a["orb"])[:12],
        "nasa_data_available": bool(nasa_distances),
    }
    cache.set("sky-now", result, ttl_seconds=3600)
    return result
