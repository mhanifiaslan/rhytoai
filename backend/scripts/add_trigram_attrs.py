"""8 trigrama aile/nitelik/yön atributları ekler (Revize İ1).

Klasik Shuo Gua (Sekiz Trigram Üzerine) geleneğinin tartışmasız çekirdeği:
aile rolleri (baba/anne/üç oğul/üç kız), tek kelimelik doğa nitelikleri ve
Sonraki Gök (King Wen) yönleri. Değerler dilden bağımsız ANAHTARDIR; adlar
services/prompts altındaki TRIGRAM_FAMILY_NAMES / TRIGRAM_ATTRIBUTE_NAMES
tablolarından çözülür (BAZI_ELEMENTS deseni).

Kullanım: backend dizininden
    .venv/Scripts/python.exe scripts/add_trigram_attrs.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

DATA_FILE = (Path(__file__).resolve().parent.parent
             / "data" / "hexagrams.json")

#: trigram anahtarı -> (aile, nitelik, Sonraki Gök yönü)
ATTRS: dict[str, tuple[str, str, str]] = {
    "qian": ("father", "creative", "NW"),
    "kun": ("mother", "receptive", "SW"),
    "zhen": ("eldest_son", "arousing", "E"),
    "kan": ("middle_son", "abysmal", "N"),
    "gen": ("youngest_son", "stillness", "NE"),
    "xun": ("eldest_daughter", "penetrating", "SE"),
    "li": ("middle_daughter", "clinging", "S"),
    "dui": ("youngest_daughter", "joyous", "W"),
}


def main() -> None:
    veri = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    trigramlar = veri["trigrams"]
    assert set(trigramlar) == set(ATTRS), (
        f"Trigram kümesi uyuşmuyor: {set(trigramlar) ^ set(ATTRS)}")
    for ad, (aile, nitelik, yon) in ATTRS.items():
        trigramlar[ad]["family"] = aile
        trigramlar[ad]["attribute"] = nitelik
        trigramlar[ad]["direction"] = yon
    DATA_FILE.write_text(
        json.dumps(veri, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    print("Tamam: 8 trigrama family/attribute/direction eklendi.")


if __name__ == "__main__":
    sys.exit(main())
