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


# ---------------------------------------------------------------------------
# İkincil progresyon + solar arc (T2)
# ---------------------------------------------------------------------------

#: Gregoryen ortalama yıl — gün-yıl dönüşümünün tek sabiti.
_YIL_GUN = 365.2425

#: Solar arc kesinleşmelerinde yönlendirilen noktalar.
_ARC_YONLENDIRILEN = ["sun", "moon", "mercury", "venus", "mars",
                      "jupiter", "saturn"]
_MAJOR_ARC_ACILARI = [(0, "conjunction"), (60, "sextile"), (90, "square"),
                      (120, "trine"), (180, "opposition")]

_BURCLAR = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir",
            "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]


def _prog_ani(birth_utc: dt.datetime, on: dt.datetime) -> dt.datetime:
    """Gün-yıl kuralı: doğumdan N yıl sonrası = doğumdan N GÜN sonrası."""
    yas_yil = (on - birth_utc).total_seconds() / (86400 * _YIL_GUN)
    return birth_utc + dt.timedelta(days=yas_yil)


def secondary_progressions(
    name: str, year: int, month: int, day: int, hour: int, minute: int,
    city: str, nation: str | None = None, hour_known: bool = True,
    on_date: dt.datetime | None = None,
) -> dict[str, Any]:
    """İkincil progresyon özeti — omurga progres Ay.

    Gün-yıl kuralı: doğumdan sonraki her GÜN, yaşamın bir YILINA karşılık
    gelir. Progres harita, doğum anına yaş kadar gün eklenerek kurulur.
    Progres ASC/MC solar arc yöntemiyle türetilir (quotidian kapsam dışı,
    bilinçli sadelik) ve yalnızca doğum saati biliniyorsa üretilir.
    """
    from zoneinfo import ZoneInfo

    natal, loc = astro_service._build_subject(
        name, year, month, day, hour, minute, city, nation)
    tz = ZoneInfo(loc.tz_str)
    birth_local = dt.datetime(year, month, day, hour, minute, tzinfo=tz)
    birth_utc = birth_local.astimezone(dt.timezone.utc)
    simdi = on_date or dt.datetime.now(dt.timezone.utc)

    prog_utc = _prog_ani(birth_utc, simdi)
    prog_yerel = prog_utc.astimezone(tz)
    prog, _ = astro_service._build_subject(
        name, prog_yerel.year, prog_yerel.month, prog_yerel.day,
        prog_yerel.hour, prog_yerel.minute, city, nation)

    # --- Progres Ay: burç + natal ev + SONRAKİ burç değişim tarihi ---
    ay = prog.moon
    ay_hizi = abs(float(getattr(ay, "speed", None) or 13.0))  # derece/prog-gün
    kalan_derece = 30.0 - float(ay.position)
    # 1 prog-gün = 1 gerçek yıl olduğundan kalan/hız = YIL. Hız değişkendir
    # ama progres Ay ayda ~1 derece ilerler; tek adım yeterli hassasiyet.
    kalan_yil = kalan_derece / ay_hizi
    degisim_tarihi = simdi + dt.timedelta(days=kalan_yil * _YIL_GUN)

    # Progres Ay'ın NATAL evlerdeki yeri (saat biliniyorsa anlamlı).
    ay_natal_evi = None
    if hour_known:
        ev_adlari = [
            "first_house", "second_house", "third_house", "fourth_house",
            "fifth_house", "sixth_house", "seventh_house", "eighth_house",
            "ninth_house", "tenth_house", "eleventh_house", "twelfth_house",
        ]
        ev_uclari = [(i + 1, float(getattr(natal, h).abs_pos))
                     for i, h in enumerate(ev_adlari)]
        boylam = float(ay.abs_pos)
        for i, (ev_no, uc) in enumerate(ev_uclari):
            sonraki_uc = ev_uclari[(i + 1) % 12][1]
            if uc <= sonraki_uc:
                icinde = uc <= boylam < sonraki_uc
            else:  # 360 derece sarması
                icinde = boylam >= uc or boylam < sonraki_uc
            if icinde:
                ay_natal_evi = ev_no
                break

    # --- Progres lunasyon fazı (Ay-Güneş uzanımı, 8 evre) ---
    uzanim = (float(ay.abs_pos) - float(prog.sun.abs_pos)) % 360
    faz_siniri = [(22.5, "new_moon"), (67.5, "waxing_crescent"),
                  (112.5, "first_quarter"), (157.5, "waxing_gibbous"),
                  (202.5, "full_moon"), (247.5, "waning_gibbous"),
                  (292.5, "last_quarter"), (337.5, "waning_crescent"),
                  (360.1, "new_moon")]
    faz = next(ad for sinir, ad in faz_siniri if uzanim < sinir)

    # --- Progres Güneş + solar arc ---
    arc = (float(prog.sun.abs_pos) - float(natal.sun.abs_pos)) % 360
    gunes_hizi = abs(float(getattr(prog.sun, "speed", None) or 0.9856))
    gunes_kalan_yil = (30.0 - float(prog.sun.position)) / gunes_hizi

    disclosures: list[str] = []
    if loc.fallback:
        disclosures.append("geo_fallback_city")
    if not hour_known:
        disclosures.append("prog_hour_unknown")

    sonuc: dict[str, Any] = {
        "calc_version": PREDICT_CALC_VERSION,
        "as_of": simdi.date().isoformat(),
        "prog_moon": {
            "sign": ay.sign,
            "position": round(float(ay.position), 2),
            "natal_house": ay_natal_evi,
            "next_sign_at": degisim_tarihi.date().isoformat(),
            "phase": faz,
        },
        "prog_sun": {
            "sign": prog.sun.sign,
            "position": round(float(prog.sun.position), 2),
            "next_sign_in_years": round(gunes_kalan_yil, 1),
        },
        "solar_arc_deg": round(arc, 2),
        "disclosures": disclosures,
    }

    if hour_known:
        # Solar arc yöntemi: natal ASC/MC + yay.
        asc_abs = (float(natal.first_house.abs_pos) + arc) % 360
        mc_abs = (float(natal.tenth_house.abs_pos) + arc) % 360
        sonuc["prog_asc"] = {"sign": _BURCLAR[int(asc_abs // 30)],
                             "position": round(asc_abs % 30, 2)}
        sonuc["prog_mc"] = {"sign": _BURCLAR[int(mc_abs // 30)],
                            "position": round(mc_abs % 30, 2)}
    return sonuc


def solar_arc_hits(
    name: str, year: int, month: int, day: int, hour: int, minute: int,
    city: str, nation: str | None = None, hour_known: bool = True,
    years: float = 3.0, limit: int = 10,
) -> list[dict[str, Any]]:
    """Önümüzdeki N yılda solar arc kesinleşmeleri — KAPALI FORM.

    Tüm noktalar aynı yayla yönlendirildiği için "yönlendirilen X'in natal
    Y'ye A açısı" tam şu yayda kesinleşir: arc = (Y - X +- A) (mod 360).
    Aramaya gerek yok; mevcut yay ve yıllık hızla tarih doğrudan çözülür.
    """
    natal, _ = astro_service._build_subject(
        name, year, month, day, hour, minute, city, nation)
    prog = secondary_progressions(
        name, year, month, day, hour, minute, city, nation,
        hour_known=hour_known)
    arc_simdi = prog["solar_arc_deg"]
    yillik_hiz = 0.9856  # progres Güneş ortalaması (derece/yıl)
    simdi = dt.datetime.now(dt.timezone.utc)

    hedefler: dict[str, float] = {
        attr: float(getattr(natal, attr).abs_pos)
        for attr in astro_service._PLANET_NAMES
        if getattr(natal, attr, None) is not None
    }
    if hour_known:
        hedefler["ascendant"] = float(natal.first_house.abs_pos)
        hedefler["medium_coeli"] = float(natal.tenth_house.abs_pos)

    vurgular: list[dict[str, Any]] = []
    for yonlendirilen in _ARC_YONLENDIRILEN:
        x = hedefler.get(yonlendirilen)
        if x is None:
            continue
        for hedef_ad, y_boylam in hedefler.items():
            if hedef_ad == yonlendirilen:
                continue
            for aci, aci_ad in _MAJOR_ARC_ACILARI:
                isaretler = (1,) if aci in (0, 180) else (1, -1)
                for isaret in isaretler:
                    gereken = (y_boylam - x - isaret * aci) % 360
                    fark_yil = (gereken - arc_simdi) / yillik_hiz
                    if 0 <= fark_yil <= years:
                        tarih = simdi + dt.timedelta(
                            days=fark_yil * _YIL_GUN)
                        # Ad anahtarları PLANET_NAMES tablosunun biçiminde
                        # (Sun, Medium_Coeli) — localize doğrudan çözer.
                        vurgular.append({
                            "directed": yonlendirilen.title(),
                            "natal": hedef_ad.title(),
                            "aspect": aci_ad,
                            "exact_on": tarih.date().isoformat(),
                        })
    vurgular.sort(key=lambda v: v["exact_on"])
    return vurgular[:limit]
