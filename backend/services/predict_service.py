"""Tahmin katmanı (T1+): solar return, progresyon, transit takvimi.

Motorun geri kalanı "an"ı hesaplar; bu modül ZAMANI hesaplar — Güneş'in
natal boylamına dönüş anı, progres Ay'ın burç değişim tarihi, transitlerin
kesinleşme günleri. Hepsi kerykeion/Swiss Ephemeris zincirinin üstünde.

Dürüstlük kuralları:
- Doğum saati bilinmiyorsa natal Güneş ±0.5° belirsizdir → solar return
  ANI ±12 saat oynar ve SR Yükseleni/evleri anlamsızlaşır. Bu durumda an
  "yaklaşık" beyanıyla verilir, ASC/evler HİÇ üretilmez.
- Konum = natal şehir. Relocation (dönüş anında başka şehirde olmak)
  bilinçli kapsam dışı; v1 bunu İDDİA ETMEZ.
- Tropikal zodyak, precession düzeltmesi YOK: natal boylam neyse dönüş o
  boylamadır — tropikal çerçevenin iç tutarlılığı bu.
"""
from __future__ import annotations

import datetime as dt
from typing import Any

from services import astro_service
from services.geo_service import resolve_city

#: Tahmin hesabı sürümü — davranış değişince artar, önbellekler tazelenir
#: (BaZi calc_version disiplini).
PREDICT_CALC_VERSION = "1"


def _model_points(model) -> list[dict[str, Any]]:
    """PlanetReturnModel noktalarını natal şemasıyla aynı biçime döker."""
    noktalar = []
    for attr in astro_service._PLANET_NAMES:
        p = getattr(model, attr, None)
        if p is not None:
            noktalar.append(astro_service._point_dict(p))
    return noktalar


def solar_return(
    name: str, year: int, month: int, day: int, hour: int, minute: int,
    city: str, nation: str | None = None, hour_known: bool = True,
    target_year: int | None = None,
) -> dict[str, Any]:
    """Aktif solar return haritası + bir sonraki dönüş anı.

    ``target_year`` verilmezse İÇİNDE BULUNULAN SR yılı seçilir: son dönüş
    (doğum günü geçmediyse geçen yılınki) aktif haritadır; bir sonraki
    dönüşün tarihi de ayrıca döner ("yeni yılın şu gün başlıyor").
    """
    natal, loc = astro_service._build_subject(
        name, year, month, day, hour, minute, city, nation)

    ker = astro_service._kerykeion()
    factory = ker.PlanetaryReturnFactory(
        natal, city=loc.city, nation=loc.nation,
        lng=loc.lng, lat=loc.lat, tz_str=loc.tz_str, online=False)

    now = dt.datetime.now(dt.timezone.utc)
    if target_year is not None:
        aktif = factory.next_return_from_year(target_year, "Solar")
        sonraki = factory.next_return_from_year(target_year + 1, "Solar")
    else:
        aday = factory.next_return_from_year(now.year, "Solar")
        aday_utc = dt.datetime.fromisoformat(
            aday.iso_formatted_utc_datetime)
        if aday_utc > now:
            # Bu yılın dönüşü henüz gelmedi → aktif harita geçen yılınki.
            aktif = factory.next_return_from_year(now.year - 1, "Solar")
            sonraki = aday
        else:
            aktif = aday
            sonraki = factory.next_return_from_year(now.year + 1, "Solar")

    disclosures: list[str] = []
    if loc.fallback:
        disclosures.append("geo_fallback_city")
    if not hour_known:
        # Natal Güneş ±0.5° → dönüş anı ±12 saat; ASC/evler anlamsız.
        disclosures.append("sr_hour_unknown")

    aspects = ker.NatalAspects(aktif).relevant_aspects

    sonuc: dict[str, Any] = {
        "calc_version": PREDICT_CALC_VERSION,
        "return_at_utc": aktif.iso_formatted_utc_datetime,
        "return_at_local": aktif.iso_formatted_local_datetime,
        "next_return_at_local": sonraki.iso_formatted_local_datetime,
        "points": _model_points(aktif),
        "aspects": astro_service._aspects_list(aspects, limit=12),
        "sr_moon_sign": aktif.moon.sign,
        "disclosures": disclosures,
        "location": {"city": loc.city, "tz": loc.tz_str},
    }

    if hour_known:
        sr_asc = aktif.first_house
        sonuc["sr_ascendant"] = {
            "sign": sr_asc.sign,
            "position": round(sr_asc.position, 2),
        }
        sonuc["sr_sun_house"] = getattr(aktif.sun, "house", None)
    # Saat bilinmiyorsa ASC/ev alanları HİÇ yok — "üretmediysen söyleme".
    return sonuc
