"""Legge 1899 yao (çizgi) metinlerini hexagrams.json'a işler (Revize İ1).

KAYNAK: James Legge, *The Yî King* (Sacred Books of the East XVI; 1882,
2. baskı 1899) — KAMU MALI. Project Gutenberg'de müstakil nüshası yok
(#25501 Çince orijinal çıktı); dijital nüsha Internet Sacred Text Archive
(sacred-texts.com/ich/ic01..ic64.htm). Künye knowledge/SOURCES.md'de.

NEDEN: hexagrams.json 64 hüküm + 64 imge taşıyor ama 384 çizgi pasajı
yoktu — I Ching pratiğinde yorumun ağırlık merkezi hareketli çizgilerin
METNİDİR; numarası değil.

DİSİPLİN (Tetrabiblos ingest'iyle aynı):
* İndirilen ham HTML knowledge/raw/legge/ altında SAKLANIR (yeniden koşum
  ağa çıkmaz; nüsha denetlenebilir kalır).
* Sayım kapısı: 64 heksagramın her birinde tam 6 çizgi paragrafı (+1 ve
  2'de yedinci "tüm çizgiler" pasajı) bulunamazsa HİÇBİR ŞEY yazılmaz.
* Legge'in parantezli editoryal ekleri çevirinin parçasıdır, KORUNUR.

Kullanım: backend dizininden
    .venv/Scripts/python.exe scripts/ingest_legge_yao.py
"""
from __future__ import annotations

import html
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
DATA_FILE = BACKEND / "data" / "hexagrams.json"
RAW_DIR = BACKEND.parent / "knowledge" / "raw" / "legge"
BASE_URL = "https://sacred-texts.com/ich/ic{n:02d}.htm"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) RythoAI-ingest"


