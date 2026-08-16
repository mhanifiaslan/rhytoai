r"""Sinastri eksen eşiklerini DAĞILIMDAN kalibre eder.

## Neden var

`synastry_service._ESIKLER` beş gerçek çiftle elle kalibre edilmişti ve
kodun kendi yorumu riski yazmıştı: "ortak eşik 'her ilişkide çekim güçlü,
duygu sessiz' gibi sahte bir tablo üretiyordu". Ölçüldüğünde risk gerçek
çıktı — 28 çiftte:

    iletişim  : %78 'hafif', hiç 'güçlü' yok
    çekim     : %53 'güçlü', neredeyse hiç 'hafif' yok

Yani kullanıcı her arkadaşında aynı tabloyu görüyordu ve ilişki ekranı
"jenerik" hissettiriyordu. Eşik bir ZEVK meselesi değil, dağılımın
nerede kesileceği meselesi; o yüzden tahminle değil ölçümle konur.

## Yöntem

Sentetik ama gerçekçi bir doğum havuzu üretilir (yıl/ay/gün/saat/şehir
çaprazı), tüm çiftler için eksen puanları hesaplanır ve eşikler
YÜZDELİKTEN verilir:

    güçlü   = üst %25   (puan >= 75. yüzdelik)
    belirgin= %25-60    (puan >= 40. yüzdelik)
    hafif   = altı

Böylece seviyeler tanım gereği dağılır: hiçbir eksende tek seviye
%50'yi geçemez. Eşikler mutlak bir "iyi ilişki" ölçüsü değil, POPÜLASYON
İÇİNDEKİ YER'dir — ürün zaten sayısal uyum puanı göstermiyor; burada da
gösterilen şey seviye adı, ham puan değil.

## Kullanım

    .venv\Scripts\python.exe scripts/calibrate_synastry.py --pairs 300
    .venv\Scripts\python.exe scripts/calibrate_synastry.py --check

`--check`: mevcut `_ESIKLER` ile dağılımı ölçer ve hiçbir eksende tek
seviyenin %50'yi geçmediğini doğrular (test bunu çağırır).
"""
from __future__ import annotations

import argparse
import collections
import itertools
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services import astro_service, synastry_service  # noqa: E402

#: Havuz: farklı yıl/mevsim/saat/şehir. Amaç "ortalama kullanıcı" değil,
#: gökyüzünün çeşitliliğini örneklemek — açı yoğunluğu mevsime ve yıla
#: göre değişiyor.
SEHIRLER = ["Istanbul", "Ankara", "Izmir", "Bursa", "Adana", "Konya",
            "Trabzon", "Antalya", "Gaziantep", "Erzurum"]


def dogum_havuzu(n: int, tohum: int = 20260816) -> list[dict]:
    rnd = random.Random(tohum)
    havuz = []
    for i in range(n):
        havuz.append(dict(
            name=f"K{i}",
            year=rnd.randint(1965, 2006),
            month=rnd.randint(1, 12),
            day=rnd.randint(1, 28),
            hour=rnd.randint(0, 23),
            minute=rnd.choice([0, 15, 30, 45]),
            city=rnd.choice(SEHIRLER),
            nation="TR",
        ))
    return havuz


def eksen_puanlari(kisiler: list[dict], max_cift: int
                   ) -> dict[str, list[float]]:
    """Her eksen için ham puan dağılımı."""
    puanlar: dict[str, list[float]] = {e: [] for e in synastry_service.AXES}
    ciftler = list(itertools.combinations(range(len(kisiler)), 2))
    random.Random(7).shuffle(ciftler)
    for i, j in ciftler[:max_cift]:
        ham = astro_service.get_synastry(kisiler[i], kisiler[j])
        for eksen, puan in _ham_puanlar(ham).items():
            puanlar[eksen].append(puan)
    return puanlar


