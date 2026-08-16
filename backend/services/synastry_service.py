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
#:
#: "2" (1.6.0): iki şey birden değişti ve ikisi de sonucu oynatıyor —
#: açılar artık öneme göre sıralanıp öyle kesiliyor (eskiden gezegen
#: sırasıyla kesiliyordu ve Yükselen temaslarının çoğu düşüyordu), ve
#: eşikler 200 çiftlik dağılımdan kalibre edildi. Eksenler LLM'siz
#: hesap olduğu için tazelenme kimseye jeton yazmaz.
SYNASTRY_CALC_VERSION = "2"

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

#: Eksen başına eşikler (güçlü, belirgin) — **dağılımdan** kalibre edildi.
#:
#: Üretim: `scripts/calibrate_synastry.py --people 40 --pairs 200`
#: (40 doğum, 200 çift, tohum sabit). Eşikler yüzdelikten verilir:
#: güçlü = 75. yüzdelik, belirgin = 40. yüzdelik. Ölçülen dağılım:
#:
#:     iletişim  min 0.15  medyan 1.46  maks 3.77
#:     duygu     min 0.13  medyan 1.58  maks 4.16
#:     çekim     min 1.87  medyan 5.60  maks 11.60
#:     zemin     min 1.14  medyan 3.20  maks 6.16
#:
#: Ölçek farkı neden ortak eşik konamayacağını gösteriyor: çekimin
#: medyanı iletişimin maksimumunun üstünde.
#:
#: Öncekiler beş çiftle ELLE konmuştu ve sahte bir tablo üretiyordu —
#: 28 çiftte iletişim %78 "hafif" (hiç "güçlü" yok), çekim %53 "güçlü"
#: (neredeyse hiç "hafif" yok). Yani kullanıcı her arkadaşında aynı
#: manzarayı görüyordu; "ilişkiler jenerik" şikâyetinin bir ayağı buydu.
#: Yeni eşiklerle hiçbir eksende tek seviye %50'yi geçmiyor (ölçülen
#: en baskın oran %40). Bekçi: `--check` + test_relationship_axes.
_ESIKLER = {
    "communication": (1.95, 1.29),
    "emotional": (2.14, 1.36),
    "attraction": (6.68, 5.15),
    "bond": (3.86, 2.89),
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


# ---------------------------------------------------------------------------
# Önbellekli erişim + sohbet fısıltısı (R4-2)
# ---------------------------------------------------------------------------

def cached_axes(uid: str, friend_uid: str) -> dict[str, Any] | None:
    """İki arkadaşın ilişki eksenleri, çift bazlı simetrik önbellekle.

    Hem /reports/relationship ucu hem sohbet fısıltısı BUNU kullanır —
    aynı ikili için tek hesap. İki profilden biri doğum verisiz ise None:
    varsayılan doğum verisiyle "sizin ilişkiniz" üretilmez
    (chart_context kuralı). ARKADAŞLIK DOĞRULAMASI ÇAĞIRANIN İŞİDİR —
    bu fonksiyon yalnız hesaplar.
    """
    from core import cache
    from services import astro_service, chart_context, profile_service

    me = profile_service.get_profile(uid)
    friend = profile_service.get_profile(friend_uid)
    if not me or not friend:
        return None
    if not (chart_context.has_birth_data(me)
            and chart_context.has_birth_data(friend)):
        return None

    ikili = "-".join(sorted((uid, friend_uid)))
    anahtar = f"rel-axes-{SYNASTRY_CALC_VERSION}-{ikili}"
    eksenler = cache.get(anahtar)
    if eksenler is None:
        ham = astro_service.get_synastry(
            profile_service.birth_kwargs(me),
            profile_service.birth_kwargs(friend))
        eksenler = relationship_axes(ham)
        # Natal veriye bağlı: doğum verisi değişmedikçe geçerli.
        cache.set(anahtar, eksenler, ttl_seconds=30 * 24 * 3600,
                  owner_uid=uid)
    return eksenler


def relationship_whisper(uid: str, friend_uid: str, lang: str,
                         max_chars: int = 600) -> str:
    """Sohbet için kompakt ilişki bağlamı (R4-2).

    Cihaz bulgusu: arkadaşla ilgili soruda model bağlamsız kaldığı için
    kullanıcının KENDİ haritasından genel cevap uyduruyordu. Bu fısıltı,
    ölçülen eksenleri (seviye · ton + en güçlü dayanak açısı) ve arkadaşın
    görünen adını modelin önüne koyar. Ham doğum verisi YOKTUR — dyad
    kuralı: arkadaşın doğum bilgisi hiçbir katmanda karşıya taşınmaz.
    """
    from services import profile_service, prompts

    eksenler = cached_axes(uid, friend_uid)
    if eksenler is None:
        return ""
    friend = profile_service.get_profile(friend_uid) or {}
    ad = friend.get("displayName") or friend.get("username") or "?"

    etiket = "Arkadaş" if lang == "tr" else "Friend"
    ilk = f"{etiket}: {ad}"
    if friend.get("sunSign"):
        ilk += f" ({friend['sunSign']})"
    satirlar = [ilk]

    yerel = prompts.localize_relationship_axes(lang, eksenler)
    for e in yerel.get("axes") or []:
        satir = (f"- {e['axis_local']}: {e['level_local']} · "
                 f"{e['tone_local']}")
        kanit = (e.get("basis") or [None])[0]
        if kanit:
            satir += (f" ({kanit['p1_local']} {kanit['aspect_local']} "
                      f"{kanit['p2_local']}, orb {kanit['orb']}°)")
        satirlar.append(satir)

    metin = "\n".join(satirlar)
    return metin[:max_chars]
