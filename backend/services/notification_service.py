"""Bildirim zamanlama mantığı — kime, ne zaman, kaç kez.

Bu modül **gönderim yapmaz**; yalnızca karar verir. Gönderim api/notify.py
içindedir. Ayrım bilinçli: buradaki kurallar (yerel saat, sessiz saat, tekrar
koruması) FCM'e hiç dokunmadan test edilebilmeli.

Üç kural birlikte çalışır ve üçü de kullanıcıyı korumak içindir:

1. **Yerel saat.** Bildirim kullanıcının sabahına denk gelmeli. Sunucu UTC'de
   çalışır; kullanıcının saat dilimi profilinde IANA adı olarak tutulur.
   Doğum şehri kullanılamaz — kişi doğduğu yerde yaşamıyor olabilir.
2. **Sessiz saat.** Gece bildirim göndermek, bu kategoride uygulamanın
   silinmesinin en hızlı yoludur. Varsayılan 22:00-08:00.
3. **Tekrar koruması.** Zamanlayıcı saatte bir çalışır ve yeniden deneme
   yapabilir; aynı bildirim iki kez gitmemeli. Gönderim kaydı sunucuya kapalı
   bir dokümanda tutulur.
"""
from __future__ import annotations

import datetime as dt
import logging
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from core import cache, firestore as firestore_client, i18n
from services import gemini_service, prompts

logger = logging.getLogger(__name__)

#: Saat dilimi okunamazsa kullanılacak varsayılan. Kullanıcıların büyük
#: çoğunluğu bu dilimde; yine de her profilde saat dilimi olması hedeflenir.
DEFAULT_TIMEZONE = "Europe/Istanbul"

#: Sessiz saat varsayılanları (yerel saat, 24 saatlik).
DEFAULT_QUIET_FROM = 22
DEFAULT_QUIET_TO = 8

#: Bildirim türlerinin hedef yerel saati. Zamanlayıcı saatte bir çalışır ve
#: yalnızca yerel saati bu değere eşit olan kullanıcılara gönderir.
TARGET_HOURS = {
    "daily": 9,     # sabah: günün okuması hazır
    "midday": 13,   # öğle: yalnız BUGÜN gerçekten kesinleşen olay varsa (OB3)
    "checkin": 20,  # akşam: günün önemli sinyaline bağlı kişisel soru (KA4)
    "streak": 20,   # akşam: seri kırılmadan önce son hatırlatma (soru yoksa)
}

#: Zamanlayıcıdan tetiklenebilecek türler.
SCHEDULED_TYPES = tuple(TARGET_HOURS)

#: Serinin hatırlatmaya değer sayılması için gereken en az gün. Tek günlük
#: seri için bildirim göndermek rahatsız edici olur; kaybedilecek bir şey yok.
MIN_STREAK_FOR_REMINDER = 2


def _notification_doc(uid: str):
    client = firestore_client.get_client()
    if client is None:
        return None
    return (client.collection("users").document(uid)
            .collection("private").document("notifications"))


# ---------------------------------------------------------------------------
# Yerel saat
# ---------------------------------------------------------------------------

def user_timezone(profile: dict[str, Any]) -> ZoneInfo:
    """Profildeki saat dilimi; tanınmıyorsa varsayılan.

    Bilinmeyen bir dilim yüzünden istisna fırlatmak, tek bir bozuk profilin
    tüm toplu gönderimi düşürmesi demek olurdu.
    """
    ad = (profile.get("timezone") or "").strip()
    if ad:
        try:
            return ZoneInfo(ad)
        except (ZoneInfoNotFoundError, ValueError):
            logger.info("Taninmayan saat dilimi: %s", ad)
    return ZoneInfo(DEFAULT_TIMEZONE)


def local_now(profile: dict[str, Any],
              now_utc: dt.datetime | None = None) -> dt.datetime:
    """Kullanıcının yerel saati."""
    now_utc = now_utc or dt.datetime.now(dt.timezone.utc)
    if now_utc.tzinfo is None:
        now_utc = now_utc.replace(tzinfo=dt.timezone.utc)
    return now_utc.astimezone(user_timezone(profile))


