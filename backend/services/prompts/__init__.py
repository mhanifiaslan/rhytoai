"""Dile göre prompt ve persona modülleri.

Prompt'lar dilden bağımsız bir şablona çevirilerin doldurulmasıyla üretilmiyor;
her dil kendi modülünde kendi metnini taşıyor. Gerekçe: bunlar arayüz etiketi
değil, karakter tanımı. Türkçedeki samimi "sen" dili İngilizceye birebir
çevrildiğinde ton bozulur — İngilizcede aynı sıcaklık farklı cümle yapısıyla
kurulur. Kelime kelime çeviri, personayı düzleştirir.

Kullanım:
    from services import prompts
    p = prompts.get("en")
    p.SYSTEM_INSTRUCTION
"""
from __future__ import annotations

from types import ModuleType

from core import i18n
from services.prompts import en as _en
from services.prompts import tr as _tr

_MODULES: dict[str, ModuleType] = {"tr": _tr, "en": _en}


def get(lang: str | None) -> ModuleType:
    """Dilin prompt modülü; tanınmayan dil varsayılana düşer."""
    return _MODULES.get(lang or "", _MODULES[i18n.DEFAULT])


def sign_name(lang: str | None, sign_key: str) -> str:
    """Burç anahtarının (``leo``) o dildeki adı."""
    return get(lang).SIGN_NAMES.get(sign_key, sign_key)


def moon_phase_name(lang: str | None, phase_key: str | None) -> str:
    """Ay evresi anahtarının (``full_moon``) o dildeki adı."""
    if not phase_key:
        return ""
    return get(lang).MOON_PHASES.get(phase_key, phase_key)


def localize_moon_phase(lang: str | None, moon: dict | None) -> dict:
    """Gökyüzü sözlüğündeki ay evresine dile göre ``name`` alanı ekler.

    Hesap paylaşımlı önbellekten geldiği için evre yalnızca anahtar taşır;
    ada çeviri isteğin dilinde, yanıt üretilirken eklenir.
    """
    if not moon:
        return {}
    key = moon.get("key")
    if not key:
        # Anahtarsız gökyüzü (eski önbellek kaydı ya da test verisi):
        # elimizdeki ``name`` neyse onunla devam et, boş metin döndürme.
        return dict(moon)
    return {**moon, "name": moon_phase_name(lang, key)}


#: kerykeion burç kodu -> prompt modüllerindeki burç anahtarı.
_SIGN_CODE_TO_KEY = {
    "Ari": "aries", "Tau": "taurus", "Gem": "gemini", "Can": "cancer",
    "Leo": "leo", "Vir": "virgo", "Lib": "libra", "Sco": "scorpio",
    "Sag": "sagittarius", "Cap": "capricorn", "Aqu": "aquarius",
    "Pis": "pisces",
}


def sign_key_from_code(code: str | None) -> str | None:
    """kerykeion burç kodunun (``Leo``) dilden bağımsız anahtarı (``leo``).

    Element/nitelik gibi türetilmiş sayımlar burç ADINDAN değil anahtarından
    yapılmalı; aksi halde hesap dile bağımlı hale gelir.
    """
    return _SIGN_CODE_TO_KEY.get(code) if code else None


def sign_name_from_code(lang: str | None, code: str | None) -> str:
    """kerykeion burç kodunun (``Leo``, ``Ari``) o dildeki adı."""
    if not code:
        return ""
    anahtar = _SIGN_CODE_TO_KEY.get(code)
    return sign_name(lang, anahtar) if anahtar else code


def sign_from_point(lang: str | None, point: dict | None) -> str:
    """Bir nokta sözlüğündeki burcu isteğin dilinde döndürür.

    Önce kerykeion kodu (``sign``) denenir; yoksa elde ne varsa (``sign_tr``)
    olduğu gibi gösterilir. Kod bulunamadığında boş string dönmek, arayüzde
    burç alanını tamamen boşaltırdı.
    """
    if not point:
        return ""
    kod = point.get("sign")
    if kod and kod in _SIGN_CODE_TO_KEY:
        return sign_name_from_code(lang, kod)
    return point.get("sign_tr") or kod or ""


def planet_name(lang: str | None, key: str | None) -> str:
    """Gezegen anahtarının (``Saturn``) o dildeki adı."""
    if not key:
        return ""
    return get(lang).PLANET_NAMES.get(key, key)


