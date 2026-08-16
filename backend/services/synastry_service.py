"""İlişki eksenleri (R2-L1): sinastriyi NİTEL okuma haline getirir.

Kategori standardı sinastri puanıdır ("uyum 82/100") — Rytho bilinçli olarak
o puanı GÖSTERMEZ. Gerekçe iki katlı: (1) tek sayı, ölçülmemiş bir kesinlik
iddiasıdır ve "ölçülmeyen söylenmez" ilkesine aykırıdır; (2) bir ilişkiyi
100 üzerinden puanlamak, kullanıcıya hakkında karar veremeyeceği bir hüküm
dayatır. Onun yerine ilişki DÖRT EKSENDE okunur; her eksen iki şey söyler:

* **seviye** — bağ ne kadar belirgin (kaç açı, ne kadar dar orb),
* **ton** — bağ akıcı mı, karışık mı, zorlayıcı mı (harmonik/sert dengesi).

Sürtünme ayrı bir eksen DEĞİL, eksenlerin tonudur: "Satürn kare Ay" hem
duygusal ekseni aktive eder hem onu zorlaştırır. Ayrı eksen yapıldığında
aynı açı iki kez sayılıyor ve gerilim yapay olarak şişiyordu.

Hesap tamamen determinist (sabit tablo, LLM yok). Eşikler UYDURMA DEĞİL:
gerçek haritalarla ölçülen dağılımdan kalibre edildi (bkz. _ESIKLER) —
eksenler farklı ölçeklerde çalışıyor, tek eşik hepsini yanlış okurdu.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

#: Eksen hesabı sürümü — tablolar değişince artar, önbellek tazelenir.
SYNASTRY_CALC_VERSION = "1"

#: Eksen anahtarları — l10n adları prompts katmanında (SYNASTRY_AXIS_NAMES).
AXES = ("communication", "emotional", "attraction", "bond")

_HARMONIK = {"conjunction", "trine", "sextile"}
_SERT = {"square", "opposition"}

_ACI_AGIRLIK = {
    "conjunction": 1.3, "opposition": 1.15, "square": 1.1,
    "trine": 1.0, "sextile": 0.85,
}

#: Kişisel noktalar — bir açının "bu ilişkiye dair" sayılması için en az
#: bir ucunun kişisel olması beklenir.
_KISISEL = {"Sun", "Moon", "Mercury", "Venus", "Mars", "Ascendant",
            "Medium_Coeli"}

#: Eksen başına eşikler (güçlü, belirgin). Beş gerçek çiftle ölçülen
#: dağılımdan: iletişim 1.6-3.4, duygu 0.6-1.3, çekim 2.5-4.0, zemin
#: 0.5-1.8. Ölçek farkı büyük — ortak eşik "her ilişkide çekim güçlü,
#: duygu sessiz" gibi sahte bir tablo üretiyordu. Örneklem küçüktür;
#: canlıda dağılım görülünce yeniden kalibre edilir.
_ESIKLER = {
    "communication": (2.6, 1.4),
    "emotional": (1.6, 0.8),
    "attraction": (3.6, 2.2),
    "bond": (1.7, 0.9),
}

#: Ton eşiği: harmonik ağırlığın toplam içindeki payı.
_TON_AKICI = 0.6
_TON_ZORLU = 0.4

#: Bir eksende dayanak olarak gösterilecek en fazla açı. Amaç kanıt sunmak,
#: açı listesi dökmek değil.
MAX_BASIS = 3


def _eksenler_icin(p1: str, p2: str) -> list[str]:
    """Bu gezegen çifti hangi eksenleri besliyor?

    Bir açı birden çok eksene girebilir ve bu doğrudur: Ay–Merkür teması
    hem duyguyu hem iletişimi ilgilendirir.
    """
    ikili = {p1, p2}
    bulunan: list[str] = []

    if "Mercury" in ikili and (ikili - {"Mercury"}) & (
            _KISISEL | {"Jupiter", "Saturn"}):
        bulunan.append("communication")
    if "Moon" in ikili and (ikili - {"Moon"}) & (
            _KISISEL | {"Neptune", "Jupiter", "Saturn"}):
        bulunan.append("emotional")
    if ikili & {"Venus", "Mars"} and ikili & {
            "Venus", "Mars", "Sun", "Moon", "Ascendant", "Pluto"}:
        bulunan.append("attraction")
    # Zemin: zaman gezegenleri (Satürn/Jüpiter) kişisel bir noktaya
    # dokunuyorsa, ya da iki kimlik noktası (Güneş/Ay/Yükselen) buluşuyorsa
    # — ilişkinin dayanıklılığı burada okunur.
    if (ikili & {"Saturn", "Jupiter"} and ikili & _KISISEL) or (
            ikili <= {"Sun", "Moon", "Ascendant"}):
        bulunan.append("bond")
    return bulunan


def _agirlik(a: dict[str, Any]) -> float:
    orb = abs(float(a.get("orbit") or a.get("orb") or 0.0))
    return _ACI_AGIRLIK.get(a.get("aspect"), 1.0) / (1.0 + orb)


def _seviye(eksen: str, puan: float) -> str:
    guclu, belirgin = _ESIKLER[eksen]
    if puan >= guclu:
        return "strong"
    if puan >= belirgin:
        return "present"
    if puan > 0:
        return "light"
    return "quiet"


def _ton(harmonik: float, toplam: float) -> str:
    if toplam <= 0:
        return "quiet"
    oran = harmonik / toplam
    if oran >= _TON_AKICI:
        return "flowing"
    if oran <= _TON_ZORLU:
        return "challenging"
    return "mixed"


def relationship_axes(synastry: dict[str, Any]) -> dict[str, Any]:
    """Sinastri açılarından dört nitel eksen + dayanakları.

    ``synastry`` astro_service.get_synastry çıktısıdır. Dönen yapıda ham
    doğum verisi YOKTUR — yalnız açı adları, ölçülen orb'lar, seviye ve ton.
    Uyum puanı da taşınmaz (bilinçli).
    """
    toplam: dict[str, float] = {e: 0.0 for e in AXES}
    harmonik: dict[str, float] = {e: 0.0 for e in AXES}
    dayanak: dict[str, list[dict[str, Any]]] = {e: [] for e in AXES}

    for a in synastry.get("aspects") or []:
        p1, p2, aci = a.get("p1"), a.get("p2"), a.get("aspect")
        if not p1 or not p2 or aci not in (_HARMONIK | _SERT):
            continue
        agirlik = _agirlik(a)
        for eksen in _eksenler_icin(p1, p2):
            toplam[eksen] += agirlik
            if aci in _HARMONIK:
                harmonik[eksen] += agirlik
            dayanak[eksen].append({
                "p1": p1, "p2": p2, "aspect": aci,
                "orb": round(abs(float(a.get("orbit") or 0.0)), 2),
                "supportive": aci in _HARMONIK,
                "weight": round(agirlik, 4),
            })

    eksenler = []
    for eksen in AXES:
        kanitlar = sorted(dayanak[eksen], key=lambda d: -d["weight"])
        eksenler.append({
            "axis": eksen,
            "level": _seviye(eksen, toplam[eksen]),
            "tone": _ton(harmonik[eksen], toplam[eksen]),
            "basis": [{k: v for k, v in d.items() if k != "weight"}
                      for d in kanitlar[:MAX_BASIS]],
            "count": len(kanitlar),
        })

    # Öne çıkan eksen: eşiğine en çok yaklaşan (ölçekler farklı olduğu için
    # ham puanla değil, "belirgin" eşiğine oranla kıyaslanır).
    def oran(e: str) -> float:
        return toplam[e] / _ESIKLER[e][1]

    return {
        "calc_version": SYNASTRY_CALC_VERSION,
        "axes": eksenler,
        "lead_axis": max(AXES, key=lambda e: (oran(e), -AXES.index(e))),
    }