# ---------------------------------------------------------------------------
# Sessiz saat
# ---------------------------------------------------------------------------

def _saat(deger: Any, varsayilan: int) -> int:
    try:
        saat = int(deger)
    except (TypeError, ValueError):
        return varsayilan
    return saat if 0 <= saat <= 23 else varsayilan


def in_quiet_hours(profile: dict[str, Any], yerel: dt.datetime) -> bool:
    """Yerel saat sessiz aralıkta mı?

    Aralık gece yarısını aşabilir (22:00-08:00). ``from == to`` sessiz saat
    yok demektir; aksi halde 24 saat sessiz olurdu ve kullanıcı hiç bildirim
    almazdı.
    """
    baslangic = _saat(profile.get("quietFrom"), DEFAULT_QUIET_FROM)
    bitis = _saat(profile.get("quietTo"), DEFAULT_QUIET_TO)
    if baslangic == bitis:
        return False

    saat = yerel.hour
    if baslangic < bitis:
        return baslangic <= saat < bitis
    # Gece yarısını aşan aralık
    return saat >= baslangic or saat < bitis


# ---------------------------------------------------------------------------
# Tekrar koruması
# ---------------------------------------------------------------------------

def already_sent(uid: str, tur: str, gun: str) -> bool:
    """Bu tür bildirim bu yerel gün için gönderildi mi?"""
    doc = _notification_doc(uid)
    if doc is None:
        # Firestore yoksa tekrar korumasını uygulayamayız. Güvenli taraf
        # GÖNDERMEMEK: aynı bildirimi iki kez atmak, hiç atmamaktan kötüdür.
        return True
    try:
        anlik = doc.get()
    except Exception as exc:
        logger.warning("Gonderim kaydi okunamadi (%s): %s", uid, exc)
        return True
    if not anlik.exists:
        return False
    return (anlik.to_dict() or {}).get(f"{tur}LastSent") == gun


def mark_sent(uid: str, tur: str, gun: str) -> None:
    doc = _notification_doc(uid)
    if doc is None:
        return
    try:
        doc.set({f"{tur}LastSent": gun,
                 "updatedAt": dt.datetime.now(dt.timezone.utc)}, merge=True)
    except Exception as exc:
        logger.warning("Gonderim kaydi yazilamadi (%s): %s", uid, exc)


# ---------------------------------------------------------------------------
# Karar
# ---------------------------------------------------------------------------

#: Tür -> profildeki tercih alanı. `checkin` BİLEREK streak tercihini
#: paylaşır: ikisi de "akşam dürtmesi" ailesinden ve akşam en fazla biri
#: gider — ayrı bir anahtar mobil ayar ekranını büyütürdü. Kullanıcılar
#: ayrı kapatmak isterse `notifyCheckin` o zaman eklenir.
PREF_FIELDS = {
    "daily": "notifyDaily",
    # OB3: öğle slotu "günün okuması" ailesinden — sabahı kapatan kullanıcı
    # öğleni de istemiyordur; ayrı bir anahtar ayar ekranını büyütürdü.
    "midday": "notifyDaily",
    "checkin": "notifyStreak",
    "streak": "notifyStreak",
    "friend": "notifyFriends",
}


def wants(profile: dict[str, Any], tur: str) -> bool:
    """Kullanıcı bu türü açık bırakmış mı? Alan yoksa AÇIK sayılır."""
    alan = PREF_FIELDS.get(tur)
    if alan is None:
        return False
    return profile.get(alan) is not False


