"""I Ching (Değişimler Kitabı) — 64 heksagram, gerçek olasılık simülasyonu.

İki geleneksel yöntem birebir simüle edilir (donanımsal entropi: `secrets`):

- Madeni para (üç para): 6 (eski yin) %12.5, 7 (genç yang) %37.5,
  8 (genç yin) %37.5, 9 (eski yang) %12.5
- Civanperçemi (yarrow): 6 -> 1/16, 7 -> 5/16, 8 -> 7/16, 9 -> 3/16

Eski (hareketli) çizgiler tersine döner ve "dönüşen heksagram" oluşur.
"""
from __future__ import annotations

import json
import re
import secrets
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "hexagrams.json"

#: Hesap sürümü (Revize İ0): çekimin ürettiği yapı değiştiğinde artar ve
#: rapor önbellek anahtarına girer — BaZi'deki calc_version disiplininin
#: birebir aynısı. Eski yorumlar kendiliğinden düşer, migrasyon gerekmez.
#: v3: nükleer heksagram + çekim günü bağlamı (İ2). v4: Liu Yao — najia,
#: saray, altı akraba, shi/ying, boşluk/çarpışma (İ3). v5: anlamsız-soru
#: kuralı prompt'a girdi (R10) — eski önbellek yeni kuralı bilmez.
ICHING_CALC_VERSION = "5"

Method = Literal["coins", "yarrow"]

#: Soru kutusuna niyet yerine yazılan tipik doldurmalar. Liste kasıtlı
#: kısa: amaç anlam denetimi değil (o imkânsız), günde tek çekim hakkının
#: "merhaba" ile harcanmasını engellemek. Türkçe kırpık biçimler de var
#: çünkü karşılaştırma casefold'la yapılır ve noktasız-I varyantları iki
#: ayrı dizgi üretir (bkz. hafıza: Türkçe metin tuzakları).
_DOLGU_KELIMELER = frozenset({
    "merhaba", "selam", "selamlar", "hello", "hi", "hey", "naber",
    "nasılsın", "nasilsin", "iyi", "misin", "test", "deneme", "asdf",
    "qwerty", "abc", "ok", "tamam", "evet", "hayır", "hayir",
})


def question_is_meaningful(question: str) -> bool:
    """Soru gerçek bir niyet taşıyor mu — kaba ama ucuz bir kapı (R10).

    Kural: dolgu kelimeler ayıklandıktan sonra EN AZ İKİ kelime kalmalı.
    "merhaba" ve "selam naber" çevrilir; "iş değiştirmeli miyim" geçer.
    Tek kelimelik gerçek sorular da ("evlilik?") bilerek çevrilir —
    kullanıcıdan istenen şey niyetini bir cümleye dökmesi.
    """
    # casefold("İ") = "i" + birleşik nokta (U+0307); nokta atılmazsa "İYİ"
    # dolgu listesindeki "iyi" ile eşleşmez (Türkçe noktalı-I tuzağı).
    kelimeler = re.split(r"[^\w']+",
                         question.casefold().replace("\u0307", ""))
    anlamli = [k for k in kelimeler if k and k not in _DOLGU_KELIMELER]
    return len(anlamli) >= 2


@lru_cache(maxsize=1)
def _load() -> dict[str, Any]:
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _lines_index() -> dict[tuple[int, ...], dict[str, Any]]:
    data = _load()
    trigrams = data["trigrams"]
    index = {}
    for hexagram in data["hexagrams"]:
        lower = trigrams[hexagram["lower"]]["lines"]
        upper = trigrams[hexagram["upper"]]["lines"]
        index[tuple(lower + upper)] = hexagram
    return index


def _cast_line_coins() -> int:
    # Uc madeni para: yazi=3, tura=2
    return sum(2 + secrets.randbelow(2) for _ in range(3))


def _cast_line_yarrow() -> int:
    # Yarrow stalk olasılık dağılımı: 6:1, 7:5, 8:7, 9:3 (16'da)
    r = secrets.randbelow(16)
    if r < 1:
        return 6
    if r < 6:
        return 7
    if r < 13:
        return 8
    return 9


def _hexagram_info(lines: list[int]) -> dict[str, Any]:
    data = _load()
    hexagram = _lines_index()[tuple(lines)]
    trigrams = data["trigrams"]
    lower, upper = trigrams[hexagram["lower"]], trigrams[hexagram["upper"]]
    # Her dil ayri alanda doner; secim yaniti ureten katmanda yapilir
    # (services/prompts.localize_iching). Burada "judgment" gibi tek bir
    # alanda Turkce metin dondurmek, Ingilizce prompt'a Turkce kaynak
    # besliyordu ve yorumun dilini bozuyordu.
    return {
        "number": hexagram["number"],
        "name": hexagram["pinyin"],
        "name_cn": hexagram["cn"],
        "name_en": hexagram["name_en"],
        "name_tr": hexagram["name_tr"],
        "judgment_tr": hexagram["judgment_tr"],
        "judgment_en": hexagram["judgment_en"],
        "image_tr": hexagram["image_tr"],
        "image_en": hexagram["image_en"],
        # 384 yao pasajı (İ1): alttan üste 6 çizgi metni + Qian/Kun'da
        # "tüm çizgiler" pasajı. Dile indirgeme localize katmanında.
        "lines_tr": hexagram.get("lines_tr"),
        "lines_en": hexagram.get("lines_en"),
        "all_lines_tr": hexagram.get("all_lines_tr"),
        "all_lines_en": hexagram.get("all_lines_en"),
        "lower_trigram": _trigram_info(lower),
        "upper_trigram": _trigram_info(upper),
        "unicode": chr(0x4DC0 + hexagram["number"] - 1),
    }


