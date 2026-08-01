"""Tetrabiblos (Ashmand 1822) ham metnini korpus biçimine çevirir.

Kaynak: Project Gutenberg #70850, J.M. Ashmand çevirisi (1822) — kamu malı.
Künye: knowledge/SOURCES.md

Betik olarak yazıldı, elle düzenlenmedi: hangi bölümün neden alındığı/alınmadığı
kod içinde görünür ve kaynak metin güncellenirse tekrar üretilebilir.

## Kapsam seçimi üç kurala dayanıyor

**1. Yasak alan (ürün ilkesi).** Ptolemaios'un ölüm süresi, hastalık, düşük ve
servet bölümleri var. Bunları korpusa almak, güvenlik kapısını ARKADAN
delmek olurdu: kapı kullanıcının SORUSUNU süzüyor, ama masum bir soruya
getirilen "ölüm süresi" pasajı cevabı oraya sürükleyebilir. Bu yüzden yasak
alan korpus seviyesinde de uygulanıyor — savunma iki katmanlı.

**2. Temellendirilebilirlik.** Sabit yıldızlar, sınırlar (terms) ve derece
hükümdarlıkları uygulamanın HESAPLAMADIĞI şeyler. Bunlar hakkında pasaj
döndürmek, modeli elimizde karşılığı olmayan bir konum hakkında konuşmaya
davet eder — "gök verisi uydurulmaz" ilkesiyle çelişir.

**3. Ürünle ilgi.** Kitap II bütünüyle ülke/iklim/tutulma astrolojisi. Doğru
ve ilginç, ama kişisel okuma yapan bir uygulamanın arama uzayını kirletir:
alakasız pasaj döndürme olasılığını artırır.

Kullanım:
    .venv/Scripts/python.exe scripts/ingest_tetrabiblos.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
HAM = REPO / "knowledge" / "raw" / "tetrabiblos_ashmand_pg70850.txt"
HEDEF = REPO / "knowledge" / "corpus" / "en" / "tetrabiblos.md"

PG_BASLA = "*** START OF THE PROJECT GUTENBERG EBOOK"
PG_BITIR = "*** END OF THE PROJECT GUTENBERG EBOOK"

#: Alınacak bölümler: (kitap, bölüm) -> korpustaki başlık.
#: Başlıklar kaynaktaki büyük harf hâlinden okunabilir biçime çevrildi;
#: içerik değiştirilmedi.
SECILEN: dict[tuple[str, str], str] = {
    # --- Kitap I: doktrin. Uygulamanın hesapladığı her şeyin karşılığı burada.
    ("FIRST", "IV"): "The Influences of the Planetary Orbs",
    ("FIRST", "V"): "Benefics and Malefics",
    ("FIRST", "VI"): "Masculine and Feminine Planets",
    ("FIRST", "VII"): "Diurnal and Nocturnal Planets",
    ("FIRST", "VIII"): "The Influence of Position with Regard to the Sun",
    ("FIRST", "XII"): "The Annual Seasons",
    ("FIRST", "XIII"): "The Influence of the Four Angles",
    ("FIRST", "XIV"): "Tropical, Equinoctial, Fixed and Bicorporeal Signs",
    ("FIRST", "XV"): "Masculine and Feminine Signs",
    ("FIRST", "XVI"): "Mutual Configurations of the Signs",
    ("FIRST", "XVII"): "Signs Commanding and Obeying",
    ("FIRST", "XVIII"): "Signs Beholding Each Other, and of Equal Power",
    ("FIRST", "XIX"): "Signs Inconjunct",
    ("FIRST", "XX"): "Houses of the Planets",
    ("FIRST", "XXI"): "The Triplicities",
    ("FIRST", "XXII"): "Exaltations",
    ("FIRST", "XXVI"): "Faces, Chariots and Other Attributes of the Planets",
    ("FIRST", "XXVII"): "Application, Separation and Other Faculties",
    # --- Kitap III: kişi. Karakter ve mizaç; uygulamanın omurgası.
    ("THIRD", "III"): "The Degree Ascending",
    ("THIRD", "XVI"): "The Form and Temperament of the Body",
    ("THIRD", "XVIII"): "The Quality of the Mind",
    # --- Kitap IV: hayat alanları. Sohbette en çok sorulan konular.
    ("FOURTH", "III"): "The Fortune of Rank",
    ("FOURTH", "IV"): "The Quality of Employment",
    ("FOURTH", "V"): "Marriage",
    ("FOURTH", "VII"): "Friends and Enemies",
    ("FOURTH", "VIII"): "Travelling",
}

#: Bilinçli olarak DIŞARIDA bırakılanlar ve sebepleri. Liste burada duruyor ki
#: "unutulmuş mu, elenmiş mi" sorusu bir daha sorulmasın.
DISARIDA = {
    # Yasak alan — ürün ilkesi (sağlık / hamilelik / ölüm / finans)
    ("THIRD", "II"): "hamilelik (gebe kalma ve doğum)",
    ("THIRD", "VII"): "hamilelik (cinsiyet kestirimi)",
    ("THIRD", "IX"): "sağlık + incitici dil (sakat doğumlar)",
    ("THIRD", "X"): "ölüm (yaşamayan çocuklar)",
    ("THIRD", "XI"): "ölüm (ömür süresi)",
    ("THIRD", "XII"): "ölüm (prorogasyon tekniği)",
    ("THIRD", "XIII"): "ölüm (prorogasyon tekniği)",
    ("THIRD", "XIV"): "ölüm (prorogasyon tekniği)",
    ("THIRD", "XV"): "ölüm (prorogasyon örneği)",
    ("THIRD", "XVII"): "sağlık (bedenin hastalıkları)",
    ("THIRD", "XIX"): "sağlık (aklın hastalıkları)",
    ("THIRD", "V"): "aile hakkında kestirim — ürün kapsamı dışı",
    ("THIRD", "VI"): "aile hakkında kestirim — ürün kapsamı dışı",
    ("THIRD", "VIII"): "hamilelik (ikizler)",
    # Once alinmisti, sonra cikarildi: bolum aslinda kitabin ICINDEKILERI —
    # "omur suresi", "olum bicimi", "servet" basliklarini sayiyor ve yorum
    # degeri dusuk. Getirilen tek pasaj o olursa cevabi yasak alana surukler.
    ("THIRD", "IV"): "icindekiler listesi; olum/servet basliklarini sayiyor",
    ("FOURTH", "II"): "finans (servet)",
    ("FOURTH", "VI"): "hamilelik (çocuklar)",
    ("FOURTH", "IX"): "ölüm (ölüm biçimi)",
    ("FOURTH", "X"): "ölüm (prorogasyon tekniği)",
    # Temellendirilemez — uygulama bunları hesaplamıyor
    ("FIRST", "IX"): "sabit yildizlar — hesaplanmiyor",
    ("FIRST", "X"): "takimyildizlar — hesaplanmiyor",
    ("FIRST", "XI"): "takimyildizlar — hesaplanmiyor",
    ("FIRST", "XXIII"): "sinirlar (terms) — hesaplanmiyor",
    ("FIRST", "XXIV"): "sinirlar (terms) — hesaplanmiyor",
    ("FIRST", "XXV"): "derece hukumdarliklari — hesaplanmiyor",
    # Yorum degil, giris/savunma metni
    ("FIRST", "I"): "proem",
    ("FIRST", "II"): "astrolojinin savunusu — yorum icermez",
    ("FIRST", "III"): "astrolojinin savunusu — yorum icermez",
    ("THIRD", "I"): "proem",
    ("FOURTH", "I"): "proem",
}

_KITAP = re.compile(r"^BOOK THE (FIRST|SECOND|THIRD|FOURTH)\s*$")
_BOLUM = re.compile(r"^CHAPTER ([IVXL]+)\s*$")
#: Satır başındaki dipnot paragrafı: "[54] Placidus şöyle der..."
_DIPNOT_PARAGRAF = re.compile(r"^\[\d+\]")
#: Metin içi dipnot işareti: "Syntaxis[19]"
_DIPNOT_ISARETI = re.compile(r"\[\d+\]")


def bolumleri_ayikla(metin: str) -> dict[tuple[str, str], list[str]]:
    """Ham metni (kitap, bölüm) -> satırlar sözlüğüne böler."""
    satirlar = metin.splitlines()
    bolumler: dict[tuple[str, str], list[str]] = {}
    kitap = bolum = None
    for satir in satirlar:
        k = _KITAP.match(satir)
        if k:
            kitap, bolum = k.group(1), None
            continue
        b = _BOLUM.match(satir)
        if b and kitap:
            bolum = b.group(1)
            bolumler[(kitap, bolum)] = []
            continue
        if kitap and bolum:
            bolumler[(kitap, bolum)].append(satir)
    return bolumler


def paragraflari_topla(satirlar: list[str], baslik: str) -> list[str]:
    """Sabit genişlikte sarılmış satırları gerçek paragraflara birleştirir.

    Ham metin 72 sütuna sarılı. Satırlar birleştirilmezse parçalama cümle
    sınırlarını göremez ve embedding kırık metin üzerinde çalışır.
    """
    paragraflar: list[str] = []
    tampon: list[str] = []
    # Bölümün kendi başlığı ilk anlamlı satır(lar)dır; içeriğe dahil edilmez.
    baslik_atlandi = False
    # Dipnotlar 72 sütuna sarılı ve BİRDEN FAZLA SATIR sürüyor. Yalnızca
    # "[29]" ile başlayan satırı atlamak yetmiyor: devamı yeni bir paragraf
    # sanılıp korpusa yarım cümle olarak giriyordu ("Sun as a planetary orb,
    # in consequence of..."). Bu yüzden dipnot boş satıra kadar atlanır.
    dipnot_icinde = False

    for satir in satirlar:
        duz = satir.strip()
        if not duz:
            dipnot_icinde = False
            if tampon:
                paragraflar.append(" ".join(tampon))
                tampon = []
            continue
        if dipnot_icinde:
            continue
        if not baslik_atlandi:
            # Büyük harf başlık satırlarını atla
            if duz == duz.upper() and any(c.isalpha() for c in duz):
                continue
            baslik_atlandi = True
        if _DIPNOT_PARAGRAF.match(duz):
            # Dipnotlar çevirmenin/derleyicinin yorumu ve sık sık BAŞKA
            # kaynaklardan alıntı taşıyor (Placidus, Cooper çevirisi...).
            # Kamu malı olup olmadıkları ayrı bir soru; korpusa alınmıyor.
            dipnot_icinde = True
            if tampon:
                paragraflar.append(" ".join(tampon))
                tampon = []
            continue
        tampon.append(duz)

    if tampon:
        paragraflar.append(" ".join(tampon))

    temiz = []
    for p in paragraflar:
        p = _DIPNOT_ISARETI.sub("", p)
        p = p.replace("_", "")            # italik işaretleri
        p = re.sub(r"\s+", " ", p).strip()
        if len(p) >= 40:
            temiz.append(p)
    if not temiz:
        print(f"UYARI: '{baslik}' bos cikti", file=sys.stderr)
    return temiz


def main() -> int:
    if not HAM.exists():
        print(f"Ham metin yok: {HAM}", file=sys.stderr)
        return 1

    ham = HAM.read_text(encoding="utf-8")

    # Project Gutenberg başlık/altlığı ayıklanır: o metin PG'nin paketlediği
    # e-kitaba ve markasına ait, alttaki 1822 çevirisine değil.
    bas = ham.find(PG_BASLA)
    son = ham.find(PG_BITIR)
    if bas < 0 or son < 0:
        print("PG basvuru isaretleri bulunamadi.", file=sys.stderr)
        return 1
    govde = ham[ham.index("\n", bas) + 1:son]

    bolumler = bolumleri_ayikla(govde)

    # Kaynakta olup ne SECILEN ne DISARIDA listesinde geçen bölüm varsa
    # sessizce düşmesin: kapsam kararı bilinçli olmalı.
    bilinmeyen = [k for k in bolumler if k not in SECILEN and k not in DISARIDA
                  and k[0] != "SECOND"]
    if bilinmeyen:
        print(f"UYARI: kapsam karari verilmemis bolumler: {bilinmeyen}",
              file=sys.stderr)

    parcalar = [
        "---",
        "book: Tetrabiblos",
        "author: Claudius Ptolemaeus",
        "translator: J. M. Ashmand (1822)",
        "license: public-domain",
        "source: Project Gutenberg eBook #70850 (PG basligi/altligi ayiklandi)",
        "---",
        "",
        "# Tetrabiblos — Claudius Ptolemaeus, tr. J. M. Ashmand (1822)",
        "",
    ]

    yazilan = 0
    for anahtar, baslik in SECILEN.items():
        satirlar = bolumler.get(anahtar)
        if satirlar is None:
            print(f"UYARI: {anahtar} kaynakta bulunamadi", file=sys.stderr)
            continue
        paragraflar = paragraflari_topla(satirlar, baslik)
        if not paragraflar:
            continue
        parcalar.append(f"## {baslik}")
        parcalar.append("")
        parcalar.extend(f"{p}\n" for p in paragraflar)
        yazilan += 1

    HEDEF.parent.mkdir(parents=True, exist_ok=True)
    HEDEF.write_text("\n".join(parcalar), encoding="utf-8")
    boyut = HEDEF.stat().st_size / 1024
    print(f"{HEDEF} yazildi: {yazilan} bolum, {boyut:.0f} KB")
    print(f"Kapsam disi birakilan: {len(DISARIDA)} bolum "
          f"(gerekceler betikte)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