def should_send(profile: dict[str, Any], tur: str,
                now_utc: dt.datetime | None = None,
                ignore_target_hour: bool = False,
                ignore_dedupe: bool = False) -> tuple[bool, str]:
    """Zamanlayıcı bu kullanıcıya şimdi göndermeli mi?

    ``(gonderilsin, gerekce)`` döner. Gerekçe loglama ve test içindir;
    "gönderilmedi" kararlarının neden alındığı görünür olmalı.

    ``ignore_target_hour`` ve ``ignore_dedupe`` yalnızca duman testi içindir
    (yayın sonrası "bildirim gerçekten gidiyor mu" kontrolü).

    **Sessiz saat ve tercih HİÇBİR bayrakla atlanmaz.** Bu ikisi kullanıcının
    açık iradesi; elinde zamanlayıcı anahtarı olan biri bile kullanıcıyı gece
    yarısı uyandıramamalı ya da kapattığı bildirimi ona gönderememeli.
    """
    if tur not in SCHEDULED_TYPES:
        return False, "bilinmeyen-tur"
    if not profile.get("fcmToken"):
        return False, "token-yok"
    if not profile.get("onboardingCompleted"):
        return False, "onboarding-tamamlanmamis"
    if not wants(profile, tur):
        return False, "tercih-kapali"

    yerel = local_now(profile, now_utc)
    if not ignore_target_hour and yerel.hour != TARGET_HOURS[tur]:
        return False, "saat-uygun-degil"
    if in_quiet_hours(profile, yerel):
        # Hedef saat sessiz aralığa denk geliyorsa kullanıcının tercihi
        # kazanır; bildirim atlanır.
        return False, "sessiz-saat"

    if tur == "streak":
        seri = int(profile.get("streakCount") or 0)
        if seri < MIN_STREAK_FOR_REMINDER:
            return False, "seri-kisa"
        if profile.get("lastSeenDaily") == yerel.date().isoformat():
            return False, "bugun-zaten-okudu"
        # KA4: akşam EN FAZLA bir bildirim — check-in gittiyse seri
        # hatırlatması susar. (checkin işi :08'de, streak :10'da koşar;
        # bu koruma sırayı da yeniden denemeyi de dert etmez.)
        if already_sent(profile["uid"], "checkin",
                        yerel.date().isoformat()):
            return False, "aksam-checkin-gitti"

    if tur == "checkin" and already_sent(profile["uid"], "streak",
                                         yerel.date().isoformat()):
        # Ters sıra da korunur: streak bir şekilde önce gittiyse aynı
        # akşam bir de soru göndermeyiz.
        return False, "aksam-streak-gitti"

    if not ignore_dedupe and already_sent(profile["uid"], tur,
                                          yerel.date().isoformat()):
        return False, "zaten-gonderildi"

    return True, "gonderilecek"


# ---------------------------------------------------------------------------
# Bildirim metni
#
# Birim ekonomi kuralı burada da geçerli: bildirim metni KULLANICI BAŞINA
# üretilmez. Günlük bildirimin gövdesi (burç, gün, dil) anahtarıyla
# önbelleklenir — 12 burç x 2 dil = günde en fazla 24 LLM çağrısı, kaç
# kullanıcı olursa olsun. Seri ve arkadaş bildirimleri hiç LLM kullanmaz.
# ---------------------------------------------------------------------------

#: Bildirim satırı için üst sınır. Prompt 85 karakter istiyor; model taşarsa
#: kırpmak yerine yedek metne düşeriz (yarım cümle göstermeyiz).
MAX_PUSH_BODY = 110


def daily_push_cache_key(sign: str, gun: str, lang: str) -> str:
    return f"push-daily-{sign}-{gun}-{lang}"


