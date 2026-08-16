"""Sinyal motoru (R2-S1): "Rytho bugün senin için 3 şey fark etti."

Ürün tezinin çekirdeği: Rytho sorulmadan konuşan kişisel astrologdur.
Bu modül kişisel transit takviminden (predict_service) bugünü ve yaklaşan
7 günü okur, olayları ÖNEMİNE göre sıralar, her birini bir yaşam temasına
eşler ve en fazla 3 "sinyal" döndürür.

Dürüstlük kuralları ("ölçülmeyen söylenmez"):
- Sıralama ve tema eşleme TAMAMEN determinist — LLM yok, sabit tablolar.
  Aynı gökyüzü + aynı harita = aynı sinyaller.
- Her sinyal DAYANAĞINI taşır: gezen gezegen, natal nokta (burcu ve eviyle),
  açı, ölçülen orb, kesinleşme tarihi. "Neden?" sorusunun cevabı üretilen
  metin değil, bu ölçülmüş alanlardır; mobil alt-sayfası bunları çizer.
- Metinleştirme iki katmanlı: başlık ŞABLONDUR (localize katmanı, LLM'siz,
  her katmana açık); tek cümlelik yorum ("insight") yalnız abonelere ve
  TEK LLM çağrısıyla üçü birden üretilir (birim ekonomi kuralı).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import logging
from typing import Any

from services import chart_context, gemini_service, predict_service, prompts

logger = logging.getLogger(__name__)

#: Sinyal hesabı sürümü — sıralama/tema tabloları değişince artar,
#: önbellekler tazelenir (PREDICT_CALC_VERSION disiplini).
#: v2 (R2-S6): `tone` alanı eklendi ve ayrılan açı puanı düştü; sürüm
#: artmasaydı eski kayıtlar 24 saat boyunca tonsuz (yanlış cümleli)
#: servis edilirdi.
SIGNAL_CALC_VERSION = "2"

#: Pencere: bugün + 7 gün. Daha uzunu "bugün senin için" iddiasını sulandırır.
WINDOW_DAYS = 8

#: En fazla kaç sinyal döner. Üçten fazlası liste olur, sinyal olmaz.
MAX_SIGNALS = 3

#: Sinyale girebilen natal noktalar: yedili + eksenler. Düğümler ve Lilith
#: takvimde kalır ama sinyal olmaz — "hayatının şu alanı" iddiasını en net
#: taşıyan noktalar bunlardır.
_SINYAL_NATAL = chart_context._ASPECT_POINTS

#: Gezen gezegen ağırlığı: dönemi işaretleyen yavaşlar üstte (takvime zaten
#: yalnız yavaşlar girer — predict_service._TRANSIT_GEZEGENLERI).
_GEZEN_AGIRLIK = {
    "Pluto": 5.0, "Neptune": 4.5, "Uranus": 4.5,
    "Saturn": 4.0, "Jupiter": 3.5, "Chiron": 3.0,
}

#: Natal noktanın kişisel ağırlığı: ışıklar ve eksenler en önde.
_NATAL_AGIRLIK = {
    "Sun": 3.0, "Moon": 3.0, "Ascendant": 3.0, "Medium_Coeli": 3.0,
    "Mercury": 2.5, "Venus": 2.5, "Mars": 2.5,
    "Jupiter": 2.0, "Saturn": 2.0,
}
_NATAL_AGIRLIK_VARSAYILAN = 1.5

#: Açı ağırlığı: kavuşum ve sert açılar dönemi daha güçlü işaretler.
_ACI_AGIRLIK = {
    "conjunction": 1.3, "opposition": 1.2, "square": 1.15,
    "trine": 1.0, "sextile": 0.85,
}

#: Yaklaşan açı güçlenir; ayrılan sönmektedir. Ayrılana CEZA (R2-S6):
#: sönmekte olan bir etki "bugün fark ettiklerim" listesinde en son sırayı
#: hak eder — yoksa kartın cümlesi ("kolaylaşıyor") zamanlama satırıyla
#: ("etkisi sönüyor") çelişir.
_YAKLASMA_CARPANI = 1.2
_AYRILMA_CARPANI = 0.7

#: Tema anahtarları — l10n adları prompts katmanında (SIGNAL_THEME_NAMES).
THEMES = ("career", "relationships", "inner", "finance")

#: Natal noktanın DOĞUM EVİNDEN tema: ev, noktanın hayatta nereye
#: bağlandığını gezegen doğasından daha kişisel söyler.
_EV_TEMASI = {
    1: "inner", 2: "finance", 3: "relationships", 4: "inner",
    5: "relationships", 6: "career", 7: "relationships", 8: "finance",
    9: "inner", 10: "career", 11: "relationships", 12: "inner",
}

#: Açının TONU (R2-S6): kart yüzeyindeki insan dili cümle bundan seçilir.
#: Destekleyici açılar akış, sert açılar gerilim, kavuşum yoğunlaşma anlatır
#: — bu geleneksel astrolojinin kendi ayrımı, uydurma değil.
_TON = {
    "trine": "support", "sextile": "support",
    "square": "tension", "opposition": "tension",
    "conjunction": "focus",
}

#: Ev bilinmiyorsa (saat yok / eksen / dış gezegen) noktanın doğasından tema.
_NOKTA_TEMASI = {
    "Sun": "career", "Moon": "inner", "Mercury": "relationships",
    "Venus": "relationships", "Mars": "career", "Jupiter": "finance",
    "Saturn": "career", "Uranus": "inner", "Neptune": "inner",
    "Pluto": "inner", "Chiron": "inner",
    "Ascendant": "inner", "Medium_Coeli": "career",
}


def _natal_yerlesim(natal: dict[str, Any] | None,
                    nokta: str) -> dict[str, Any] | None:
    """natal_facts çıktısından noktanın yerleşimi (burç + ev)."""
    if not natal:
        return None
    if nokta == "Ascendant":
        burc = natal.get("ascendant")
        return {"sign": burc, "house": 1} if burc else None
    if nokta == "Medium_Coeli":
        # MC'nin burcu natal_facts'te yok; evi tanım gereği 10.
        return {"house": 10}
    for y in [natal.get("sun"), natal.get("moon"),
              *(natal.get("placements") or [])]:
        if y and y.get("planet") == nokta:
            return y
    return None


def _tema(nokta: str, yerlesim: dict[str, Any] | None) -> str:
    ev = (yerlesim or {}).get("house")
    if isinstance(ev, int) and ev in _EV_TEMASI:
        return _EV_TEMASI[ev]
    return _NOKTA_TEMASI.get(nokta, "inner")


def _puan(aday: dict[str, Any]) -> float:
    """Determinist önem puanı — testler sıralamayı buna göre iddia eder."""
    p = (_GEZEN_AGIRLIK.get(aday["transit"], 3.0)
         * _NATAL_AGIRLIK.get(aday["natal"], _NATAL_AGIRLIK_VARSAYILAN)
         * _ACI_AGIRLIK.get(aday["aspect"], 1.0))
    if aday.get("active"):
        # Bugün orb içinde: ne kadar darsa o kadar baskın.
        p *= 1.5 / (1.0 + float(aday.get("orb") or 0.0))
        if aday.get("movement") == "applying":
            p *= _YAKLASMA_CARPANI
        elif aday.get("movement") == "separating":
            p *= _AYRILMA_CARPANI
    else:
        # Henüz orb dışında ama pencere içinde kesinleşecek.
        p *= 1.0 / (1.0 + float(aday.get("days_to_exact") or 0))
    return p


def compute_signals(birth: dict[str, Any], hour_known: bool = True,
                    natal: dict[str, Any] | None = None,
                    start: dt.datetime | None = None) -> dict[str, Any]:
    """Sinyalleri hesaplar — LLM yok, sıralama determinist.

    ``natal`` verilirse (chart_context.natal_facts çıktısı) ev tabanlı tema
    eşlemesi kullanılır; verilmezse hesaplanmaya çalışılır, düşerse nokta
    tabanlı temaya geri düşülür — sinyal üretimi natal olgulara MUHTAÇ değil.
    """
    cal = predict_service.transit_calendar(
        **birth, hour_known=hour_known, days=WINDOW_DAYS, start=start)
    bugun = dt.date.fromisoformat(cal["start"])

    if natal is None:
        try:
            natal = chart_context.natal_facts(birth)
        except Exception as exc:
            logger.warning("Sinyal için natal olgular üretilemedi: %s", exc)
            natal = None

    # Pencere içindeki kesinleşmeler: (gezen, natal, açı) -> tarih.
    kesinlesmeler: dict[tuple[str, str, str], str] = {}
    for o in cal.get("events") or []:
        if o.get("type") != "aspect_exact":
            continue
        anahtar = (o["transit"], o["natal"], o["aspect"])
        # Aynı açı pencerede iki kez kesinleşmez; ilk tarih kalır.
        kesinlesmeler.setdefault(anahtar, o["date"])

    adaylar: dict[tuple[str, str, str], dict[str, Any]] = {}

    # 1) Bugün orb içinde olanlar.
    for a in cal.get("active_now") or []:
        if a.get("natal") not in _SINYAL_NATAL:
            continue
        anahtar = (a["transit"], a["natal"], a["aspect"])
        aday: dict[str, Any] = {
            "transit": a["transit"], "natal": a["natal"],
            "aspect": a["aspect"], "orb": a.get("orb"),
            "movement": a.get("movement"), "active": True,
        }
        if anahtar in kesinlesmeler:
            aday["exact_on"] = kesinlesmeler[anahtar]
            aday["days_to_exact"] = (
                dt.date.fromisoformat(aday["exact_on"]) - bugun).days
        adaylar[anahtar] = aday

    # 2) Bugün orb dışında ama pencerede kesinleşecekler.
    for anahtar, tarih in kesinlesmeler.items():
        if anahtar in adaylar or anahtar[1] not in _SINYAL_NATAL:
            continue
        adaylar[anahtar] = {
            "transit": anahtar[0], "natal": anahtar[1],
            "aspect": anahtar[2], "orb": None, "movement": None,
            "active": False, "exact_on": tarih,
            "days_to_exact": (dt.date.fromisoformat(tarih) - bugun).days,
        }

    # Zenginleştir + puanla.
    liste = []
    for aday in adaylar.values():
        yerlesim = _natal_yerlesim(natal, aday["natal"])
        aday["theme"] = _tema(aday["natal"], yerlesim)
        aday["tone"] = _TON.get(aday["aspect"], "focus")
        if yerlesim:
            if yerlesim.get("sign"):
                aday["natal_sign"] = yerlesim["sign"]
            if isinstance(yerlesim.get("house"), int):
                aday["natal_house"] = yerlesim["house"]
        aday["score"] = round(_puan(aday), 4)
        liste.append(aday)
    liste.sort(key=lambda a: (-a["score"], a["transit"], a["natal"]))

    # Tema çeşitliliği: 2. ve 3. sırada, henüz kullanılmamış temanın en
    # güçlüsü tercih edilir; kalmadıysa genel sıra doldurur. Amaç üç kartın
    # üçünün de "kariyer" dememesi — analiz kararı, ürün sesi.
    secilen: list[dict[str, Any]] = []
    kalan = list(liste)
    while kalan and len(secilen) < MAX_SIGNALS:
        kullanilan = {s["theme"] for s in secilen}
        yeni_temali = next(
            (a for a in kalan if a["theme"] not in kullanilan), None)
        secim = yeni_temali if yeni_temali is not None else kalan[0]
        secilen.append(secim)
        kalan.remove(secim)

    return {
        "calc_version": SIGNAL_CALC_VERSION,
        "generated_for": cal["start"],
        "signals": secilen,
        "disclosures": cal.get("disclosures") or [],
    }


# ---------------------------------------------------------------------------
# Önbellekli erişim — uç (api/reports) ve bildirim (api/notify) AYNI kaydı
# paylaşır; sinyaller günde bir kez / harita başına hesaplanır.
# ---------------------------------------------------------------------------

def cached_signals(profile: dict[str, Any],
                   today: dt.date | None = None) -> dict[str, Any] | None:
    """Profilden sinyaller, doğum verisine anahtarlı paylaşımlı önbellekle.

    Doğum verisi yoksa None: sinyal "senin haritan" iddiasıdır ve varsayılan
    doğum verisiyle üretilemez (chart_context.has_birth_data kuralı).
    """
    from core import cache
    from services import profile_service

    if not chart_context.has_birth_data(profile):
        return None
    birth = profile_service.birth_kwargs(profile)
    saat_biliniyor = bool(str(profile.get("birthTime") or "").strip())
    gun = (today or dt.date.today()).isoformat()
    ozet = chart_context._birth_digest(birth)

    anahtar = (f"signals-{SIGNAL_CALC_VERSION}-"
               f"{predict_service.PREDICT_CALC_VERSION}-{ozet}-"
               f"{saat_biliniyor}-{gun}")
    ham = cache.get(anahtar)
    if ham is None:
        ham = compute_signals(birth, hour_known=saat_biliniyor)
        cache.set(anahtar, ham, ttl_seconds=24 * 3600)
    return ham


# ---------------------------------------------------------------------------
# Abone yorumu — tek LLM çağrısı, üç sinyal birden
# ---------------------------------------------------------------------------

def signals_fingerprint(ham: dict[str, Any]) -> str:
    """Sinyal kümesinin özet anahtarı — yorum önbelleği buna bağlanır.

    Hesap sürümü de imzaya girer: prompt kuralları değiştiğinde (S6'da
    "gezegen adı kullanma") eski yorumlar TTL boyunca servis edilmesin.
    """
    imza = "|".join(
        f"{s['transit']}-{s['aspect']}-{s['natal']}-{s.get('exact_on')}"
        for s in ham.get("signals") or [])
    return hashlib.sha256(
        f"{SIGNAL_CALC_VERSION}|{ham.get('generated_for')}|{imza}"
        .encode()).hexdigest()[:20]


def signal_insights(ham: dict[str, Any], lang: str) -> list[str] | None:
    """Her sinyal için tek cümlelik yorum — üçü TEK çağrıda.

    Model satır sayısını tutturamazsa None döner ve arayüz şablon başlıkla
    yaşar; yarım/uydurma eşleştirme yapılmaz.
    """
    sinyaller = ham.get("signals") or []
    if not sinyaller:
        return None
    p = prompts.get(lang)
    satirlar = []
    for i, s in enumerate(sinyaller, 1):
        parca = (f"{i}. {prompts.planet_name(lang, s['transit'])} "
                 f"{prompts.aspect_name(lang, s['aspect'])} "
                 f"natal {prompts.planet_name(lang, s['natal'])}")
        if s.get("exact_on"):
            parca += f" ({p.SIGNAL_EXACT_LABEL}: {s['exact_on']})"
        elif s.get("orb") is not None:
            parca += f" (orb {s['orb']}°)"
        parca += f" — {p.SIGNAL_THEME_NAMES.get(s['theme'], s['theme'])}"
        satirlar.append(parca)

    prompt = p.SIGNALS_PROMPT.format(count=len(sinyaller),
                                     lines="\n".join(satirlar))
    try:
        metin = (gemini_service.generate(prompt, lang=lang) or "").strip()
    except Exception as exc:
        logger.warning("Sinyal yorumu üretilemedi: %s", exc)
        return None

    yorumlar: list[str] = []
    for satir in metin.splitlines():
        satir = satir.strip().strip('"').strip()
        if not satir:
            continue
        # "1." / "1)" / "-" öneklerini soy.
        for onek in (f"{len(yorumlar) + 1}.", f"{len(yorumlar) + 1})", "-"):
            if satir.startswith(onek):
                satir = satir[len(onek):].strip()
                break
        yorumlar.append(satir)
    if len(yorumlar) != len(sinyaller) or any(
            len(y) > p.SIGNAL_INSIGHT_MAX for y in yorumlar):
        logger.info("Sinyal yorumu biçim dışı (%s satır), şablona düşüldü",
                    len(yorumlar))
        return None
    return yorumlar
