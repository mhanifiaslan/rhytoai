"""Liu Yao (Wen Wang Gua) — najia, saray, altı akraba, shi/ying (İ3).

Kamu malı Jing Fang (京房, MÖ 1. yy) geleneğinin çekirdeği: heksagramın
her çizgisine bir gövde+dal atanır (najia), heksagram sekiz saraydan
birine yerleşir, çizgiler saray elementine göre "altı akraba"ya ayrılır
ve çekim gününün dalıyla boşluk/çarpışma ilişkisi kurulur. Tamamı
deterministik ve tablo-denetlenebilirdir; LLM yalnız YORUMLAR.

## Tasarım

* **Saray ataması KURALDAN üretilir, tablodan değil.** Jing Fang dizisi:
  saf saray → 1. çizgi döner → 1-2 → 1-2-3 → 1-2-3-4 → 1-2-3-5. derken
  1..5 → "gezgin ruh" (you hun: 5'lik hâlden 4. çizgi geri) → "dönen ruh"
  (gui hun: gezgin ruhtan 1-2-3 geri). 64 atama bu kuraldan çıkar; test,
  Qian sarayının klasik tam zincirini (1→44→33→12→20→23→35→14) dondurur.
* **Najia tablosu** transkripsiyon hatasına açık tek yer — altın vektör:
  heksagram 1 = JiaZi/JiaYin/JiaChen/RenWu/RenShen/RenXu, heksagram 2 =
  YiWei/YiSi/YiMao/GuiChou/GuiHai/GuiYou (klasik diziler, testte kilitli).
* Çıktı ANAHTAR taşır (sibling/wealth...), ad prompts katmanında çözülür
  (LIU_QIN_NAMES) — dil-izolasyon disiplini.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any

from services.bazi_service import BRANCHES, STEMS, _element_relation
from services.bazi_stars import void_branches

#: Saray trigramı → saray elementi (klasik eşleme).
PALACE_ELEMENT = {
    "qian": "metal", "dui": "metal",
    "li": "fire",
    "zhen": "wood", "xun": "wood",
    "kan": "water",
    "gen": "earth", "kun": "earth",
}

#: Saray içi konum → shi (özne) çizgisi. Ying (karşılık) = shi ± 3.
SHI_SEQUENCE = (6, 1, 2, 3, 4, 5, 4, 3)

#: Najia — trigram × (iç/dış konum) → (gövde indeksi, üç dal indeksi).
#: Yang trigramlar dalları yükselen sırayla, yin trigramlar alçalan
#: sırayla alır. İndeksler bazi_service.STEMS/BRANCHES'e işaret eder.
#: Kaynak: Jing Fang najia şeması; hex 1/2 altın vektörleriyle kilitli.
NAJIA: dict[str, dict[str, tuple[int, tuple[int, int, int]]]] = {
    "qian": {"inner": (0, (0, 2, 4)), "outer": (8, (6, 8, 10))},
    "kun": {"inner": (1, (7, 5, 3)), "outer": (9, (1, 11, 9))},
    "zhen": {"inner": (6, (0, 2, 4)), "outer": (6, (6, 8, 10))},
    "kan": {"inner": (4, (2, 4, 6)), "outer": (4, (8, 10, 0))},
    "gen": {"inner": (2, (4, 6, 8)), "outer": (2, (10, 0, 2))},
    "xun": {"inner": (7, (1, 11, 9)), "outer": (7, (7, 5, 3))},
    "li": {"inner": (5, (3, 1, 11)), "outer": (5, (9, 7, 5))},
    "dui": {"inner": (3, (5, 3, 1)), "outer": (3, (11, 9, 7))},
}

#: Saray elementi ↔ çizgi dalının elementi → altı akraba anahtarı.
_RELATIVE_BY_RELATION = {
    "same": "sibling",          # 兄弟 — akran/rakip
    "i_produce": "offspring",   # 子孫 — saray onu üretir
    "produces_me": "parent",    # 父母 — o sarayı üretir
    "i_control": "wealth",      # 妻財 — saray onu yönetir
    "controls_me": "officer",   # 官鬼 — o sarayı yönetir
}


@lru_cache(maxsize=1)
def _trigram_lines() -> dict[str, tuple[int, ...]]:
    from services.iching_service import _load
    return {ad: tuple(t["lines"]) for ad, t in _load()["trigrams"].items()}


@lru_cache(maxsize=1)
def _lines_to_trigram() -> dict[tuple[int, ...], str]:
    return {cizgiler: ad for ad, cizgiler in _trigram_lines().items()}


def _cevir(lines: tuple[int, ...], hangi: int) -> tuple[int, ...]:
    """Verilen (0 tabanlı) çizgiyi ters çevirir."""
    return tuple((1 - v) if i == hangi else v for i, v in enumerate(lines))


@lru_cache(maxsize=1)
def _palace_index() -> dict[tuple[int, ...], tuple[str, int]]:
    """64 çizgi deseni → (saray, saray içi konum). Kuraldan üretilir."""
    indeks: dict[tuple[int, ...], tuple[str, int]] = {}
    for saray, trig in _trigram_lines().items():
        saf = trig + trig
        dizi = [saf]
        mevcut = saf
        for i in range(5):                     # konum 1..5: 1..i+1 döner
            mevcut = _cevir(mevcut, i)
            dizi.append(mevcut)
        gezgin = _cevir(dizi[5], 3)            # you hun: 4. çizgi geri
        donen = saf[:3] + gezgin[3:]           # gui hun: alt trigram saf
        dizi += [gezgin, donen]
        for konum, desen in enumerate(dizi):
            indeks[desen] = (saray, konum)
    assert len(indeks) == 64, "Saray üretim kuralı 64 benzersiz desen vermedi"
    return indeks


def analyze(lines: list[int],
            day_cycle: int | None = None) -> dict[str, Any]:
    """Heksagram çizgilerinden tam Liu Yao yapısı.

    ``day_cycle`` (çekim gününün 60'lık döngü indeksi,
    bazi_service.day_pillar_for_date verir) sağlanırsa boşluk (kong wang)
    ve gün dalıyla çarpışma (liu chong) da işaretlenir; sağlanmazsa o iki
    alan None kalır — bilinmeyen, yanlış bilinenden iyidir.
    """
    desen = tuple(lines)
    saray, konum = _palace_index()[desen]
    shi = SHI_SEQUENCE[konum]
    ying = shi - 3 if shi > 3 else shi + 3
    saray_elementi = PALACE_ELEMENT[saray]

    bos: tuple[int, int] | None = None
    gun_dal: int | None = None
    if day_cycle is not None:
        bos = void_branches(day_cycle)
        gun_dal = day_cycle % 12

    alt = _lines_to_trigram()[desen[:3]]
    ust = _lines_to_trigram()[desen[3:]]

    cizgiler = []
    for i in range(6):
        trig = alt if i < 3 else ust
        govde_idx, dallar = NAJIA[trig]["inner" if i < 3 else "outer"]
        dal_idx = dallar[i % 3]
        iliski = _element_relation(saray_elementi,
                                   BRANCHES[dal_idx]["element"])
        cizgiler.append({
            "position": i + 1,
            "stem": STEMS[govde_idx]["pinyin"],
            "branch": BRANCHES[dal_idx]["pinyin"],
            "branch_element": BRANCHES[dal_idx]["element"],
            "relative": _RELATIVE_BY_RELATION[iliski],
            "void": (dal_idx in bos) if bos is not None else None,
            "clash": ((dal_idx + 6) % 12 == gun_dal)
            if gun_dal is not None else None,
        })

    return {
        "palace": saray,
        "palace_element": saray_elementi,
        "shi": shi,
        "ying": ying,
        "lines": cizgiler,
    }