def aspect_name(lang: str | None, key: str | None) -> str:
    """Açı anahtarının (``square``) o dildeki adı."""
    if not key:
        return ""
    return get(lang).ASPECT_NAMES.get(key, key)


def localize_bazi(lang: str | None, chart: dict | None) -> dict:
    """BaZi haritasındaki anahtarları isteğin diline çevirir.

    Hesap motoru (bazi_service) element, hayvan ve On Tanrı için **anahtar**
    döndürür; ad ve açıklama burada kurulur. Motorda Türkçe ad tutulsaydı
    İngilizce kullanıcı hem ekranda hem yorumda "Ahşap" görürdü.
    """
    if not chart:
        return {}
    p = get(lang)

    def element(key: str | None) -> str:
        return p.BAZI_ELEMENTS.get(key or "", key or "")

    def polarity(key: str | None) -> str:
        return p.POLARITY_NAMES.get(key or "", key or "")

    def sutun(pillar: dict | None) -> dict:
        if not pillar:
            return {}
        gövde = pillar.get("stem") or {}
        dal = pillar.get("branch") or {}
        return {
            **pillar,
            "stem": {**gövde,
                     "element": element(gövde.get("element")),
                     "polarity": polarity(gövde.get("polarity"))},
            "branch": {**dal,
                       "element": element(dal.get("element")),
                       "animal": p.BAZI_ANIMALS.get(dal.get("animal") or "",
                                                    dal.get("animal") or "")},
        }

    def tanri(god: dict | None) -> dict:
        if not god:
            return {}
        return {**god,
                "meaning": p.TEN_GOD_MEANINGS.get(god.get("meaning_key") or "",
                                                  god.get("meaning_key") or "")}

    day_master = chart.get("day_master") or {}
    çevrilmiş_dm = {
        **day_master,
        "element": element(day_master.get("element")),
        "polarity": polarity(day_master.get("polarity")),
    }
    if day_master:
        çevrilmiş_dm["description"] = p.DAY_MASTER_DESCRIPTION.format(
            polarity=çevrilmiş_dm["polarity"], element=çevrilmiş_dm["element"],
            cn=day_master.get("cn", ""), pinyin=day_master.get("pinyin", ""),
        )

    return {
        **chart,
        "gender": p.GENDER_NAMES.get(chart.get("gender") or "",
                                     chart.get("gender") or ""),
        "pillars": {ad: sutun(v)
                    for ad, v in (chart.get("pillars") or {}).items()},
        "day_master": çevrilmiş_dm,
        "ten_gods": {ad: tanri(v)
                     for ad, v in (chart.get("ten_gods") or {}).items()},
        "element_distribution": {
            element(k): v
            for k, v in (chart.get("element_distribution") or {}).items()},
        "dominant_element": element(chart.get("dominant_element")),
        "missing_elements": [element(e)
                             for e in (chart.get("missing_elements") or [])],
        "zodiac_animal": p.BAZI_ANIMALS.get(chart.get("zodiac_animal") or "",
                                            chart.get("zodiac_animal") or ""),
        "luck_pillars": [{**sutun(lp), "ten_god": tanri(lp.get("ten_god"))}
                         for lp in (chart.get("luck_pillars") or [])],
    }


def localize_iching(lang: str | None, cast: dict | None) -> dict:
    """I Ching çekilişindeki heksagram metinlerini isteğin diline indirger.

    Veri katmanı her dili ayrı alanda tutuyor (``judgment_tr`` /
    ``judgment_en``); burada tek bir ``judgment``/``image``/``name`` alanına
    düşürülür ki prompt şablonları dilden habersiz kalabilsin.
    """
    if not cast:
        return {}
    son_ek = "en" if (lang or DEFAULT) == "en" else "tr"
    p = get(lang)

    def trigram(t: dict | None) -> dict:
        if not t:
            return {}
        return {**t,
                "name": t.get(f"name_{son_ek}") or t.get("name_tr") or "",
                "element": p.BAZI_ELEMENTS.get(t.get("element") or "",
                                               t.get("element") or "")}

    def heksagram(h: dict | None) -> dict:
        if not h:
            return {}
        return {
            **h,
            "name_local": h.get(f"name_{son_ek}") or h.get("name_tr") or "",
            "judgment": h.get(f"judgment_{son_ek}") or h.get("judgment_tr") or "",
            "image": h.get(f"image_{son_ek}") or h.get("image_tr") or "",
            "lower_trigram": trigram(h.get("lower_trigram")),
            "upper_trigram": trigram(h.get("upper_trigram")),
        }

    sonuç = {**cast, "primary": heksagram(cast.get("primary"))}
    if cast.get("transformed"):
        sonuç["transformed"] = heksagram(cast["transformed"])
    return sonuç


