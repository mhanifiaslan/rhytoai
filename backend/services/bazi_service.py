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
    {"pinyin": "Jia", "cn": "甲", "element": "wood", "polarity": "Yang"},
    {"pinyin": "Yi", "cn": "乙", "element": "wood", "polarity": "Yin"},
    {"pinyin": "Bing", "cn": "丙", "element": "fire", "polarity": "Yang"},
    {"pinyin": "Ding", "cn": "丁", "element": "fire", "polarity": "Yin"},
    {"pinyin": "Wu", "cn": "戊", "element": "earth", "polarity": "Yang"},
    {"pinyin": "Ji", "cn": "己", "element": "earth", "polarity": "Yin"},
    {"pinyin": "Geng", "cn": "庚", "element": "metal", "polarity": "Yang"},
    {"pinyin": "Xin", "cn": "辛", "element": "metal", "polarity": "Yin"},
    {"pinyin": "Ren", "cn": "壬", "element": "water", "polarity": "Yang"},
    {"pinyin": "Gui", "cn": "癸", "element": "water", "polarity": "Yin"},
]

BRANCHES = [
    {"pinyin": "Zi", "cn": "子", "animal": "rat", "element": "water"},
    {"pinyin": "Chou", "cn": "丑", "animal": "ox", "element": "earth"},
    {"pinyin": "Yin", "cn": "寅", "animal": "tiger", "element": "wood"},
    {"pinyin": "Mao", "cn": "卯", "animal": "rabbit", "element": "wood"},
    {"pinyin": "Chen", "cn": "辰", "animal": "dragon", "element": "earth"},
    {"pinyin": "Si", "cn": "巳", "animal": "snake", "element": "fire"},
    {"pinyin": "Wu", "cn": "午", "animal": "horse", "element": "fire"},
    {"pinyin": "Wei", "cn": "未", "animal": "goat", "element": "earth"},
    {"pinyin": "Shen", "cn": "申", "animal": "monkey", "element": "metal"},
    {"pinyin": "You", "cn": "酉", "animal": "rooster", "element": "metal"},
    {"pinyin": "Xu", "cn": "戌", "animal": "dog", "element": "earth"},
    {"pinyin": "Hai", "cn": "亥", "animal": "pig", "element": "water"},
]

# Element uretim dongusu: wood -> fire -> earth -> metal -> water -> wood
# Degerler dilden bagimsiz ANAHTARDIR; adlar services/prompts altinda.
_ELEMENT_ORDER = ["wood", "fire", "earth", "metal", "water"]

# On Tanri (Ten Gods) — Day Master ile diger govdeler arasindaki iliski.
#
# Pinyin ad dilden bagimsizdir; ACIKLAMA metni tasinmaz, yerine anahtar
# doner (services/prompts altindaki TEN_GOD_MEANINGS tablosundan cozulur).
_TEN_GODS = {
    ("same", True): ("Bi Jian", "bi_jian"),
    ("same", False): ("Jie Cai", "jie_cai"),
    ("produces_me", True): ("Pian Yin", "pian_yin"),
    ("produces_me", False): ("Zheng Yin", "zheng_yin"),
    ("i_produce", True): ("Shi Shen", "shi_shen"),
    ("i_produce", False): ("Shang Guan", "shang_guan"),
    ("i_control", True): ("Pian Cai", "pian_cai"),
    ("i_control", False): ("Zheng Cai", "zheng_cai"),
    ("controls_me", True): ("Qi Sha", "qi_sha"),
    ("controls_me", False): ("Zheng Guan", "zheng_guan"),
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
    name, meaning_key = _TEN_GODS[(relation, same_polarity)]
    return {"name": name, "meaning_key": meaning_key}


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
    # Aciklama metni burada KURULMAZ: "Gunun Efendisi: Yang Ahsap" gibi bir
    # cumle dili yuke gomerdi. Bilesenler doner, cumle isteğin dilinde
    # services/prompts icinde kurulur.
    day_master = {**STEMS[day_stem]}
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
    is_female = gender.lower() in ("female", "kadin", "kadın", "f", "woman")
    # Cinsiyet "other" (ya da tanınmayan bir değer) ise yön YİN kuralıyla
    # hesaplanır — ama artık SESSİZCE değil. Klasik yöntem yön için ikili
    # bir temel ister; temeli biz seçiyorsak bunu söylemek zorundayız.
    # Anahtar localize_bazi'de cümleye çevrilir, rapor ve ekranda görünür.
    gender_note_key = None if (is_male or is_female) else "luck_direction_yin"
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
        "gender": "male" if is_male else "female",
        # Hesap sürümü: hesap davranışı değişen her fazda artar ve rapor
        # önbellek anahtarına girer — eski metinler kendiliğinden düşer,
        # "yeni harita + 30 günlük eski rapor" çelişkisi hiç yaşanmaz.
        "calc_version": "2",
        "gender_note_key": gender_note_key,
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
