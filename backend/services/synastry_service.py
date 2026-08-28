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

import hashlib
import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

#: Eksen hesabı sürümü — tablolar değişince artar, önbellek tazelenir.
#:
#: "2" (1.6.0): iki şey birden değişti ve ikisi de sonucu oynatıyor —
#: açılar artık öneme göre sıralanıp öyle kesiliyor (eskiden gezegen
#: sırasıyla kesiliyordu ve Yükselen temaslarının çoğu düşüyordu), ve
#: eşikler 200 çiftlik dağılımdan kalibre edildi. Eksenler LLM'siz
#: hesap olduğu için tazelenme kimseye jeton yazmaz.
#:
#: "3" (1.7.0): saatsiz tarafın Yükselen/MC açıları artık sinastriden
#: de düşüyor (natal ile aynı disiplin). Ölçüldü: uydurma Yükselen
#: "ortak zemin" eksenini bir seviye şişiriyordu.
SYNASTRY_CALC_VERSION = "3"

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
        # Saatsizlik beyanı motordan geliyor; eksen katmanı onu taşır ki
        # arayüz "bu okumada Yükselen yok" diyebilsin.
        "disclosures": list(synastry.get("disclosures") or []),
        "axes": eksenler,
        "lead_axis": max(AXES, key=lambda e: (oran(e), -AXES.index(e))),
    }


# ---------------------------------------------------------------------------
# Önbellekli erişim + sohbet fısıltısı (R4-2)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Counterpart:
    """İlişkinin KARŞI TARAFI — Rytho arkadaşı ya da kullanıcının eklediği
    kişi (P-turu).

    İlişki hesabı iki tarafın doğum verisinden başka bir şey bilmek zorunda
    değil; ikisi arasındaki fark kimlik ve gizlilik katmanında. Bu yüzden
    hesap yolu buradan aşağısı için TEK: arkadaş ve kişi aynı fonksiyonlara
    girer, ayrışma yalnız bu nesnenin nasıl kurulduğundadır.
    """

    #: Önbellek anahtarına giren kararlı kimlik. Arkadaşta sıralı ikili
    #: (simetrik — iki taraf aynı kaydı paylaşır), kişide sahibe özel.
    key: str

    #: astro_service'in beklediği doğum verisi.
    birth: dict[str, Any]

    #: Prompt'ta ve fısıltıda görünen ad. Arkadaşta gerçek görünen ad,
    #: kişide İLİŞKİ ETİKETİ ("eşin") — sunucu kişinin adını bilmiyor.
    label: str

    sun_sign: str | None = None

    #: Yalnız eklenen kişide dolu; eksen adlarını ve AI çerçevesini
    #: belirler (çocukla "çekim" ekseni gösterilmez).
    relation: str | None = None


def friend_counterpart(uid: str, friend_uid: str) -> Counterpart | None:
    """Arkadaşı karşı tarafa çevirir; doğum verisi yoksa None."""
    from services import chart_context, profile_service

    friend = profile_service.get_profile(friend_uid)
    if not friend or not chart_context.has_birth_data(friend):
        return None
    return Counterpart(
        # Simetrik anahtar KORUNUYOR: mevcut önbellek kayıtları düşmesin.
        key="-".join(sorted((uid, friend_uid))),
        birth=profile_service.birth_kwargs(friend),
        label=(friend.get("displayName") or friend.get("username") or "?"),
        sun_sign=friend.get("sunSign"),
    )


def person_counterpart(uid: str, person_id: str,
                       lang: str | None = None) -> Counterpart | None:
    """Eklenen kişiyi karşı tarafa çevirir; kişi bu kullanıcının değilse
    None (sahiplik doğrulaması `people_service.get_person` üzerinden).

    Anahtar doğum ÖZETİNİ taşır: kullanıcı kişinin doğum saatini
    düzeltince eski eksenler kendiliğinden düşer. Arkadaş yolunda bu
    yapılamıyor (anahtar simetrik ve iki profile bağlı) ama burada
    bedava — eksenler LLM'siz hesap, tazelenmesi kimseye ücret yazmaz.
    """
    from services import people_service, prompts

    kayit = people_service.get_person(uid, person_id)
    if not kayit or not kayit.get("birthDate"):
        return None

    etiket = prompts.relation_label(lang, kayit.get("relation") or "other")
    ozet = hashlib.sha256(
        "|".join(str(kayit.get(alan) or "") for alan in
                 ("birthDate", "birthTime", "birthCity", "birthNation"))
        .encode("utf-8")).hexdigest()[:10]
    return Counterpart(
        key=f"{uid}-p{person_id}-{ozet}",
        birth=people_service.birth_kwargs(kayit, name=etiket),
        label=etiket,
        sun_sign=kayit.get("sunSign"),
        relation=kayit.get("relation") or "other",
    )


