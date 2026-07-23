"""Şehir → koordinat + saat dilimi çözümlemesi.

Astronomik hassasiyetin en kritik hata noktası konum/saat dilimidir.
Önce dahili gazetteer'e bakılır (ağ bağımsız, deterministik);
bulunamazsa GeoNames REST API denenir (GEONAMES_USERNAME gerekli).
"""
from __future__ import annotations

import logging
import unicodedata
from dataclasses import dataclass

import httpx

from core import config

logger = logging.getLogger(__name__)


@dataclass
class GeoLocation:
    city: str
    nation: str
    lat: float
    lng: float
    tz_str: str


def _normalize(s: str) -> str:
    s = s.strip().lower().replace("ı", "i")
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c))


# Türkiye'nin tüm büyükşehirleri + sık kullanılan dünya şehirleri
_GAZETTEER: dict[str, tuple[str, float, float, str]] = {
    # sehir: (ulke, lat, lng, tz)
    "istanbul": ("TR", 41.0082, 28.9784, "Europe/Istanbul"),
    "ankara": ("TR", 39.9334, 32.8597, "Europe/Istanbul"),
    "izmir": ("TR", 38.4237, 27.1428, "Europe/Istanbul"),
    "bursa": ("TR", 40.1885, 29.0610, "Europe/Istanbul"),
    "antalya": ("TR", 36.8969, 30.7133, "Europe/Istanbul"),
    "adana": ("TR", 37.0000, 35.3213, "Europe/Istanbul"),
    "konya": ("TR", 37.8746, 32.4932, "Europe/Istanbul"),
    "gaziantep": ("TR", 37.0662, 37.3833, "Europe/Istanbul"),
    "sanliurfa": ("TR", 37.1674, 38.7955, "Europe/Istanbul"),
    "mersin": ("TR", 36.8121, 34.6415, "Europe/Istanbul"),
    "diyarbakir": ("TR", 37.9144, 40.2306, "Europe/Istanbul"),
    "kayseri": ("TR", 38.7205, 35.4826, "Europe/Istanbul"),
    "eskisehir": ("TR", 39.7767, 30.5206, "Europe/Istanbul"),
    "samsun": ("TR", 41.2867, 36.3300, "Europe/Istanbul"),
    "denizli": ("TR", 37.7765, 29.0864, "Europe/Istanbul"),
    "malatya": ("TR", 38.3552, 38.3095, "Europe/Istanbul"),
    "trabzon": ("TR", 41.0027, 39.7168, "Europe/Istanbul"),
    "erzurum": ("TR", 39.9043, 41.2679, "Europe/Istanbul"),
    "van": ("TR", 38.4891, 43.4089, "Europe/Istanbul"),
    "batman": ("TR", 37.8812, 41.1351, "Europe/Istanbul"),
    "elazig": ("TR", 38.6810, 39.2264, "Europe/Istanbul"),
    "kahramanmaras": ("TR", 37.5858, 36.9371, "Europe/Istanbul"),
    "manisa": ("TR", 38.6191, 27.4289, "Europe/Istanbul"),
    "sivas": ("TR", 39.7477, 37.0179, "Europe/Istanbul"),
    "balikesir": ("TR", 39.6484, 27.8826, "Europe/Istanbul"),
    "aydin": ("TR", 37.8560, 27.8416, "Europe/Istanbul"),
    "tekirdag": ("TR", 40.9781, 27.5117, "Europe/Istanbul"),
    "sakarya": ("TR", 40.7889, 30.4060, "Europe/Istanbul"),
    "mugla": ("TR", 37.2153, 28.3636, "Europe/Istanbul"),
    "mardin": ("TR", 37.3212, 40.7245, "Europe/Istanbul"),
    "hatay": ("TR", 36.2023, 36.1613, "Europe/Istanbul"),
    "ordu": ("TR", 40.9839, 37.8764, "Europe/Istanbul"),
    "kocaeli": ("TR", 40.8533, 29.8815, "Europe/Istanbul"),
    "izmit": ("TR", 40.7654, 29.9408, "Europe/Istanbul"),
    # Dünya
    "london": ("GB", 51.5074, -0.1278, "Europe/London"),
    "londra": ("GB", 51.5074, -0.1278, "Europe/London"),
    "new york": ("US", 40.7128, -74.0060, "America/New_York"),
    "los angeles": ("US", 34.0522, -118.2437, "America/Los_Angeles"),
    "paris": ("FR", 48.8566, 2.3522, "Europe/Paris"),
    "berlin": ("DE", 52.5200, 13.4050, "Europe/Berlin"),
    "amsterdam": ("NL", 52.3676, 4.9041, "Europe/Amsterdam"),
    "moscow": ("RU", 55.7558, 37.6173, "Europe/Moscow"),
    "moskova": ("RU", 55.7558, 37.6173, "Europe/Moscow"),
    "dubai": ("AE", 25.2048, 55.2708, "Asia/Dubai"),
    "tokyo": ("JP", 35.6762, 139.6503, "Asia/Tokyo"),
    "beijing": ("CN", 39.9042, 116.4074, "Asia/Shanghai"),
    "pekin": ("CN", 39.9042, 116.4074, "Asia/Shanghai"),
    "delhi": ("IN", 28.7041, 77.1025, "Asia/Kolkata"),
    "mumbai": ("IN", 19.0760, 72.8777, "Asia/Kolkata"),
    "cairo": ("EG", 30.0444, 31.2357, "Africa/Cairo"),
    "kahire": ("EG", 30.0444, 31.2357, "Africa/Cairo"),
    "baku": ("AZ", 40.4093, 49.8671, "Asia/Baku"),
    "bakü": ("AZ", 40.4093, 49.8671, "Asia/Baku"),
    "tashkent": ("UZ", 41.2995, 69.2401, "Asia/Tashkent"),
    "sydney": ("AU", -33.8688, 151.2093, "Australia/Sydney"),
    "sao paulo": ("BR", -23.5505, -46.6333, "America/Sao_Paulo"),
    "mexico city": ("MX", 19.4326, -99.1332, "America/Mexico_City"),
    "toronto": ("CA", 43.6532, -79.3832, "America/Toronto"),
    "chicago": ("US", 41.8781, -87.6298, "America/Chicago"),
    "athens": ("GR", 37.9838, 23.7275, "Europe/Athens"),
    "atina": ("GR", 37.9838, 23.7275, "Europe/Athens"),
    "sofia": ("BG", 42.6977, 23.3219, "Europe/Sofia"),
    "tahran": ("IR", 35.6892, 51.3890, "Asia/Tehran"),
    "tehran": ("IR", 35.6892, 51.3890, "Asia/Tehran"),
    "riyadh": ("SA", 24.7136, 46.6753, "Asia/Riyadh"),
    "riyad": ("SA", 24.7136, 46.6753, "Asia/Riyadh"),
    "mecca": ("SA", 21.3891, 39.8579, "Asia/Riyadh"),
    "mekke": ("SA", 21.3891, 39.8579, "Asia/Riyadh"),
    "frankfurt": ("DE", 50.1109, 8.6821, "Europe/Berlin"),
    "munich": ("DE", 48.1351, 11.5820, "Europe/Berlin"),
    "münih": ("DE", 48.1351, 11.5820, "Europe/Berlin"),
    "vienna": ("AT", 48.2082, 16.3738, "Europe/Vienna"),
    "viyana": ("AT", 48.2082, 16.3738, "Europe/Vienna"),
    "brussels": ("BE", 50.8503, 4.3517, "Europe/Brussels"),
    "brüksel": ("BE", 50.8503, 4.3517, "Europe/Brussels"),
    "stockholm": ("SE", 59.3293, 18.0686, "Europe/Stockholm"),
    "zurich": ("CH", 47.3769, 8.5417, "Europe/Zurich"),
    "zürih": ("CH", 47.3769, 8.5417, "Europe/Zurich"),
    "lefkosa": ("CY", 35.1856, 33.3823, "Asia/Nicosia"),
    "nicosia": ("CY", 35.1856, 33.3823, "Asia/Nicosia"),
}