def _ham_puanlar(synastry: dict) -> dict[str, float]:
    """`relationship_axes`'in içindeki toplamı eşiklerden BAĞIMSIZ üretir.

    Seviye eşiğe bağlı; kalibrasyon eşiği arayacağı için ham puana
    ihtiyaç var. Ağırlık mantığı servisle aynı fonksiyondan gelir —
    burada ikinci bir kopya tutulmaz.
    """
    toplam = {e: 0.0 for e in synastry_service.AXES}
    for a in synastry.get("aspects") or []:
        p1, p2, aci = a.get("p1"), a.get("p2"), a.get("aspect")
        if not p1 or not p2:
            continue
        if aci not in (synastry_service._HARMONIK | synastry_service._SERT):
            continue
        w = synastry_service._agirlik(a)
        for eksen in synastry_service._eksenler_icin(p1, p2):
            toplam[eksen] += w
    return toplam


def yuzdelik(degerler: list[float], p: float) -> float:
    if not degerler:
        return 0.0
    s = sorted(degerler)
    k = (len(s) - 1) * (p / 100.0)
    alt, ust = int(k), min(int(k) + 1, len(s) - 1)
    return s[alt] + (s[ust] - s[alt]) * (k - alt)


def seviye_dagilimi(puanlar: dict[str, list[float]],
                    esikler: dict[str, tuple[float, float]]
                    ) -> dict[str, collections.Counter]:
    dagilim = {}
    for eksen, liste in puanlar.items():
        guclu, belirgin = esikler[eksen]
        c: collections.Counter = collections.Counter()
        for p in liste:
            if p >= guclu:
                c["strong"] += 1
            elif p >= belirgin:
                c["present"] += 1
            elif p > 0:
                c["light"] += 1
            else:
                c["quiet"] += 1
        dagilim[eksen] = c
    return dagilim


def _rapor(dagilim, n) -> float:
    """Dağılımı basar, en baskın seviyenin oranını döndürür."""
    en_kotu = 0.0
    for eksen, c in dagilim.items():
        baskin, adet = c.most_common(1)[0]
        oran = adet / max(n, 1)
        en_kotu = max(en_kotu, oran)
        print(f"  {eksen:14} {dict(c)}  -> en baskin %{oran*100:.0f} ({baskin})")
    return en_kotu


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--people", type=int, default=40)
    ap.add_argument("--pairs", type=int, default=200)
    ap.add_argument("--check", action="store_true",
                    help="mevcut esikleri dogrula, yeni esik onerme")
    args = ap.parse_args()

    kisiler = dogum_havuzu(args.people)
    print(f"{len(kisiler)} dogum, {args.pairs} cift hesaplaniyor...")
    puanlar = eksen_puanlari(kisiler, args.pairs)
    n = len(next(iter(puanlar.values())))

    if args.check:
        print(f"\nMEVCUT esiklerle dagilim ({n} cift):")
        en_kotu = _rapor(seviye_dagilimi(puanlar, synastry_service._ESIKLER), n)
        tamam = en_kotu <= 0.50
        print(f"\nen baskin seviye orani: %{en_kotu*100:.0f} "
              f"(hedef: <= %50) -> {'TAMAM' if tamam else 'KALIBRASYON GEREK'}")
        return 0 if tamam else 1

    yeni = {}
    print(f"\nDagilim ({n} cift):")
    for eksen, liste in puanlar.items():
        guclu = round(yuzdelik(liste, 75), 2)
        belirgin = round(yuzdelik(liste, 40), 2)
        yeni[eksen] = (guclu, belirgin)
        print(f"  {eksen:14} min={min(liste):.2f} medyan="
              f"{yuzdelik(liste, 50):.2f} maks={max(liste):.2f}"
              f"  -> guclu>={guclu} belirgin>={belirgin}")

    print("\nOnerilen _ESIKLER (synastry_service.py'ye yapistir):")
    print("_ESIKLER = {")
    for eksen, (g, b) in yeni.items():
        print(f'    "{eksen}": ({g}, {b}),')
    print("}")

    print(f"\nBu esiklerle dagilim ({n} cift):")
    en_kotu = _rapor(seviye_dagilimi(puanlar, yeni), n)
    print(f"\nen baskin seviye orani: %{en_kotu*100:.0f} (hedef: <= %50)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