def axes_for(uid: str, other: Counterpart) -> dict[str, Any] | None:
    """Kullanıcı ile karşı taraf arasındaki eksenler, önbellekli.

    Kullanıcının kendi doğum verisi yoksa None: varsayılan doğum verisiyle
    "sizin ilişkiniz" üretilmez (chart_context kuralı). YETKİ DOĞRULAMASI
    ÇAĞIRANIN İŞİ — bu fonksiyon yalnız hesaplar.
    """
    from core import cache
    from services import astro_service, chart_context, profile_service

    me = profile_service.get_profile(uid)
    if not me or not chart_context.has_birth_data(me):
        return None

    anahtar = f"rel-axes-{SYNASTRY_CALC_VERSION}-{other.key}"
    eksenler = cache.get(anahtar)
    if eksenler is None:
        ham = astro_service.get_synastry(
            profile_service.birth_kwargs(me), other.birth)
        eksenler = relationship_axes(ham)
        # Natal veriye bağlı: doğum verisi değişmedikçe geçerli.
        cache.set(anahtar, eksenler, ttl_seconds=30 * 24 * 3600,
                  owner_uid=uid)
    return eksenler


def cached_axes(uid: str, friend_uid: str) -> dict[str, Any] | None:
    """İki arkadaşın ilişki eksenleri, çift bazlı simetrik önbellekle.

    Hem /reports/relationship ucu hem sohbet fısıltısı BUNU kullanır —
    aynı ikili için tek hesap. İki profilden biri doğum verisiz ise None:
    varsayılan doğum verisiyle "sizin ilişkiniz" üretilmez
    (chart_context kuralı). ARKADAŞLIK DOĞRULAMASI ÇAĞIRANIN İŞİDİR —
    bu fonksiyon yalnız hesaplar.
    """
    karsi = friend_counterpart(uid, friend_uid)
    if karsi is None:
        return None
    return axes_for(uid, karsi)


# ---------------------------------------------------------------------------
# Günlük çift-transit ölçümü (GT-turu)
#
# Cihaz bulgusu: ilişki katmanında SIFIR tarih farkındalığı vardı — fısıltı
# her gün bayt-aynı eksen satırlarını taşıyor, ücretli günlük okumanın
# "bugün" girdisi bile çifte özgü değildi (herkese aynı Ay evresi). Bu
# katman LLM'SİZ ölçümdür ($0, maliyet belgesi emsali): bugünün gökyüzünün
# İKİ haritanın ilişkiyle ilgili natal noktalarına değdiği yerler.
# ---------------------------------------------------------------------------

#: Taraf başına ve toplamda en çok kaç vuruş. Fısıltı ve şerit kompakt
#: kalmalı; dönemin temasını 3-4 vuruş zaten anlatıyor.
PAIR_TRANSIT_PER_SIDE = 2
PAIR_TRANSIT_CAP = 4

#: Günlük önbellek ömrü (`transit-facts-v2` emsali: 36 saat — gün dönümü
#: taşmalarına pay bırakır).
PAIR_TTL_SECONDS = 36 * 3600


