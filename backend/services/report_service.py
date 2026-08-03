"""Rapor / Prompt Mühendisliği Servisi.

Ham hesaplama çıktıları (astroloji, BaZi, yüz, I Ching, gökyüzü) doğrudan
LLM'e verilmez; burada yapılandırılmış prompt şablonlarına dönüştürülür,
RAG bağlamı eklenir, Gemini'ye gönderilir ve sonuç kullanıcı+gün bazında
önbelleklenir (maliyet kontrolü).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import logging
from typing import Any, Callable

from core import cache, i18n
from services import (
    chart_context,
    chart_query,
    firasa_service,
    gemini_service,
    memory_service,
    prompts,
)
from services.rag_service import retrieve_context

logger = logging.getLogger(__name__)


def _memory_block(memory: str, lang: str | None = None) -> str:
    """Hafıza bağlamını prompt'a iliştirilebilir bir bloğa çevirir.

    Hafıza boşsa hiçbir başlık yazılmaz — boş bir "KULLANICI HAKKINDA" başlığı
    modeli bilmediği şeyler uydurmaya davet eder.
    """
    memory = (memory or "").strip()
    if not memory:
        return ""
    return prompts.get(lang).MEMORY_BLOCK.format(memory=memory)


def _cached_generate(cache_key: str, prompt: str, fallback: str,
                     ttl_seconds: int = 24 * 3600,
                     lang: str | None = None,
                     owner_uid: str | None = None,
                     spend: Callable[[], None] | None = None,
                     refund: Callable[[], None] | None = None) -> dict[str, Any]:
    """Üretimi önbellekli çalıştırır.

    ``owner_uid`` KİŞİYE ÖZEL üretimlerde verilir (günlük okuma, natal, BaZi,
    I Ching, sinastri, ikili dinamik). Önbellek dokümanının kimliği anahtarın
    özeti olduğu için kayıtlar kullanıcıya göre sorgulanamaz; hesap
    silindiğinde bu üretimlerin de silinebilmesi sahiplik alanına bağlı.

    Burç yorumu ve gökyüzü PAYLAŞIMLI olduğu için sahipsizdir — tek bir
    kullanıcının hesabını silmesi herkesin yorumunu silmemeli.

    ``spend`` token düşümüdür ve YALNIZCA önbellek kaçırıldığında, LLM
    çağrısından hemen önce çalışır: aynı rapora ikinci bakış ücretsizdir,
    çünkü sunucuya da maliyeti yoktur. Ücret ile maliyet aynı çizgide
    durursa kullanıcıya "neden yine ücret?" sorusu hiç doğmaz. Üretim
    fallback'e düşerse ``refund`` çağrılır — kullanıcı almadığı şeye ödemez.
    ``spend`` 402 fırlatabilir; o durumda LLM çağrısı hiç yapılmaz.
    """
    cached = cache.get(cache_key)
    if cached is not None:
        return {"text": cached, "cached": True}

    if spend is not None:
        spend()

    text = gemini_service.generate(prompt, lang=lang)
    if text:
        cache.set(cache_key, text, ttl_seconds=ttl_seconds,
                  owner_uid=owner_uid)
        return {"text": text, "cached": False}
    if refund is not None:
        refund()
    return {"text": fallback, "cached": False, "fallback": True}


def daily_reading(user_id: str, natal: dict[str, Any], sky: dict[str, Any],
                  lang: str | None = None,
                  birth: dict[str, Any] | None = None) -> dict[str, Any]:
    """Kişiye özel günlük kozmik yorum: natal harita x güncel gökyüzü.

    ``birth`` verilirse bugünün gökyüzünün HARİTAYA değdiği noktalar da
    prompt'a girer (Revize R8). Eskiden yalnızca genel gökyüzü (retrolar +
    gökyüzü geneli açılar) veriliyordu; transit-natal kesişimi — "bugün
    Satürn SENİN Güneşine kare" — sohbete gidiyor ama günlük okumaya
    gitmiyordu. Oysa kişisel günlük okumanın kişisel kısmı tam da bu.
    Ek LLM çağrısı YOK: transit hesabı yerel efemeris, önbellek anahtarı
    değişmedi.
    """
    lang = lang if lang in i18n.SUPPORTED else i18n.DEFAULT
    p = prompts.get(lang)
    today = dt.date.today().isoformat()
    # Dil önbellek anahtarına girer; aksi halde İngilizce kullanıcı Türkçe
    # üretilmiş yorumu görür.
    cache_key = f"daily-{user_id}-{today}-{lang}"

    # Önbellek isabeti prompt kurulumundan ÖNCE denetlenir (horoscope_reading
    # ile aynı gerekçe): bu satırın altında bir RAG araması — yani her
    # istekte ücretli bir embedding çağrısı — var. Aynı gün ikinci kez açılan
    # okuma, düzeltmeden önce o çağrıyı BOŞUNA yapıyordu.
    cached = cache.get(cache_key)
    if cached is not None:
        return {"text": cached, "cached": True}

    # Burç adları da dile göre: "Aslan" yazan bir İngilizce prompt modeli
    # Türkçeye kaydırıyor.
    yerel_harita = prompts.localize_chart(lang, natal)
    sun_sign = yerel_harita.get("sun_sign_local") or natal.get("sun_sign")
    moon_sign = yerel_harita.get("moon_sign_local") or natal.get("moon_sign")
    ascendant = yerel_harita.get("ascendant_local") or natal.get("ascendant")

    # Bugünün gökyüzünün haritaya değdiği noktalar (Revize R8). Efemeris
    # düşerse okuma düşmez — transitsiz devam edilir; eski davranış buydu.
    transits = ""
    if birth:
        try:
            vurus = chart_context.transit_facts(birth)["hits"]
            transits = chart_context.transit_lines(vurus, lang)
        except Exception as exc:
            logger.warning("Günlük okuma transitsiz: %s", exc)

    # Sorgu korpusun dilinde kurulur (chart_query gerekçesi): eski sabit
    # şablon TR korpusta İngilizce dolgu kelimeleriyle arıyordu.
    rag = retrieve_context(
        " ".join(filter(None, [
            chart_query.topic_seed("timing", lang),
            chart_query.topic_seed("temperament", lang),
            f"{sun_sign or ''} {moon_sign or ''}".strip(),
            transits,
        ])),
        lang=lang,
    )
    # Kullanıcı hafızası: günlük okumayı gerçekten kişisel yapan şey natal
    # harita değil (o herkes için sabit), zamanla biriken bu bağlam.
    memory = memory_service.memory_context(user_id, max_chars=400)

    retros = ", ".join(sky.get("retrogrades", [])) or "-"
    aspects = "; ".join(
        f"{a['p1']}-{a['p2']} {a['aspect']}" for a in sky.get("aspects", [])[:5]
    )
    moon = prompts.localize_moon_phase(lang, sky.get("moon_phase"))

    prompt = p.DAILY.format(
        sun_sign=sun_sign, moon_sign=moon_sign,
        ascendant=ascendant, today=today,
        moon_name=moon.get("name"), moon_emoji=moon.get("emoji"),
        illumination=moon.get("illumination"), retros=retros, aspects=aspects,
        transits=transits or "-",
        rag=rag, memory=_memory_block(memory, lang),
    )
    fallback = p.DAILY_FALLBACK.format(
        moon_name=moon.get("name") or "-",
        sun_sign=sun_sign or "-",
        ascendant=ascendant or "-",
    )
    return _cached_generate(cache_key, prompt, fallback, lang=lang,
                            owner_uid=user_id)


#: Dönem -> önbellek TTL'i. Anahtar tarih kovası içerdiği için TTL'in tek
#: görevi eski dosyaların diskte birikmesini önlemek; kova süresiyle hizalıdır.
_HOROSCOPE_TTL = {
    "daily": 24 * 3600,
    "weekly": 7 * 24 * 3600,
    "monthly": 31 * 24 * 3600,
}

def _horoscope_bucket(period: str, today: dt.date) -> str:
    """Önbellek tarih kovası: günlük YYYY-MM-DD, haftalık ISO yıl-hafta, aylık YYYY-MM."""
    if period == "weekly":
        iso = today.isocalendar()
        return f"{iso.year}-W{iso.week:02d}"
    if period == "monthly":
        return today.strftime("%Y-%m")
    return today.isoformat()


def horoscope_cache_key(sign: str, period: str, bucket: str, lang: str) -> str:
    """Burç yorumu önbellek anahtarı — kullanıcıdan bağımsız, dile bağlı.

    Dil anahtara girmek zorunda: girmezse İngilizce kullanıcı, aynı burç ve
    dönem için daha önce Türkçe üretilmiş yorumu görür.
    """
    return f"horoscope-{sign}-{period}-{bucket}-{lang}"


def horoscope_reading(sign: str, period: str, sky: dict[str, Any],
                      lang: str | None = None) -> dict[str, Any]:
    """Burç bazlı günlük/haftalık/aylık yorum.

    Kullanıcıdan BAĞIMSIZ önbelleklenir: anahtar (burç, dönem, tarih kovası,
    dil). Böylece dil x burç x dönem başına LLM'e en fazla 1 kez gidilir;
    sonraki tüm kullanıcılar aynı dönem içinde önbellekten okur.
    """
    lang = lang if lang in i18n.SUPPORTED else i18n.DEFAULT
    p = prompts.get(lang)
    today = dt.date.today()
    bucket = _horoscope_bucket(period, today)
    cache_key = horoscope_cache_key(sign, period, bucket, lang)

    # Önbellek isabeti en sık yoldur (dil x burç x dönem başına tek üretim,
    # geri kalan tüm istekler isabet). Bu yüzden prompt kurulmadan ÖNCE
    # bakılır: aksi halde her istekte RAG araması (ve embedding API çağrısı)
    # boşuna yapılırdı.
    cached = cache.get(cache_key)
    if cached is not None:
        return {"text": cached, "cached": True, "generated_for": bucket}

    sign_name = p.SIGN_NAMES.get(sign, sign)
    period_name = p.PERIOD_NAMES.get(period, p.PERIOD_NAMES["daily"])
    length = p.PERIOD_LENGTHS.get(period, p.PERIOD_LENGTHS["daily"])

    retros = ", ".join(sky.get("retrogrades", [])) or "-"
    aspects = "; ".join(
        f"{a['p1']}-{a['p2']} {a['aspect']}" for a in sky.get("aspects", [])[:5]
    ) or "-"
    moon = prompts.localize_moon_phase(lang, sky.get("moon_phase"))
    # Mizaç tohumu + yerel burç adı (Revize R8): eski sabit şablon TR
    # korpusta "sign temperament planet transit" diye İngilizce arıyordu.
    rag = retrieve_context(
        f"{chart_query.topic_seed('temperament', lang)} {sign_name}",
        lang=lang)

    prompt = p.HOROSCOPE.format(
        sign=sign_name, period=period_name, period_upper=period_name.upper(),
        length=length, today=today.isoformat(),
        moon_name=moon.get("name"), moon_emoji=moon.get("emoji"),
        illumination=moon.get("illumination"), retros=retros, aspects=aspects,
        rag=rag,
    )
    fallback = p.HOROSCOPE_FALLBACK.format(
        sign=sign_name, period=period_name,
        moon_name=moon.get("name") or "-",
    )
    result = _cached_generate(
        cache_key, prompt, fallback,
        ttl_seconds=_HOROSCOPE_TTL.get(period, 24 * 3600), lang=lang,
    )
    result["generated_for"] = bucket
    return result


def dyad_cache_key(uid_a: str, uid_b: str, today: dt.date) -> str:
    """İkili okuma önbellek anahtarı — çiftin sırasından bağımsız.

    İki arkadaş aynı günü aynı metinle görmeli: hem tek üretim yapılır hem de
    aralarında konuşulabilecek ortak bir şey oluşur.
    """
    first, second = sorted((uid_a, uid_b))
    return f"dyad-{first}-{second}-{today.isoformat()}"


def dyad_reading(uid_a: str, uid_b: str, name_a: str, name_b: str,
                 synastry: dict[str, Any], sky: dict[str, Any],
                 lang: str | None = None,
                 spend: Callable[[], None] | None = None,
                 refund: Callable[[], None] | None = None) -> dict[str, Any]:
    """İki arkadaş için GÜNLÜK ikili dinamik okuması.

    Kalıcı bir uyum skoru üretilmez. Gerekçe iki katlı: skor ölçüm değil
    gelenektir (ürünün dürüstlük ilkesi), ve geri alınamaz bir damga gerçek
    ilişkilere zarar verir. Bunun yerine bugüne özgü, yarın değişebilecek bir
    dinamik anlatılır.
    """
    lang = lang if lang in i18n.SUPPORTED else i18n.DEFAULT
    p = prompts.get(lang)
    today = dt.date.today()
    cache_key = dyad_cache_key(uid_a, uid_b, today)

    cached = cache.get(cache_key)
    if cached is not None:
        return {"text": cached, "cached": True, "generated_for": today.isoformat()}

    yerel_sinastri = prompts.localize_synastry(lang, synastry)
    aspects = "\n".join(
        f"- {a['p1_local']} ({name_a}) {a['aspect_local']} {a['p2_local']} "
        f"({name_b}) orb {a['orbit']}°"
        for a in yerel_sinastri.get("aspects", [])[:6]
    ) or p.NO_ASPECTS

    moon = prompts.localize_moon_phase(lang, sky.get("moon_phase"))
    retros = ", ".join(sky.get("retrogrades", [])) or p.NONE_LABEL
    # İlişki + zamanlama tohumları isteğin dilinde (Revize R8).
    rag = retrieve_context(
        f"{chart_query.topic_seed('relationship', lang)} "
        f"{chart_query.topic_seed('timing', lang)}",
        lang=lang)

    prompt = p.DYAD.format(
        name_a=name_a, name_b=name_b, today=today.isoformat(),
        moon_name=moon.get("name"), moon_emoji=moon.get("emoji"),
        illumination=moon.get("illumination"), retros=retros,
        aspects=aspects, rag=rag,
    )
    fallback = p.DYAD_FALLBACK.format(
        name_a=name_a, name_b=name_b, moon_name=moon.get("name") or "-")
    # Okuma iki kişiye ait ama sahiplik tek alan; isteyen taraf yazılır.
    # Zaten 24 saatlik ömrü var, kalan taraf için de kısa sürede düşer.
    result = _cached_generate(cache_key, prompt, fallback,
                              ttl_seconds=24 * 3600, lang=lang,
                              owner_uid=uid_a, spend=spend, refund=refund)
    result["generated_for"] = today.isoformat()
    return result


def natal_report(user_id: str, natal: dict[str, Any],
                 lang: str | None = None,
                 spend: Callable[[], None] | None = None,
                 refund: Callable[[], None] | None = None) -> dict[str, Any]:
    """Derinlemesine doğum haritası raporu (kullanıcı başına bir kez, 30 gün önbellek)."""
    lang = lang if lang in i18n.SUPPORTED else i18n.DEFAULT
    p = prompts.get(lang)
    cache_key = (f"natal-report-{user_id}-{natal.get('sun_sign')}"
                 f"-{natal.get('ascendant')}-{lang}")

    # İsabette embedding çağrısını atla (bkz. daily_reading'deki gerekçe).
    cached = cache.get(cache_key)
    if cached is not None:
        return {"text": cached, "cached": True}

    # Harita adları isteğin diline çevrilir: koşulsuz `_tr` seçmek İngilizce
    # prompt'a Türkçe gezegen ve burç adları sokuyordu.
    yerel = prompts.localize_chart(lang, natal)
    sun_sign = yerel.get("sun_sign_local") or natal.get("sun_sign")
    moon_sign = yerel.get("moon_sign_local") or natal.get("moon_sign")
    ascendant = yerel.get("ascendant_local") or natal.get("ascendant")

    points = "\n".join(
        f"- {pt['name_local']}: {pt['sign_local']} {pt['position']}° "
        f"({p.HOUSE_LABEL} {pt.get('house') or '?'}"
        f"{', ' + p.RETROGRADE_LABEL if pt.get('retrograde') else ''})"
        for pt in yerel.get("points", [])[:12]
    )
    aspects = "\n".join(
        f"- {a['p1_local']} {a['aspect_local']} {a['p2_local']} (orb {a['orbit']}°)"
        for a in yerel.get("aspects", [])[:10]
    )
    # Sorgu haritadan ve isteğin dilinde (Revize R8): burçlar + en sıkı açı.
    # Eski sabit şablon TR korpusta İngilizce dolgu kelimeleriyle arıyordu.
    en_siki = next(iter(yerel.get("aspects", [])), None)
    rag = retrieve_context(
        " ".join(filter(None, [
            chart_query.topic_seed("temperament", lang),
            chart_query.topic_seed("self", lang),
            f"{sun_sign or ''} {moon_sign or ''} {ascendant or ''}".strip(),
            (f"{en_siki['p1_local']} {en_siki['aspect_local']} "
             f"{en_siki['p2_local']}") if en_siki else "",
        ])),
        lang=lang,
    )

    prompt = p.NATAL.format(
        sun_sign=sun_sign, moon_sign=moon_sign,
        ascendant=ascendant, points=points, aspects=aspects, rag=rag,
    )
    fallback = p.NATAL_FALLBACK.format(
        sun_sign=sun_sign, moon_sign=moon_sign, ascendant=ascendant,
    )
    return _cached_generate(cache_key, prompt, fallback,
                            ttl_seconds=30 * 24 * 3600, lang=lang,
                            owner_uid=user_id, spend=spend, refund=refund)


def firasa_report(user_id: str, ratios: dict[str, Any],
                  chart: str = "", lang: str | None = None,
                  spend: Callable[[], None] | None = None,
                  refund: Callable[[], None] | None = None) -> dict[str, Any]:
    """Yüz ORANLARINDAN firaset okuması.

    Bu fonksiyon eski `face_report`'un yerini aldı. Eskisinin üç sorunu vardı
    ve üçü de bu projede başka yerlerde kapatılan kusur sınıflarındandı:

    * **Sunucu görüntü alıyordu.** Artık almıyor: tespit kullanıcının
      cihazında yapılıyor, buraya yalnızca oranlar geliyor.
    * **Prompt Türkçeye sabitliydi** (`lang` parametresi yoktu), yani
      İngilizce kullanıcı Türkçe kurallarla üretilmiş metin alıyordu.
    * **Yağcılık talimatı taşıyordu:** "Yorum pozitif psikoloji çerçevesinde
      olsun: her özellik güç + gelişim alanı." Bu, ürünün "pohpohlama yok"
      ilkesinin tam tersi. Yerini geleneğin kendi sınırı aldı: tek belirti
      hüküm vermez, belirti kader değildir, amaç ayıklamak değil dengelemek.

    Ayrıca eskisi tahmini yaş ve duygu da prompt'a koyuyordu; ikisi de
    biyometrik çıkarım ve ikisi de artık üretilmiyor.
    """
    p = prompts.get(lang)

    # Önbellek anahtarı oranların kendisiyle: aynı yüz aynı okumayı alır,
    # her açılışta yeni bir LLM çağrısı yapılmaz.
    ozet = json.dumps(
        {k: ratios.get(k) for k in sorted(ratios)}, sort_keys=True)
    cache_key = (f"firasa-{user_id}-{lang}-"
                 f"{hashlib.sha256(ozet.encode()).hexdigest()[:16]}")

    # İsabette embedding çağrısını atla (bkz. daily_reading'deki gerekçe).
    cached = cache.get(cache_key)
    if cached is not None:
        return {"text": cached, "cached": True}

    belirtiler = firasa_service.prompt_block(ratios, lang)
    rag = retrieve_context(
        p.FIRASA_RAG_QUERY, top_k=3, lang=lang)

    prompt = p.FIRASA.format(signs=belirtiler, chart=chart or "—", rag=rag)
    return _cached_generate(cache_key, prompt, p.FIRASA_FALLBACK,
                            ttl_seconds=7 * 24 * 3600,
                            lang=lang, owner_uid=user_id,
                            spend=spend, refund=refund)


def bazi_report(user_id: str, bazi: dict[str, Any],
                lang: str | None = None,
                spend: Callable[[], None] | None = None,
                refund: Callable[[], None] | None = None) -> dict[str, Any]:
    """BaZi haritasından kader analizi raporu."""
    lang = lang if lang in i18n.SUPPORTED else i18n.DEFAULT
    p = prompts.get(lang)
    cache_key = f"bazi-report-{user_id}-{bazi['pillars']['day']['label']}-{lang}"

    # İsabette embedding çağrısını atla (bkz. daily_reading'deki gerekçe).
    cached = cache.get(cache_key)
    if cached is not None:
        return {"text": cached, "cached": True}

    # Element, hayvan ve On Tanri adlari hesap motorunda anahtar olarak
    # duruyor; prompt'a girmeden once istegin diline cevrilir.
    bazi = prompts.localize_bazi(lang, bazi)

    pillars = " | ".join(f"{k}: {v['label']}" for k, v in bazi["pillars"].items())
    luck = "; ".join(
        f"{lp['from_age']}-{lp['to_age']}: {lp['label']} ({lp['ten_god']['name']})"
        for lp in bazi.get("luck_pillars", [])[:4]
    )
    # Mizaç tohumu + yerelleştirilmiş element adları (Revize R8). Korpus
    # BaZi metni taşımıyor; en yakın gerçek karşılık dört element/mizaç
    # bölümleri, sorgu da oraya yönelir. "Day Master" gibi İngilizce
    # terimler TR korpusta hiçbir şeye benzemiyordu.
    rag = retrieve_context(
        " ".join(filter(None, [
            chart_query.topic_seed("temperament", lang),
            str(bazi["day_master"].get("element") or ""),
            str(bazi.get("dominant_element") or ""),
        ])),
        lang=lang,
    )

    prompt = p.BAZI.format(
        pillars=pillars, day_master=bazi["day_master"]["description"],
        zodiac_animal=bazi["zodiac_animal"],
        elements=bazi["element_distribution"], dominant=bazi["dominant_element"],
        missing=bazi.get("missing_elements") or p.NONE_LABEL,
        ten_year=bazi["ten_gods"]["year"]["name"],
        ten_month=bazi["ten_gods"]["month"]["name"],
        ten_hour=bazi["ten_gods"]["hour"]["name"],
        luck=luck, rag=rag,
    )
    fallback = p.BAZI_FALLBACK.format(
        element=bazi["day_master"]["element"],
        polarity=bazi["day_master"]["polarity"],
        dominant=bazi["dominant_element"],
    )
    return _cached_generate(cache_key, prompt, fallback,
                            ttl_seconds=30 * 24 * 3600, lang=lang,
                            owner_uid=user_id, spend=spend, refund=refund)


def iching_reading(user_id: str, cast: dict[str, Any],
                   lang: str | None = None,
                   spend: Callable[[], None] | None = None,
                   refund: Callable[[], None] | None = None) -> dict[str, Any]:
    """I Ching çekimini kullanıcının sorusuna bağlayan yorum."""
    lang = lang if lang in i18n.SUPPORTED else i18n.DEFAULT
    p = prompts.get(lang)
    # Heksagram metinleri veri katmanında iki dilde tutuluyor; burada isteğin
    # diline indirgenir (name_local / judgment / image).
    yerel = prompts.localize_iching(lang, cast)
    primary = yerel["primary"]
    cache_key = (f"iching-{user_id}-{primary['number']}"
                 f"-{cast.get('question', '')[:48]}"
                 f"-{'-'.join(map(str, cast.get('moving_lines', [])))}-{lang}")

    # İsabette embedding çağrısını atla (bkz. daily_reading'deki gerekçe).
    cached = cache.get(cache_key)
    if cached is not None:
        return {"text": cached, "cached": True}

    transformed_text = ""
    if yerel.get("transformed"):
        t = yerel["transformed"]
        transformed_text = p.ICHING_TRANSFORMED.format(
            lines=cast["moving_lines"], number=t["number"],
            name_tr=t["name_local"], name=t["name"], judgment=t["judgment"],
        )

    rag = retrieve_context(
        f"I Ching hexagram {primary['name']} change synchronicity", lang=lang)

    prompt = p.ICHING.format(
        question=cast.get("question"), method=cast.get("method"),
        number=primary["number"], name_tr=primary["name_local"],
        name=primary["name"], name_cn=primary["name_cn"],
        unicode=primary["unicode"], judgment=primary["judgment"],
        image=primary["image"],
        lower=primary["lower_trigram"]["name"],
        upper=primary["upper_trigram"]["name"],
        transformed=transformed_text, rag=rag,
    )
    fallback = (
        f"#{primary['number']} {primary['name_local']} {primary['unicode']}: "
        f"{primary['judgment']}"
    )
    return _cached_generate(cache_key, prompt, fallback, ttl_seconds=3600,
                            lang=lang, owner_uid=user_id,
                            spend=spend, refund=refund)


def synastry_report(user_id: str, synastry: dict[str, Any],
                    lang: str | None = None,
                    spend: Callable[[], None] | None = None,
                    refund: Callable[[], None] | None = None) -> dict[str, Any]:
    """İki kişi arasındaki kozmik uyum raporu.

    Sinastri skoru hesaplanıyor ama prompt'a GİRMİYOR ve rapora yazdırılmıyor:
    ilişkiyi tek sayıya indirgemek ürünün dürüstlük ilkesiyle çelişiyor ve
    ikili dinamikte de aynı gerekçeyle yasak.
    """
    lang = lang if lang in i18n.SUPPORTED else i18n.DEFAULT
    p = prompts.get(lang)
    yerel = prompts.localize_synastry(lang, synastry)
    p1, p2 = yerel["person1"], yerel["person2"]
    cache_key = f"synastry-{user_id}-{p1['name']}-{p2['name']}-{lang}"

    # İsabette embedding çağrısını atla (bkz. daily_reading'deki gerekçe).
    cached = cache.get(cache_key)
    if cached is not None:
        return {"text": cached, "cached": True}

    aspects = "\n".join(
        f"- {a['p1_local']} ({p1['name']}) {a['aspect_local']} {a['p2_local']} "
        f"({p2['name']}) orb {a['orbit']}°"
        for a in yerel.get("aspects", [])[:8]
    ) or p.NO_ASPECTS
    # Sorgu isteğin dilinde ve İKİ haritadan (Revize R8): ilişki tohumu +
    # iki Güneş + en sıkı sinastri açısı.
    en_siki = next(iter(yerel.get("aspects", [])), None)
    rag = retrieve_context(
        " ".join(filter(None, [
            chart_query.topic_seed("relationship", lang),
            f"{p1['sun']['sign_local']} {p2['sun']['sign_local']}",
            (f"{en_siki['p1_local']} {en_siki['aspect_local']} "
             f"{en_siki['p2_local']}") if en_siki else "",
        ])),
        lang=lang)

    prompt = p.SYNASTRY.format(
        name1=p1["name"], sun1=p1["sun"]["sign_local"],
        moon1=p1["moon"]["sign_local"],
        name2=p2["name"], sun2=p2["sun"]["sign_local"],
        moon2=p2["moon"]["sign_local"],
        aspects=aspects, rag=rag,
    )
    fallback = p.SYNASTRY_FALLBACK.format(
        name1=p1["name"], sun1=p1["sun"]["sign_local"],
        name2=p2["name"], sun2=p2["sun"]["sign_local"],
    )
    return _cached_generate(cache_key, prompt, fallback,
                            ttl_seconds=7 * 24 * 3600, lang=lang,
                            owner_uid=user_id, spend=spend, refund=refund)
