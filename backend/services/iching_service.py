"""I Ching (Değişimler Kitabı) — 64 heksagram, gerçek olasılık simülasyonu.

İki geleneksel yöntem birebir simüle edilir (donanımsal entropi: `secrets`):

- Madeni para (üç para): 6 (eski yin) %12.5, 7 (genç yang) %37.5,
  8 (genç yin) %37.5, 9 (eski yang) %12.5
- Civanperçemi (yarrow): 6 -> 1/16, 7 -> 5/16, 8 -> 7/16, 9 -> 3/16

Eski (hareketli) çizgiler tersine döner ve "dönüşen heksagram" oluşur.
"""
from __future__ import annotations

import json
import secrets
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "hexagrams.json"

Method = Literal["coins", "yarrow"]


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
    return {
        "number": hexagram["number"],
        "name": hexagram["pinyin"],
        "name_cn": hexagram["cn"],
        "name_en": hexagram["name_en"],
        "name_tr": hexagram["name_tr"],
        "judgment": hexagram["judgment_tr"],
        "image": hexagram["image_tr"],
        "lower_trigram": {"name_tr": lower["name_tr"], "symbol": lower["symbol"], "element": lower["element"]},
        "upper_trigram": {"name_tr": upper["name_tr"], "symbol": upper["symbol"], "element": upper["element"]},
        "unicode": chr(0x4DC0 + hexagram["number"] - 1),
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
    }

    if moving:
        transformed = [
            (1 - line) if (i + 1) in moving else line
            for i, line in enumerate(primary_lines)
        ]
        result["transformed"] = _hexagram_info(transformed)

    return result


def get_hexagram(number: int) -> dict[str, Any]:
    for hexagram in _load()["hexagrams"]:
        if hexagram["number"] == number:
            trigrams = _load()["trigrams"]
            lines = trigrams[hexagram["lower"]]["lines"] + trigrams[hexagram["upper"]]["lines"]
            return _hexagram_info(lines)
    raise ValueError(f"Heksagram bulunamadı: {number}")