def pair_transits(uid: str, other: Counterpart,
                  today=None) -> dict[str, Any] | None:
    """Bugün ÇİFTE dokunan gökyüzü — LLM'siz, gün-anahtarlı önbellekli.

    Her taraf için bugünün transitleri hesaplanır ve ilişkiyle İLGİLİ
    natal noktalara süzülür: kişisel noktalar (`_KISISEL`) + o tarafın
    eksen dayanaklarında adı geçen noktalar (eksenleri taşıyan
    Jüpiter/Satürn gibi ağır noktalar da böylece girer). Süzgeç doktrini
    `chart_context.filter_transit_hits`ten gelir — tek yerde yaşar.

    Dönen: ``{"date": iso, "hits": [{side: "user"|"other", transit,
    natal, aspect, orb, movement}]}``; kullanıcının doğum verisi yoksa
    None. Uçlar `today`e kullanıcının yerel gününü geçirir (dyad emsali);
    fısıltı yolu varsayılanla çalışır — gece yarısı sınırında en kötü
    bir fazla önbellek satırı.
    """
    import datetime as dt

    from core import cache
    from services import astro_service, chart_context, profile_service

    me = profile_service.get_profile(uid)
    if not me or not chart_context.has_birth_data(me):
        return None

    gun = (today or dt.date.today()).isoformat()
    anahtar = f"pair-transits-{SYNASTRY_CALC_VERSION}-{other.key}-{gun}"
    mevcut = cache.get(anahtar)
    if mevcut is not None:
        return mevcut

    eksenler = axes_for(uid, other) or {}
    kullanici_nokta = set(_KISISEL)
    karsi_nokta = set(_KISISEL)
    for e in eksenler.get("axes") or []:
        for b in e.get("basis") or []:
            if b.get("p1"):
                kullanici_nokta.add(b["p1"])
            if b.get("p2"):
                karsi_nokta.add(b["p2"])

    vuruslar: list[dict[str, Any]] = []
    taraflar = (
        ("user", profile_service.birth_kwargs(me), frozenset(kullanici_nokta)),
        ("other", other.birth, frozenset(karsi_nokta)),
    )
    for taraf, birth, noktalar in taraflar:
        try:
            ham = astro_service.get_transits(
                **astro_service.subject_kwargs(birth),
                hour_known=astro_service.hour_is_known(birth))
        except Exception as exc:
            logger.warning("Çift transiti hesaplanamadı (%s/%s): %s",
                           uid, taraf, exc)
            continue
        for v in chart_context.filter_transit_hits(
                ham.get("aspects_to_natal", []), natal_points=noktalar,
                cap=PAIR_TRANSIT_PER_SIDE):
            vuruslar.append({**v, "side": taraf})

    # Birleşimde de yavaş-önce: dönemi işaretleyen Satürn/Plüton vuruşu,
    # hangi tarafta olursa olsun Merkür'ün önüne geçer.
    vuruslar.sort(key=lambda v: (
        0 if chart_context.is_slow_mover(v["transit"]) else 1, v["orb"]))
    sonuc = {"date": gun, "hits": vuruslar[:PAIR_TRANSIT_CAP]}
    cache.set(anahtar, sonuc, ttl_seconds=PAIR_TTL_SECONDS, owner_uid=uid)
    return sonuc


def pair_transits_cached(uid: str, other: Counterpart,
                         today=None) -> dict[str, Any] | None:
    """Bugünün çift vuruşları YALNIZ ÖNBELLEKTEN — asla hesaplamaz (OB3).

    Öğle bildirimi tüm kullanıcıları tarar; her çift için efemeris
    koşturmak toplu işte kabul edilemez. Bu okuma organiktir: çift, gün
    içinde bir ilişki yüzeyi açıldıysa (`pair_transits` önbelleğe yazar)
    öğlen anılabilir; açılmadıysa o gün sessizce atlanır.
    """
    import datetime as dt

    from core import cache

    gun = (today or dt.date.today()).isoformat()
    anahtar = f"pair-transits-{SYNASTRY_CALC_VERSION}-{other.key}-{gun}"
    return cache.get(anahtar)


def pair_transit_lines(hits: list[dict[str, Any]], other_label: str,
                       lang: str) -> list[str]:
    """Vuruşları isteğin dilinde tek satırlara çevirir (fısıltı + dyad ortak).

    Yan adlandırma ek almaz ("{label} tarafında") — keyfî bir ada Türkçe
    iyelik eki yapıştırmak yazım hatası üretirdi.
    """
    from services import prompts

    p = prompts.get(lang)
    satirlar = []
    for v in hits or []:
        yan = (p.PAIR_SIDE_SELF if v.get("side") == "user"
               else p.PAIR_SIDE_OTHER_FMT.format(label=other_label))
        hareket = ""
        if v.get("movement"):
            hareket = ", " + p.MOVEMENT_NAMES.get(v["movement"],
                                                  v["movement"])
        satirlar.append(p.PAIR_TRANSIT_FMT.format(
            side=yan,
            transit=prompts.planet_name(lang, v.get("transit")),
            natal=prompts.planet_name(lang, v.get("natal")),
            aspect=prompts.aspect_name(lang, v.get("aspect")),
            orb=v.get("orb"), movement=hareket))
    return satirlar


