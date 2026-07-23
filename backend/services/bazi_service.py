"""BaZi (Dört Sütun / Kaderin Sekiz Karakteri) hesaplama motoru.

Gerçek güneş terimlerine (Jie Qi) dayanır: Güneş'in ekliptik boylamı Swiss
Ephemeris ile hesaplanır, ay sütunları 30 derecelik güneş dilimlerine göre
belirlenir (klasik Ziping yöntemi).

- Yıl sütunu: Li Chun (Güneş 315 derece) sınırına göre
- Ay sütunu: Beş Kaplan kuralı (yıl gövdesinden ay gövdesi)
- Gün sütunu: 1949-10-01 = JiaZi çapası ile doğrulanmış 60'lık döngü
- Saat sütunu: Beş Sıçan kuralı (gün gövdesinden saat gövdesi)
- Şans Sütunları (Da Yun): cinsiyet + yıl polaritesine göre ileri/geri,
  başlangıç yaşı bir sonraki/önceki Jie sınırına olan gün sayısı / 3
"""
from __future__ import annotations

import datetime as dt
from typing import Any
from zoneinfo import ZoneInfo

import swisseph as swe

from services.geo_service import resolve_city

STEMS = [
    {"pinyin": "Jia", "cn": "甲", "element": "Ahşap", "polarity": "Yang"},
    {"pinyin": "Yi", "cn": "乙", "element": "Ahşap", "polarity": "Yin"},
    {"pinyin": "Bing", "cn": "丙", "element": "Ateş", "polarity": "Yang"},
    {"pinyin": "Ding", "cn": "丁", "element": "Ateş", "polarity": "Yin"},
    {"pinyin": "Wu", "cn": "戊", "element": "Toprak", "polarity": "Yang"},
    {"pinyin": "Ji", "cn": "己", "element": "Toprak", "polarity": "Yin"},
    {"pinyin": "Geng", "cn": "庚", "element": "Metal", "polarity": "Yang"},
    {"pinyin": "Xin", "cn": "辛", "element": "Metal", "polarity": "Yin"},
    {"pinyin": "Ren", "cn": "壬", "element": "Su", "polarity": "Yang"},
    {"pinyin": "Gui", "cn": "癸", "element": "Su", "polarity": "Yin"},
]

BRANCHES = [
    {"pinyin": "Zi", "cn": "子", "animal": "Sıçan", "element": "Su"},
    {"pinyin": "Chou", "cn": "丑", "animal": "Öküz", "element": "Toprak"},
    {"pinyin": "Yin", "cn": "寅", "animal": "Kaplan", "element": "Ahşap"},
    {"pinyin": "Mao", "cn": "卯", "animal": "Tavşan", "element": "Ahşap"},
    {"pinyin": "Chen", "cn": "辰", "animal": "Ejderha", "element": "Toprak"},
    {"pinyin": "Si", "cn": "巳", "animal": "Yılan", "element": "Ateş"},
    {"pinyin": "Wu", "cn": "午", "animal": "At", "element": "Ateş"},
    {"pinyin": "Wei", "cn": "未", "animal": "Keçi", "element": "Toprak"},
    {"pinyin": "Shen", "cn": "申", "animal": "Maymun", "element": "Metal"},
    {"pinyin": "You", "cn": "酉", "animal": "Horoz", "element": "Metal"},
    {"pinyin": "Xu", "cn": "戌", "animal": "Köpek", "element": "Toprak"},
    {"pinyin": "Hai", "cn": "亥", "animal": "Domuz", "element": "Su"},
]

# Element üretim döngüsü: Ahşap -> Ateş -> Toprak -> Metal -> Su -> Ahşap
_ELEMENT_ORDER = ["Ahşap", "Ateş", "Toprak", "Metal", "Su"]