def _indir(n: int) -> str:
    """Sayfayı yerel önbellekten okur; yoksa indirir ve saklar."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    yerel = RAW_DIR / f"ic{n:02d}.htm"
    if yerel.exists():
        return yerel.read_text(encoding="utf-8", errors="replace")
    istek = urllib.request.Request(BASE_URL.format(n=n),
                                   headers={"User-Agent": UA})
    with urllib.request.urlopen(istek, timeout=30) as yanit:
        icerik = yanit.read().decode("utf-8", errors="replace")
    yerel.write_text(icerik, encoding="utf-8")
    time.sleep(0.5)  # arşive nazik ol
    return icerik


def _temizle(parca: str) -> str:
    """HTML artıklarını ve sayfa işaretlerini süpürür."""
    parca = re.sub(r"<[^>]+>", " ", parca)
    parca = html.unescape(parca)
    # SBE dizgi işaretleri: "p. 57" sayfa imleri, köşeli dipnot imleri.
    parca = re.sub(r"\bp\.\s*\d+\b", " ", parca)
    parca = re.sub(r"\[\d+\]", " ", parca)
    # OCR harf bölünmesi: "T he fourth NINE" (heksagram 55) — dizgi hatası
    # metnin kendisinde de kalmasın.
    parca = re.sub(r"\bT\s+he\b", "The", parca)
    return re.sub(r"\s+", " ", parca).strip()


#: Çizgi pasajları "The first NINE/SIX..." kalıbıyla başlar; sıra numarası
#: RAKAMDAN DEĞİL bu kelimeden türetilir. Sebep: nüshada OCR artıkları var
#: — heksagram 6'da "5." yerine "S." basılmış. Rakama güvenmek 64 sayfada
#: sessiz kayıplar üretirdi; sıra kelimesi dizgi hatasından etkilenmiyor.
_SIRA_KELIMESI = {
    "first": 1, "second": 2, "third": 3,
    "fourth": 4, "fifth": 5, "sixth": 6, "topmost": 6,
}


def _cizgileri_ayikla(html_metin: str, n: int) -> tuple[list[str], str | None]:
    """Sayfadan 6 çizgi pasajı (+ varsa 7.) çıkarır.

    İki nüsha tuzağına dayanıklı:
    * OCR rakam bozulması ("S." = "5.") — sıra kelimesinden numara.
    * Sayfa kırılması: bir pasaj iki <p>'ye bölünebiliyor; numarasız devam
      paragrafı aktif çizgiye EKLENİR (heksagram 6'nın 3. çizgisi böyle
      kurtuldu). Dipnotlar "Footnotes" iminde kesilir.
    """
    govde = html_metin.split("Footnotes")[0]
    paragraflar = re.findall(r"<p[^>]*>(.*?)</p>", govde,
                             flags=re.S | re.I)
    # Nüsha kalıp çeşitleri: "The first NINE" / "In the first (or lowest)
    # NINE" (hex 1) / "From the first SIX" (hex 39) / "(To the subject of)
    # the fourth NINE" (hex 40) / küçük harf "the fifth six" (hex 11) /
    # numarasız çizgi (hex 8/3) / OCR "S." (hex 6/5). Sabit önek kovalamak
    # bitmez; kalıp paragraf başındaki DAR PENCEREDE aranır — asıl güvence
    # sıra kelimesi + hemen ardından gelen nine/six çifti.
    cizgi_kalibi = re.compile(
        r"\bthe\s+(first|second|third|fourth|fifth|sixth|topmost)"
        r"(?:\s*\([^)]*\))?\s*,?\s*(?:place|line)?\s*"
        r".{0,20}?\b(nine|six)\b", flags=re.S | re.I)

    cizgiler: dict[int, str] = {}
    aktif: int | None = None
    for p in paragraflar:
        duz = _temizle(p)
        if not duz:
            continue
        es_no = re.match(r"^([0-9SlI])\.\s+(.*)$", duz)
        icerik = es_no.group(2).strip() if es_no else duz
        # Numaralı paragrafta arama penceresi geniş (parantezli girişler
        # var); numarasızda dar — düz metnin ortasındaki bir gönderme
        # çizgi başı sanılmasın.
        pencere = 80 if es_no else 40
        kelime = cizgi_kalibi.search(icerik[:pencere])
        if kelime:
            # Numara SIRA KELİMESİNDEN: nüshada "5." yerine "S." (OCR) ve
            # heksagram 8'de 3. çizginin numarası hiç yok — rakam güvenilmez.
            no = _SIRA_KELIMESI[kelime.group(1).lower()]
            cizgiler.setdefault(no, icerik)
            aktif = no
            continue
        if es_no:
            if es_no.group(1) == "7":
                cizgiler.setdefault(7, icerik)
                aktif = 7
                continue
            # Numaralı ama çizgi kalıbına uymayan paragraf (hüküm altı
            # madde, dipnot kaçağı): aktif zincir kesilir ki yanlış
            # çizgiye devam yapıştırılmasın.
            aktif = None
            continue
        # Numarasız paragraf: aktif çizginin sayfa-kırılması devamı olabilir.
        # Başlık/bölüm imleri eklenmez.
        if aktif is not None and "HEXAGRAM" not in duz and not duz.isupper():
            cizgiler[aktif] = f"{cizgiler[aktif]} {duz}".strip()

    eksik = [i for i in range(1, 7) if i not in cizgiler]
    if eksik:
        raise SystemExit(
            f"Heksagram {n}: çizgi paragrafı eksik {eksik} — YAZILMADI. "
            f"Sayfa yapısı değişmiş olabilir; knowledge/raw/legge/"
            f"ic{n:02d}.htm elle incelenmeli.")

    yedinci = cizgiler.get(7)
    if n in (1, 2) and not yedinci:
        raise SystemExit(
            f"Heksagram {n}: beklenen 7. pasaj (tüm çizgiler) yok.")
    if n not in (1, 2) and yedinci:
        raise SystemExit(
            f"Heksagram {n}: beklenmeyen 7. paragraf — dipnot kaçağı "
            f"olabilir, elle incelenmeli.")

    return [cizgiler[i] for i in range(1, 7)], yedinci


def main() -> None:
    veri = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    heksagramlar = {h["number"]: h for h in veri["hexagrams"]}
    assert len(heksagramlar) == 64

    tum: dict[int, tuple[list[str], str | None]] = {}
    for n in range(1, 65):
        tum[n] = _cizgileri_ayikla(_indir(n), n)
        print(f"  {n:2d}: 6 çizgi{' + tüm-çizgiler' if tum[n][1] else ''}")

    # Sayım kapısı geçildi — şimdi yaz.
    for n, (cizgiler, yedinci) in tum.items():
        heksagramlar[n]["lines_en"] = cizgiler
        if yedinci:
            heksagramlar[n]["all_lines_en"] = yedinci

    DATA_FILE.write_text(
        json.dumps(veri, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    # Windows konsolu cp1254; ASCII dışı süs karakteri kullanma.
    print(f"Tamam: 64x6 cizgi + 2 'tum cizgiler' pasaji yazildi -> "
          f"{DATA_FILE.name}")


if __name__ == "__main__":
    sys.exit(main())
