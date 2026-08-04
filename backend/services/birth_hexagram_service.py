"""Doğum Heksagramı — Güneş boylamından 64 kapı çarkı (Revize İ5).

Doğum anında Güneş'in ekliptik boylamı, zodyak çemberine dizilmiş 64
heksagram "kapısından" birine düşer. Çarkın DİZİLİMİ Human Design
çevrelerinde kullanılan yerleşimdir — dizilim olgu/veridir ve telif
taşımaz; YORUM METİNLERİ ise Rytho'nun kendi aktarımıdır (Gene Keys /
HD literatüründen cümle YOKTUR — knowledge/SOURCES.md).

## Çarkın matematiği

* Başlangıç: Kapı 41 = 302°00′ mutlak boylam (02°00′ Kova).
* Her kapı 360/64 = 5.625° (5°37′30″); kapı içinde 6 çizgi × 0.9375°.
* Sıra listesi zodyak yönünde dondurulmuştur; üç bağımsız çapa testte
  kilitlidir (Kapı 41 → 302°, Kapı 1 → 223.25° Akrep, Kapı 2 → 43.25°
  Boğa) — listedeki tek bir kayma üçünü birden kırar.

## Dürüstlük

Saatsiz doğumda Güneş'in konumu gün içinde ~1° oynar. Boylam bir kapı
SINIRINA yarım dereceden yakınsa kapı kesin bildirilemez: sonuç iki
adaylı "sınır beyanı" taşır — ölçemediğimizi ölçmüş gibi göstermeyiz.
"""
from __future__ import annotations

import datetime as dt
from typing import Any
from zoneinfo import ZoneInfo

from services.bazi_service import _sun_longitude
from services.geo_service import resolve_city
from services.iching_service import get_hexagram

#: Çark sürümü — dizilim/başlangıç değişirse artar, önbellek anahtarına girer.
WHEEL_VERSION = "1"

#: Kapı 41'in başlangıcı: 302°00′ (02°00′ Kova).
START_DEGREE = 302.0

GATE_SPAN = 360.0 / 64          # 5.625°
LINE_SPAN = GATE_SPAN / 6       # 0.9375°

#: Zodyak yönünde kapı sırası (başlangıç: Kapı 41). Dondurulmuş veri;
#: üç çapa + 64 benzersizlik testle kilitli.
GATE_ORDER = [
    41, 19, 13, 49, 30, 55, 37, 63, 22, 36, 25, 17, 21, 51, 42, 3,
    27, 24, 2, 23, 8, 20, 16, 35, 45, 12, 15, 52, 39, 53, 62, 56,
    31, 33, 7, 4, 29, 59, 40, 64, 47, 6, 46, 18, 48, 57, 32, 50,
    28, 44, 1, 43, 14, 34, 9, 5, 26, 11, 10, 58, 38, 54, 61, 60,
]


def gate_for_longitude(lon: float) -> dict[str, Any]:
    """Mutlak ekliptik boylamı kapı + çizgiye çevirir."""
    ofset = (lon - START_DEGREE) % 360
    kapi_indeksi = int(ofset // GATE_SPAN)
    kapi_ici = ofset % GATE_SPAN
    return {
        "gate": GATE_ORDER[kapi_indeksi],
        "line": int(kapi_ici // LINE_SPAN) + 1,
        # Sınıra uzaklık (derece): saatsiz doğumun belirsizlik kararı için.
        "boundary_distance": round(min(kapi_ici, GATE_SPAN - kapi_ici), 3),
    }


def birth_hexagram(
    year: int, month: int, day: int, hour: int | None, minute: int,
    city: str = "Istanbul", nation: str | None = None,
) -> dict[str, Any]:
    """Doğum anının kapısını hesaplar; saatsizde sınır beyanı üretir."""
    hour_known = hour is not None
    loc = resolve_city(city, nation)

    def _lon(h: int, m: int) -> float:
        local = dt.datetime(year, month, day, h, m,
                            tzinfo=ZoneInfo(loc.tz_str))
        return _sun_longitude(local.astimezone(dt.timezone.utc))

    lon = _lon(hour if hour_known else 12, minute if hour_known else 0)
    sonuc = gate_for_longitude(lon)

    # Saatsiz doğumda gün içi tarama: gün başı ve sonundaki kapı farklıysa
    # (Güneş ~1°/gün ilerler, sınırın üstünden geçmiş olabilir) iki aday
    # da bildirilir. Kesin kapı iddiası ancak ikisi aynıysa yapılır.
    alternate = None
    if not hour_known:
        bas = gate_for_longitude(_lon(0, 0))
        son = gate_for_longitude(_lon(23, 59))
        if bas["gate"] != son["gate"]:
            alternate = son["gate"] if sonuc["gate"] == bas["gate"] \
                else bas["gate"]

    hexagram = get_hexagram(sonuc["gate"])
    return {
        "gate": sonuc["gate"],
        "line": sonuc["line"],
        "longitude": round(lon, 2),
        "hour_known": hour_known,
        "wheel_version": WHEEL_VERSION,
        "hexagram": hexagram,
        # Sınır beyanı: saatsiz doğumda kapı sınırı gün içinde aşılmışsa
        # alternatif kapı da söylenir; çizgi zaten iddia edilmez.
        "alternate_gate": alternate,
        "alternate_hexagram": get_hexagram(alternate) if alternate else None,
    }
