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

#: (açı, dilden bağımsız anahtar, orb). Ad değil ANAHTAR tutulur — gökyüzü
#: paylaşımlı önbellekten servis ediliyor ve tüm diller aynı hesabı kullanıyor.
_MAJOR_ASPECTS = [
    (0, "conjunction", 6), (60, "sextile", 4), (90, "square", 6),
    (120, "trine", 6), (180, "opposition", 8),
]


def _julday_now() -> float:
    now = dt.datetime.now(dt.timezone.utc)
    return swe.julday(now.year, now.month, now.day,
                      now.hour + now.minute / 60 + now.second / 3600)


#: Ay evresi sınırları: (üst açı, dilden bağımsız anahtar, emoji).
#:
#: Evre adı burada METİN olarak tutulmaz. Gökyüzü paylaşımlı önbellekten
#: servis ediliyor ve tüm diller aynı hesabı kullanıyor; ada dil karıştırmak
#: İngilizce kullanıcıya "Dolunay" göstermek demekti. Ad, isteğin diline göre
#: services/prompts altındaki MOON_PHASES tablosundan çözülür.
_MOON_PHASES = [
    (22.5, "new_moon", "🌑"), (67.5, "waxing_crescent", "🌒"),
    (112.5, "first_quarter", "🌓"), (157.5, "waxing_gibbous", "🌔"),
    (202.5, "full_moon", "🌕"), (247.5, "waning_gibbous", "🌖"),
    (292.5, "last_quarter", "🌗"), (337.5, "waning_crescent", "🌘"),
    (360.1, "new_moon", "🌑"),
]


def _moon_phase(jd: float) -> dict[str, Any]:
    sun_lon = swe.calc_ut(jd, swe.SUN)[0][0]
    moon_lon = swe.calc_ut(jd, swe.MOON)[0][0]
    angle = (moon_lon - sun_lon) % 360
    for limit, key, emoji in _MOON_PHASES:
        if angle < limit:
            return {"angle": round(angle, 1), "key": key, "emoji": emoji,
                    "illumination": round((1 - abs(angle - 180) / 180) * 100)}
    return {"angle": round(angle, 1), "key": "new_moon", "emoji": "🌑",
            "illumination": 0}


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


#: Önbellek anahtarı sürümlü: yükün biçimi değiştiğinde (Türkçe adlar ->
#: dilden bağımsız anahtarlar) eski kayıtlar okunmaya devam ederse İngilizce
#: kullanıcı bir saat boyunca Türkçe gökyüzü görürdü.
_SKY_CACHE_KEY = "sky-now-v2"


def get_sky_now(include_nasa: bool = True) -> dict[str, Any]:
    cached = cache.get(_SKY_CACHE_KEY)
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
            # Gezegen ADI değil anahtarı; ada çeviri isteğin dilinde yapılır.
            retrogrades.append(name)
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
            for angle, aspect_key, orb in _MAJOR_ASPECTS:
                if abs(diff - angle) <= orb:
                    aspects.append({
                        "p1": n1[0], "p2": n2[0], "aspect": aspect_key,
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
    cache.set(_SKY_CACHE_KEY, result, ttl_seconds=3600)
    return result