def _trigram_info(trigram: dict[str, Any]) -> dict[str, Any]:
    """Trigram: iki dilde ad + dilden bagimsiz anahtarlar.

    family/attribute/direction İ1'de eklendi (Shuo Gua); adlar prompts
    katmanındaki TRIGRAM_*_NAMES tablolarından çözülür.
    """
    return {
        "name_tr": trigram["name_tr"],
        "name_en": trigram["name_en"],
        "symbol": trigram["symbol"],
        "element": trigram["element"],
        "family": trigram.get("family"),
        "attribute": trigram.get("attribute"),
        "direction": trigram.get("direction"),
    }


def cast_iching(question: str, method: Method = "coins") -> dict[str, Any]:
    cast_fn = _cast_line_coins if method == "coins" else _cast_line_yarrow
    values = [cast_fn() for _ in range(6)]  # alttan üste

    primary_lines = [1 if v in (7, 9) else 0 for v in values]
    moving = [i + 1 for i, v in enumerate(values) if v in (6, 9)]

    result: dict[str, Any] = {
        "question": question,
        "method": method,
        "line_values": values,
        "lines": primary_lines,
        "moving_lines": moving,
        "primary": _hexagram_info(primary_lines),
        # Nükleer heksagram (hu gua, İ2): 2-3-4. çizgiler alt, 3-4-5.
        # çizgiler üst trigramı kurar — durumun "çekirdeği". Qian ve Kun
        # kendilerine döner; bu bir kusur değil, klasik sabit noktadır.
        "nuclear": _hexagram_info(
            primary_lines[1:4] + primary_lines[2:5]),
    }

    # Liu Yao (İ3): najia + saray + altı akraba çekimin KENDİSİNE aittir,
    # tarihe değil — burada temel hâliyle iliştirilir; boşluk/çarpışma gün
    # bağlamıyla enrich_cast'te tazelenir. İçe aktarma fonksiyon içinde:
    # liuyao_service trigram desenlerini bu modülden okuyor (döngü kırıcı).
    from services import liuyao_service
    result["liu_yao"] = liuyao_service.analyze(primary_lines)

    if moving:
        transformed = [
            (1 - line) if (i + 1) in moving else line
            for i, line in enumerate(primary_lines)
        ]
        result["transformed"] = _hexagram_info(transformed)

    return result


def enrich_cast(cast: dict[str, Any], *,
                day_pillar: dict[str, Any] | None = None,
                month_pillar: dict[str, Any] | None = None,
                day_master_element: str | None = None,
                basis: str = "utc") -> dict[str, Any]:
    """Çekime GÜN BAĞLAMI iliştirir (İ2) — saf, girdisiz de çalışır.

    Klasik danışma çekimi, çekildiği GÜNÜN içinde okunur (Wen Wang Gua
    geleneğinin zemini): günün ve ayın sütunları ile trigram elementlerinin
    danışanın Day Master'ına ilişkisi yorumu kişiselleştirir. Bağlamsız
    çağrı (test, profilsiz kullanıcı) çekimi olduğu gibi döndürür —
    kişiselleştirme İDDİASI da prompt kurallarıyla o durumda yasak.

    ``basis``: günün hangi saat diliminden alındığının beyanı
    ("profile_tz" | "utc") — gün sınırında dürüstlük.
    """
    if not (day_pillar or month_pillar or day_master_element):
        return cast

    context: dict[str, Any] = {"basis": basis}
    if day_pillar:
        context["day_pillar"] = day_pillar
        # Gün döngüsü biliniyorsa Liu Yao boşluk/çarpışma işaretleriyle
        # yeniden kurulur (İ3) — analyze saf ve ucuz.
        if day_pillar.get("cycle") is not None and cast.get("lines"):
            from services import liuyao_service
            cast = {**cast,
                    "liu_yao": liuyao_service.analyze(
                        cast["lines"], day_cycle=day_pillar["cycle"])}
    if month_pillar:
        context["month_pillar"] = month_pillar
    if day_master_element:
        from services.bazi_service import _element_relation
        context["day_master_element"] = day_master_element
        context["trigram_relations"] = {
            konum: _element_relation(
                day_master_element,
                cast["primary"][f"{konum}_trigram"]["element"])
            for konum in ("lower", "upper")
        }
    return {**cast, "context": context}


def get_hexagram(number: int) -> dict[str, Any]:
    for hexagram in _load()["hexagrams"]:
        if hexagram["number"] == number:
            trigrams = _load()["trigrams"]
            lines = trigrams[hexagram["lower"]]["lines"] + trigrams[hexagram["upper"]]["lines"]
            return _hexagram_info(lines)
    raise ValueError(f"Heksagram bulunamadı: {number}")