# On Tanrı (Ten Gods) — Day Master ile diğer gövdeler arasındaki ilişki
_TEN_GODS = {
    ("same", True): ("Bi Jian", "Omuz Omuza (Dostluk, benlik gücü)"),
    ("same", False): ("Jie Cai", "Servet Ortağı (Rekabet, paylaşım)"),
    ("produces_me", True): ("Pian Yin", "Dolaylı Kaynak (Sezgi, alternatif bilgelik)"),
    ("produces_me", False): ("Zheng Yin", "Doğrudan Kaynak (Öğrenme, koruma, anne)"),
    ("i_produce", True): ("Shi Shen", "Yetenek Yıldızı (Üretkenlik, ifade)"),
    ("i_produce", False): ("Shang Guan", "Parlak Zeka (Yaratıcılık, kural tanımazlık)"),
    ("i_control", True): ("Pian Cai", "Dolaylı Servet (Fırsat, girişimcilik)"),
    ("i_control", False): ("Zheng Cai", "Doğrudan Servet (Birikim, istikrarlı kazanç)"),
    ("controls_me", True): ("Qi Sha", "Yedi Katil (Hırs, disiplin, meydan okuma)"),
    ("controls_me", False): ("Zheng Guan", "Doğrudan Otorite (Statü, sorumluluk)"),
}


def _element_relation(me: str, other: str) -> str:
    i, j = _ELEMENT_ORDER.index(me), _ELEMENT_ORDER.index(other)
    if i == j:
        return "same"
    if (i + 1) % 5 == j:
        return "i_produce"
    if (j + 1) % 5 == i:
        return "produces_me"
    if (i + 2) % 5 == j:
        return "i_control"
    return "controls_me"


def _ten_god(day_stem: int, other_stem: int) -> dict[str, str]:
    me, other = STEMS[day_stem], STEMS[other_stem]
    relation = _element_relation(me["element"], other["element"])
    same_polarity = me["polarity"] == other["polarity"]
    name, desc = _TEN_GODS[(relation, same_polarity)]
    return {"name": name, "meaning": desc}


def _sun_longitude(when_utc: dt.datetime) -> float:
    jd = swe.julday(
        when_utc.year, when_utc.month, when_utc.day,
        when_utc.hour + when_utc.minute / 60 + when_utc.second / 3600,
    )
    pos, _ = swe.calc_ut(jd, swe.SUN)
    return pos[0] % 360


def _pillar(stem_idx: int, branch_idx: int) -> dict[str, Any]:
    s, b = STEMS[stem_idx % 10], BRANCHES[branch_idx % 12]
    return {
        "stem": {"index": stem_idx % 10, **s},
        "branch": {"index": branch_idx % 12, **b},
        "label": f"{s['cn']}{b['cn']} ({s['pinyin']} {b['pinyin']})",
    }