def localize_chart(lang: str | None, chart: dict | None) -> dict:
    """Natal haritadaki nokta ve açı adlarını isteğin diline çevirir.

    astro_service her ikisini de döndürüyor (``name`` / ``name_tr``); rapor
    katmanı koşulsuz Türkçe olanı seçtiği için İngilizce prompt'a Türkçe
    gezegen ve burç adları giriyordu.
    """
    if not chart:
        return {}

    def nokta(pt: dict) -> dict:
        return {**pt,
                "name_local": planet_name(lang, pt.get("name")),
                "sign_local": sign_name_from_code(lang, pt.get("sign"))}

    def açı(a: dict) -> dict:
        return {**a,
                "p1_local": planet_name(lang, a.get("p1")),
                "p2_local": planet_name(lang, a.get("p2")),
                "aspect_local": aspect_name(lang, a.get("aspect"))}

    sonuç = {**chart,
             "points": [nokta(p) for p in (chart.get("points") or [])],
             "aspects": [açı(a) for a in (chart.get("aspects") or [])]}

    # ``sun_sign`` / ``moon_sign`` / ``ascendant`` alanlarına DOKUNULMAZ:
    # onboarding bu değerleri Firestore profiline yazıyor ve mobil tarafta
    # burç eşleştirmesi ("Kova ♒") bu biçime bağlı. Biçimi değiştirmek eski
    # profillerle yenileri uyumsuz hale getirirdi. Yerelleştirilmiş karşılık
    # ayrı bir alanda döner.
    for alan, kaynak in (("sun_sign_local", "sun"), ("moon_sign_local", "moon"),
                         ("ascendant_local", "asc")):
        kod = (chart.get(kaynak) or {}).get("sign")
        if kod:
            sonuç[alan] = sign_name_from_code(lang, kod)
    return sonuç


def localize_synastry(lang: str | None, synastry: dict | None) -> dict:
    """Sinastri çıktısındaki iki kişinin nokta adlarını ve açıları çevirir."""
    if not synastry:
        return {}

    def kişi(p: dict | None) -> dict:
        if not p:
            return {}
        çevrilmiş = dict(p)
        for alan in ("sun", "moon", "ascendant", "asc"):
            nokta = p.get(alan)
            if isinstance(nokta, dict):
                çevrilmiş[alan] = {**nokta,
                                   "sign_local": sign_from_point(lang, nokta)}
        return çevrilmiş

    return {
        **synastry,
        "person1": kişi(synastry.get("person1")),
        "person2": kişi(synastry.get("person2")),
        "aspects": [
            {**a,
             "p1_local": planet_name(lang, a.get("p1")),
             "p2_local": planet_name(lang, a.get("p2")),
             "aspect_local": aspect_name(lang, a.get("aspect"))}
            for a in (synastry.get("aspects") or [])
        ],
    }


def localize_sky(lang: str | None, sky: dict | None) -> dict:
    """Gökyüzü yükünü isteğin diline çevirir.

    Hesap dilden bağımsızdır ve paylaşımlı önbellekten servis edilir; bu
    yüzden retro listesi, açılar ve ay evresi anahtar taşır. Çeviri **yanıt
    üretilirken** yapılır — aksi halde önbelleği ilk dolduran dil herkese
    servis edilirdi (İngilizce kullanıcı "Satürn retro" görüyordu).
    """
    if not sky:
        return {}
    return {
        **sky,
        "moon_phase": localize_moon_phase(lang, sky.get("moon_phase")),
        "planets": [
            {**gezegen,
             "name_local": planet_name(lang, gezegen.get("name")),
             "sign_local": sign_name(lang, gezegen.get("sign"))}
            for gezegen in (sky.get("planets") or [])
        ],
        "retrogrades": [planet_name(lang, p)
                        for p in (sky.get("retrogrades") or [])],
        "aspects": [
            {**a,
             "p1": planet_name(lang, a.get("p1")),
             "p2": planet_name(lang, a.get("p2")),
             "aspect": aspect_name(lang, a.get("aspect"))}
            for a in (sky.get("aspects") or [])
        ],
    }