def daily_push_body(sign: str, sky: dict[str, Any], lang: str,
                    gun: str | None = None) -> str:
    """Burç için günün tek satırlık bildirim metni.

    ``sign`` İngilizce burç anahtarıdır ("leo"). ``sky`` çağıran tarafından
    **dile göre yerelleştirilmiş** olarak gelir.
    """
    lang = lang if lang in i18n.SUPPORTED else i18n.DEFAULT
    gun = gun or dt.date.today().isoformat()
    p = prompts.get(lang)
    sign_adi = p.SIGN_NAMES.get(sign, sign)

    anahtar = daily_push_cache_key(sign, gun, lang)
    onbellekten = cache.get(anahtar)
    if onbellekten is not None:
        return onbellekten

    moon = (sky or {}).get("moon_phase") or {}
    retros = ", ".join((sky or {}).get("retrogrades") or []) or p.NONE_LABEL
    prompt = p.PUSH_DAILY_PROMPT.format(
        sign=sign_adi, today=gun, moon_name=moon.get("name") or "-",
        illumination=moon.get("illumination"), retros=retros,
    )

    metin = (gemini_service.generate(prompt, lang=lang) or "").strip()
    # Model bazen tırnak içinde döndürüyor; bildirimde tırnak görünmemeli.
    metin = metin.strip('"').strip("'").strip()
    if not metin or len(metin) > MAX_PUSH_BODY:
        if metin:
            logger.info("Push satiri cok uzun (%s kar.), yedege dusuldu",
                        len(metin))
        metin = p.PUSH_DAILY_FALLBACK.format(sign=sign_adi)

    # Yedek metin de önbelleklenir: aksi halde Gemini'nin sorunlu olduğu bir
    # saatte her burç için tekrar tekrar denenirdi.
    cache.set(anahtar, metin, ttl_seconds=36 * 3600)
    return metin


def signal_push(profile: dict[str, Any], lang: str,
                today: dt.date | None = None
                ) -> tuple[str, str, str] | None:
    """Sabah bildirimi kullanıcının 1 numaralı sinyalinden (R2-S4 → KA-turu).

    ``(başlık, gövde, parmak_izi)`` döner: başlık temanın adı ("Bugün:
    İlişkiler"), gövde o güne/o kişiye ÖZGÜ AI cümlesi — uç ile AYNI
    paylaşılan paketten (`cached_insight_bundle`), yani kullanıcı
    bildirimde okuduğu cümleyi uygulamayı açınca kartta bulur ve günde
    toplam bir LLM çağrısı yapılır (kim önce çalışırsa). Parmak izi
    derin bağlantı eşleşmesi içindir (KA5).

    Eski davranış (`headline` = 12 cümlelik sabit tablo) cihazda ölçülen
    kusurdu: tema+ton haftalarca sabit kaldığı için HERKESE her sabah
    birebir aynı metin gidiyordu. Paket üretilemezse gövde DÜRÜST teknik
    satıra düşer — o da ölçülmüş veridir ve tarih içerdiği için günden
    güne değişir.

    Üretilemezse (doğum verisi yok / hesap düştü / satır uzun) None döner
    ve çağıran paylaşımlı burç satırına düşer; bildirim ASLA atlanmaz.
    """
    try:
        from services import signal_service
        ham = signal_service.cached_signals(profile, today=today)
        if not ham or not ham.get("signals"):
            return None
        paket = signal_service.cached_insight_bundle(ham, lang)
        sinyal = prompts.localize_signals(lang, ham)["signals"][0]
        govde = ""
        if paket and paket.get("insights"):
            govde = paket["insights"][0]
            if not 0 < len(govde) <= prompts.get(lang).SIGNAL_INSIGHT_MAX:
                govde = ""  # taşan yorum: dürüst teknik satıra düş
        if not govde:
            govde = sinyal["technical"]
            if not 0 < len(govde) <= MAX_PUSH_BODY:
                return None
        p = prompts.get(lang)
        iz = signal_service.signals_fingerprint(ham)
        return (p.PUSH_SIGNAL_TITLE.format(
                    emoji=prompts.theme_emoji(sinyal.get("theme")),
                    theme=sinyal["theme_local"]),
                govde, iz)
    except Exception as exc:
        logger.warning("Sinyal bildirimi uretilemedi (%s): %s",
                       profile.get("uid"), exc)
        return None