def relationship_whisper(uid: str, friend_uid: str, lang: str,
                         max_chars: int = 900) -> str:
    """Arkadaş için sohbet bağlamı (R4-2) — `whisper_for`'un ince sarmalı."""
    karsi = friend_counterpart(uid, friend_uid)
    if karsi is None:
        # KA8: boş fısıltı loglanır — eskiden model bağlamsız kaldığında
        # sebep hiçbir yerde görünmüyordu.
        logger.info("İlişki fısıltısı boş: arkadaşın doğum verisi yok "
                    "(%s→%s)", uid, friend_uid)
        return ""
    return whisper_for(uid, karsi, lang, max_chars=max_chars)


def whisper_for(uid: str, other: Counterpart, lang: str,
                max_chars: int = 900) -> str:
    """Sohbet için kompakt ilişki bağlamı (R4-2, P-turu'nda genelleşti).

    Cihaz bulgusu: arkadaşla ilgili soruda model bağlamsız kaldığı için
    kullanıcının KENDİ haritasından genel cevap uyduruyordu. Bu fısıltı,
    ölçülen eksenleri (seviye · ton + en güçlü dayanak açısı) ve karşı
    tarafın adını modelin önüne koyar. Ham doğum verisi YOKTUR — dyad
    kuralı: karşı tarafın doğum bilgisi hiçbir katmanda taşınmaz.

    Eklenen kişide "ad" gerçek ad değil ilişki etiketidir ("eşin"):
    sunucu o kişinin adını zaten bilmiyor.
    """
    from services import prompts

    eksenler = axes_for(uid, other)
    if eksenler is None:
        # KA8: boş fısıltı loglanır (kullanıcının kendi doğum verisi yok).
        logger.info("İlişki fısıltısı boş: kullanıcının doğum verisi yok "
                    "(%s)", uid)
        return ""

    etiket = "Arkadaş" if lang == "tr" else "Friend"
    if other.relation:
        etiket = "Kişi" if lang == "tr" else "Person"
    ilk = f"{etiket}: {other.label}"
    if other.sun_sign:
        ilk += f" ({other.sun_sign})"
    satirlar = [ilk]

    yerel = prompts.localize_relationship_axes(lang, eksenler,
                                               other.relation)
    for e in yerel.get("axes") or []:
        satir = (f"- {e['axis_local']}: {e['level_local']} · "
                 f"{e['tone_local']}")
        kanit = (e.get("basis") or [None])[0]
        if kanit:
            satir += (f" ({kanit['p1_local']} {kanit['aspect_local']} "
                      f"{kanit['p2_local']}, orb {kanit['orb']}°)")
        satirlar.append(satir)

    # GT2: BUGÜNÜN çifte özgü gökyüzü — fısıltı artık her gün taze veri
    # taşır (eskiden bu blok bayt-aynıydı ve model her gün aynı ilişki
    # cümlelerini kuruyordu). Ölçüm düşerse fısıltı eksensiz değil,
    # yalnız bugünsüz kalır.
    try:
        gunluk = pair_transits(uid, other)
    except Exception as exc:
        logger.warning("Çift transit fısıltıya eklenemedi (%s): %s",
                       uid, exc)
        gunluk = None
    if gunluk and gunluk.get("hits"):
        p = prompts.get(lang)
        satirlar.append(p.PAIR_TODAY_LABEL)
        satirlar += ["  - " + s for s in pair_transit_lines(
            gunluk["hits"], other.label, lang)]

    metin = "\n".join(satirlar)
    if other.relation:
        # Modelin türü bilmesi ŞART: aksi halde çocuğuyla ilgili soruya
        # romantik çerçeveyle cevap verebilir (bkz. RELATION_FRAME).
        cerceve = prompts.relation_frame(lang, other.relation)
        if cerceve:
            metin = f"{metin}\n- {cerceve}"
    return metin[:max_chars]