def resolve_city(city: str, nation: str | None = None) -> GeoLocation:
    """Şehir adını koordinata çevirir. Bulunamazsa GeoNames'e sorar,
    o da başarısız olursa İstanbul varsayılanına döner (uyarı loglanır)."""
    key = _normalize(city)
    if key in _GAZETTEER:
        nat, lat, lng, tz = _GAZETTEER[key]
        return GeoLocation(city=city, nation=nation or nat, lat=lat, lng=lng, tz_str=tz)

    if config.GEONAMES_USERNAME:
        try:
            resp = httpx.get(
                "http://api.geonames.org/searchJSON",
                params={
                    "q": city,
                    "maxRows": 1,
                    "username": config.GEONAMES_USERNAME,
                    **({"country": nation} if nation else {}),
                },
                timeout=8,
            )
            geo = resp.json()["geonames"][0]
            lat, lng = float(geo["lat"]), float(geo["lng"])
            tz_resp = httpx.get(
                "http://api.geonames.org/timezoneJSON",
                params={"lat": lat, "lng": lng, "username": config.GEONAMES_USERNAME},
                timeout=8,
            )
            tz = tz_resp.json().get("timezoneId", "UTC")
            return GeoLocation(
                city=city, nation=geo.get("countryCode", nation or ""),
                lat=lat, lng=lng, tz_str=tz,
            )
        except Exception as exc:
            logger.warning("GeoNames sorgusu başarısız (%s): %s", city, exc)

    logger.warning("Şehir çözümlenemedi, İstanbul varsayılanı kullanılıyor: %s", city)
    return GeoLocation(city=city, nation=nation or "TR",
                       lat=41.0082, lng=28.9784, tz_str="Europe/Istanbul")