def checkin_push(profile: dict[str, Any], lang: str,
                 today: dt.date | None = None) -> tuple[str, str] | None:
    """Akşam check-in sorusu (KA4) — YALNIZ önbellekten, LLM yakmaz.

    Soru sabahki toplu üretimin son satırıdır; akşam işi yalnız okur
    (`generate_if_missing=False`). Paket yoksa ya da o gün "önemli
    sinyal" çıkmadıysa None döner — çağıran kullanıcıyı atlar ve :10'daki
    seri hatırlatması normal davranır.
    """
    try:
        from services import signal_service
        ham = signal_service.cached_signals(profile, today=today)
        if not ham or not ham.get("signals"):
            return None
        paket = signal_service.cached_insight_bundle(
            ham, lang, generate_if_missing=False)
        soru = (paket or {}).get("checkin_question")
        if not soru:
            return None
        return prompts.get(lang).PUSH_CHECKIN_TITLE, soru
    except Exception as exc:
        logger.warning("Check-in bildirimi uretilemedi (%s): %s",
                       profile.get("uid"), exc)
        return None


def midday_push(profile: dict[str, Any], lang: str,
                today: dt.date | None = None
                ) -> tuple[str, str, dict[str, str]] | None:
    """Öğle ölçülü slotu (OB3) — yalnız gerçekten olay varsa, LLM'siz.

    ``(başlık, gövde, fcm_verisi)`` döner; olay yoksa None ve çağıran o
    kullanıcıyı "olay-yok" ile atlar — öğle bildirimi bir HAK değil,
    ölçülmüş bir olayın haberi. Çözüm sırası:

    a) **Kendi haritasında BUGÜN kesinleşen açı** (``days_to_exact == 0``,
       sabahki paylaşımlı sinyal önbelleği): gövde sabah paketindeki
       indeks-hizalı AI cümlesi (yalnız okunur — öğle LLM yakmaz), yoksa
       dürüst teknik satır. Yük birebir sabahki `daily` deseni: dokununca
       ilgili kartın dayanak sayfası açılır, mobilde SIFIR yeni tüketici.
    b) **Çift ânı, YALNIZ ÖNBELLEK** (`pair_transits_cached` — asla
       hesaplamaz): kabul edilmiş arkadaşlar + Çevrem kişileri taranır,
       bugün önbelleği olan çiftlerden en dar yavaş-gezen vuruş seçilir.
       Yük `type=friend` → Çevrem sekmesi.
    c) Hiçbiri → None.
    """
    try:
        from services import (circle_context, people_service, profile_service,
                              signal_service, synastry_service)

        today = today or dt.date.today()
        gun = today.isoformat()

        # --- a) kendi haritasında bugün kesinleşen ---
        ham = signal_service.cached_signals(profile, today=today)
        sinyaller = (ham or {}).get("signals") or []
        idx = next((i for i, s in enumerate(sinyaller)
                    if s.get("exact_on") and s.get("days_to_exact") == 0),
                   None)
        if ham and idx is not None:
            p = prompts.get(lang)
            yerel = prompts.localize_signals(lang, ham)["signals"][idx]
            paket = signal_service.cached_insight_bundle(
                ham, lang, generate_if_missing=False)
            govde = ""
            if paket and len(paket.get("insights") or []) > idx:
                govde = paket["insights"][idx]
                if not 0 < len(govde) <= p.SIGNAL_INSIGHT_MAX:
                    govde = ""
            if not govde:
                govde = yerel["technical"]
            if 0 < len(govde) <= max(MAX_PUSH_BODY, p.SIGNAL_INSIGHT_MAX):
                baslik = p.PUSH_MIDDAY_TITLE.format(
                    emoji=prompts.theme_emoji(yerel.get("theme")),
                    theme=yerel["theme_local"])
                veri = {"type": "daily", "route": "signal",
                        "fp": signal_service.signals_fingerprint(ham),
                        "idx": str(idx), "d": gun, "src": "midday"}
                sign = profile_service.sun_sign_key(profile)
                if sign:
                    veri["sign"] = sign
                return baslik, govde, veri

        # --- b) çift ânı, yalnız önbellekten ---
        uid = profile.get("uid") or ""
        adaylar: list = []
        for friend_uid in circle_context.list_accepted_friend_uids(uid):
            cp = synastry_service.friend_counterpart(uid, friend_uid)
            if cp is not None:
                adaylar.append(cp)
        for kayit in people_service.list_people(uid):
            cp = synastry_service.person_counterpart(
                uid, kayit["id"], lang=lang)
            if cp is not None:
                adaylar.append(cp)

        from services import chart_context
        en_iyi: tuple[tuple[int, float], Any, dict[str, Any]] | None = None
        for cp in adaylar:
            veri_cp = synastry_service.pair_transits_cached(uid, cp,
                                                            today=today)
            vuruslar = (veri_cp or {}).get("hits") or []
            if not vuruslar:
                continue
            v = vuruslar[0]  # zaten yavaş-önce + dar-orb sıralı
            sira = (0 if chart_context.is_slow_mover(v.get("transit")) else 1,
                    float(v.get("orb") or 99.0))
            if en_iyi is None or sira < en_iyi[0]:
                en_iyi = (sira, cp, v)

        if en_iyi is not None:
            _, cp, v = en_iyi
            satirlar = synastry_service.pair_transit_lines([v], cp.label,
                                                           lang)
            if satirlar and 0 < len(satirlar[0]) <= MAX_PUSH_BODY:
                p = prompts.get(lang)
                baslik = p.PUSH_MIDDAY_PAIR_TITLE.format(name=cp.label)
                return (baslik, satirlar[0],
                        {"type": "friend", "src": "midday", "d": gun})

        return None
    except Exception as exc:
        logger.warning("Ogle bildirimi uretilemedi (%s): %s",
                       profile.get("uid"), exc)
        return None


