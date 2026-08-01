"""Kullaniciya gorunen sabit Turkce metinleri tarar.

Dil isi tek tek ekran goruntusuyle kovalanamayacak kadar genis oldugu icin
bu tarayici yazildi: her Dart dosyasinda kullaniciya gosterilen bir alana
(Text, label, hintText, SnackBar icerigi...) dogrudan yazilmis Turkce metin
arar. l10n uretimi, hukuki metinler ve kapsam disi yuz okuma ekrani atlanir.

Calistirma:  python tool/scan_hardcoded_strings.py
Cikis kodu 1 ise en az bir sizinti var.
"""
from __future__ import annotations

import pathlib
import re
import sys

TURKCE = re.compile("[ığşİĞŞçöü"
                    "ÇÖÜ]")

KOK = pathlib.Path("lib")

#: Atlanacak yollar ve gerekceleri.
ATLA = (
    "lib/l10n",                              # uretilmis ceviri dosyalari
    "lib/features/profile/legal_texts.dart",  # iki dil ayri sabitlerde
    "lib/features/oracle/face_tab.dart",      # v1 kapsami disi, cagrilmiyor
)

#: Kullaniciya gorunen alanlar.
GORUNUR = re.compile(
    r"Text\(|label:|title:|hintText:|labelText:|errorText:|prefixText:"
    r"|content:|text:|subtitle:|tooltip:|semanticLabel:"
)

LITERAL = re.compile(r"'((?:[^'\\]|\\.)*)'" r'|"((?:[^"\\]|\\.)*)"')

#: Kullanici arayuzu olmayan, gorunur alan gibi gorunen satirlar.
YOKSAY = ("debugPrint", "throw ", "assert(", "// ", "/// ")


def tara(kok: pathlib.Path) -> list[str]:
    bulgular: list[str] = []
    for dosya in sorted(kok.rglob("*.dart")):
        yol = dosya.as_posix()
        if yol.startswith(ATLA):
            continue
        for no, satir in enumerate(
                dosya.read_text(encoding="utf-8").splitlines(), 1):
            kirpik = satir.strip()
            if kirpik.startswith("//"):
                continue
            if any(im in satir for im in YOKSAY):
                continue
            if not GORUNUR.search(satir):
                continue
            for eslesme in LITERAL.finditer(satir):
                deger = eslesme.group(1) or eslesme.group(2) or ""
                if TURKCE.search(deger):
                    bulgular.append(f"{yol}:{no}: {deger[:90]}")
    return bulgular


def main() -> int:
    if not KOK.is_dir():
        print("lib/ bulunamadi — betigi apps/mobile icinden calistirin.")
        return 2

    bulgular = tara(KOK)
    if not bulgular:
        print("Temiz: gorunur alanlarda sabit Turkce metin yok.")
        return 0

    print(f"{len(bulgular)} sizinti:")
    for bulgu in bulgular:
        print("  " + bulgu)
    return 1


if __name__ == "__main__":
    sys.exit(main())