def _find_jie_boundary(start_utc: dt.datetime, forward: bool) -> dt.datetime:
    """Bir sonraki/önceki güneş terimi (Jie: boylam % 30 == 15 dereceleri
    değil, ay sınırları 315+30k) anını 1 saatlik adım + ikili arama ile bulur."""
    def month_index(t: dt.datetime) -> int:
        return int(((_sun_longitude(t) - 315) % 360) // 30)

    step = dt.timedelta(hours=6) * (1 if forward else -1)
    t = start_utc
    base = month_index(t)
    for _ in range(140 * 4):  # en fazla ~35 gün
        t2 = t + step
        if month_index(t2) != base:
            lo, hi = (t, t2) if forward else (t2, t)
            for _ in range(30):
                mid = lo + (hi - lo) / 2
                if (month_index(mid) != base) == forward:
                    hi = mid
                else:
                    lo = mid
            return hi if forward else lo
        t = t2
    return t


def get_bazi_chart(
    year: int, month: int, day: int, hour: int, minute: int,
    city: str = "Istanbul", nation: str | None = None,
    gender: str = "female", name: str = "Gezgin",
) -> dict[str, Any]:
    loc = resolve_city(city, nation)
    local = dt.datetime(year, month, day, hour, minute, tzinfo=ZoneInfo(loc.tz_str))
    utc = local.astimezone(dt.timezone.utc)

    sun_lon = _sun_longitude(utc)

    # --- Yıl sütunu (Li Chun sınırı) ---
    bazi_year = year
    if month <= 2 and sun_lon < 315 and sun_lon >= 270:
        bazi_year = year - 1
    year_stem = (bazi_year - 4) % 10
    year_branch = (bazi_year - 4) % 12

    # --- Ay sütunu (güneş boylamından; ay 1 = Kaplan/Yin, Li Chun'da başlar) ---
    month_no = int(((sun_lon - 315) % 360) // 30) + 1  # 1..12
    month_branch = (month_no + 1) % 12  # ay 1 -> Yin (index 2)
    five_tigers = {0: 2, 5: 2, 1: 4, 6: 4, 2: 6, 7: 6, 3: 8, 8: 8, 4: 0, 9: 0}
    month_stem = (five_tigers[year_stem] + (month_no - 1)) % 10

    # --- Gün sütunu (60'lık döngü; 23:00 sonrası ertesi güne sayılır) ---
    day_date = local.date()
    if local.hour >= 23:
        day_date = day_date + dt.timedelta(days=1)
    days_since_anchor = (day_date - dt.date(1900, 1, 1)).days
    day_cycle = (days_since_anchor + 10) % 60  # 1900-01-01 = JiaXu (10)
    day_stem, day_branch = day_cycle % 10, day_cycle % 12

    # --- Saat sütunu ---
    hour_branch = ((local.hour + 1) // 2) % 12
    five_rats = {0: 0, 5: 0, 1: 2, 6: 2, 2: 4, 7: 4, 3: 6, 8: 6, 4: 8, 9: 8}
    hour_stem = (five_rats[day_stem] + hour_branch) % 10

    pillars = {
        "year": _pillar(year_stem, year_branch),
        "month": _pillar(month_stem, month_branch),
        "day": _pillar(day_stem, day_branch),
        "hour": _pillar(hour_stem, hour_branch),
    }

    # --- Day Master ve On Tanrı ---
    day_master = {
        **STEMS[day_stem],
        "description": (
            f"Günün Efendisi: {STEMS[day_stem]['polarity']} {STEMS[day_stem]['element']} "
            f"({STEMS[day_stem]['cn']} {STEMS[day_stem]['pinyin']})"
        ),
    }
    ten_gods = {
        "year": _ten_god(day_stem, year_stem),
        "month": _ten_god(day_stem, month_stem),
        "hour": _ten_god(day_stem, hour_stem),
    }

    # --- Element dağılımı ---
    element_count: dict[str, int] = {e: 0 for e in _ELEMENT_ORDER}
    for p in pillars.values():
        element_count[p["stem"]["element"]] += 1
        element_count[p["branch"]["element"]] += 1
    dominant = max(element_count, key=element_count.get)
    missing = [e for e, c in element_count.items() if c == 0]

    # --- Şans Sütunları (Da Yun) ---
    yang_year = STEMS[year_stem]["polarity"] == "Yang"
    is_male = gender.lower() in ("male", "erkek", "m", "man")
    forward = yang_year == is_male  # yang+erkek veya yin+kadın -> ileri
    boundary = _find_jie_boundary(utc, forward=forward)
    days_to_boundary = abs((boundary - utc).total_seconds()) / 86400
    start_age = max(1, round(days_to_boundary / 3))

    luck_pillars = []
    for i in range(1, 9):
        offset = i if forward else -i
        lp = _pillar(month_stem + offset, month_branch + offset)
        luck_pillars.append({
            "from_age": start_age + (i - 1) * 10,
            "to_age": start_age + i * 10 - 1,
            **lp,
            "ten_god": _ten_god(day_stem, (month_stem + offset) % 10),
        })

    return {
        "name": name,
        "gender": "Erkek" if is_male else "Kadın",
        "birth_local": local.isoformat(),
        "timezone": loc.tz_str,
        "pillars": pillars,
        "day_master": day_master,
        "ten_gods": ten_gods,
        "element_distribution": element_count,
        "dominant_element": dominant,
        "missing_elements": missing,
        "zodiac_animal": BRANCHES[year_branch]["animal"],
        "luck_pillars": luck_pillars,
        "luck_direction": "forward" if forward else "backward",
    }