def streak_push(profile: dict[str, Any], lang: str) -> tuple[str, str]:
    """Seri hatırlatması — şablon, LLM yok."""
    p = prompts.get(lang)
    seri = int(profile.get("streakCount") or 0)
    return p.PUSH_STREAK_TITLE.format(days=seri), p.PUSH_STREAK_BODY


def friend_push(name: str, emoji: str, label: str,
                lang: str) -> tuple[str, str]:
    """Arkadaş tepkisi — şablon, LLM yok."""
    p = prompts.get(lang)
    return (p.PUSH_FRIEND_TITLE.format(name=name),
            p.PUSH_FRIEND_BODY.format(emoji=emoji, label=label))


def profile_language(profile: dict[str, Any]) -> str:
    """Profildeki dil; yoksa varsayılan.

    Bildirim sunucuda üretildiği için istemcinin ``Accept-Language`` başlığı
    burada yoktur — dil profile yazılır (bkz. apps/mobile/lib/core/locale.dart).
    """
    kod = (profile.get("language") or "").strip().lower()
    return kod if kod in i18n.SUPPORTED else i18n.DEFAULT


def can_send_event(profile: dict[str, Any], tur: str,
                   now_utc: dt.datetime | None = None) -> tuple[bool, str]:
    """Olay tabanlı bildirim (arkadaş tepkisi) gönderilebilir mi?

    Zamanlayıcıdan farkı: hedef saat yoktur, olay ne zaman olduysa o zaman
    gider. Ama sessiz saat yine de geçerlidir — bir arkadaşın tepkisi gece
    3'te telefonu titretmeye yetmez. Sessiz saatte bildirim DÜŞÜRÜLÜR,
    ertelenmez; tepki uygulama içindeki kutuda zaten görünüyor.
    """
    if not profile.get("fcmToken"):
        return False, "token-yok"
    if not wants(profile, tur):
        return False, "tercih-kapali"
    if in_quiet_hours(profile, local_now(profile, now_utc)):
        return False, "sessiz-saat"
    return True, "gonderilecek"
