"""Tek cihaz kilidi — YALNIZCA ücretli aboneler için; hakem "son giriş".

## Neden var

Ürün kararı: bir abonelik tek cihazdan kullanılır. Hesap paylaşımı,
kullanıcı başına LLM maliyeti olan bir üründe doğrudan zarar kalemidir —
beş kişinin paylaştığı tek abonelik, beş kullanıcının maliyetine tek
abonelik geliri demek.

## Nasıl çalışır (TC-turu: sunucu hakem, "son giriş kazanır")

İstemci her isteğe rastgele üretilmiş `X-Device-Id` başlığı ekler. Ücretli
uçlarda başlıktaki kimlik `users/{uid}/private/device` dokümanıyla
karşılaştırılır. Hakem, Firebase ID token'ındaki `auth_time`: girişte
sabitlenir, token yenilemede DEĞİŞMEZ — eski cihaz kullanıcı yeniden
giriş yapmadan "yeniden kazanamaz" (K1).

* Doküman yok → sessiz ilk sahiplenme (ilk cihaz zaten "onun cihazı").
* Kimlik eşleşiyor → geç.
* Eşleşmiyor → önce Firestore YENİDEN okunur (K4: instance-yerel memo'ya
  güvenilmez; başka instance'ta devralma olmuş olabilir). Hâlâ uyumsuzsa:
  `caller.auth_time > kayıt.claimedAt` → **otomatik devralma** (K2, yeni
  cihaz soru görmez); değilse **409** + ``X-Device-Conflict: 1``. 409'u
  gören istemci oturumu KAPATMAZ; "hesabın başka cihazda açıldı" kapısı
  gösterir — "Bu cihazda kullan" `POST /device/claim` ile açıkça devralır
  (`claimedAt=now` → öbür cihazın `auth_time`'ı ondan küçük kalır, ping-pong
  ancak kullanıcı isteğiyle), "Çıkış yap" `DELETE /device/claim` ile
  serbest bırakır (K7).

Karşılaştırma `claimedAt`'a yapılır, kayıttaki `authTime`'a değil: açık
devralma ve otomatik devralma aynı alanı yazar, eski kayıtlarda `authTime`
zaten yok.

## Bilinçli sınırlar

* **Ücretsiz VE deneme kullanıcısı hiç etkilenmez** (K3): kilit
  `get_subscription(uid).active` ister; `is_subscriber` değil — üç günlük
  denemede paylaşım riski yok ama yeniden kurulum/ikinci telefon yeni
  kullanıcıyı kilitlerdi. `FORCE_PLUS` kilidi etkilemez.
* **Başlık yoksa geç**: eski uygulama sürümleri kimlik göndermez.
* **Okuma hatası = "bilinmiyor" → geçir, YAZMA** (K5): geçici hata
  sahipliği ters çeviremez. "Kayıt yok" (None) ile karıştırılmaz.
* **`get_current_user`'a DOKUNULMAZ**: kilit yalnızca ücretli yollarda;
  eşitlik yolu süreç içi 60 sn memo'dan sürer, Firestore yalnız uyumsuzluk
  ve ilk okumada.
"""
from __future__ import annotations

import datetime as dt
import logging
import threading
import time
from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException

from core import entitlements
from core import firestore as firestore_client
from core.i18n import DEFAULT as DEFAULT_LANG
from core.messages import text

logger = logging.getLogger(__name__)

#: Cihaz uyuşmazlığında dönen kod. 402 paywall'a, 401 oturum yenilemeye
#: gider; ikisi de yanlış tepki doğururdu. 409 "çakışma"nın kendisidir.
DEVICE_CONFLICT_STATUS = 409

#: Süreç içi memo ömrü. Eşitlik yolunda Firestore okumasını keser;
#: uyumsuzlukta zaten yeniden okunur (K4), o yüzden bayatlık 409 üretmez.
_CACHE_TTL_SECONDS = 60.0


@dataclass(frozen=True)
class Claim:
    """`users/{uid}/private/device` dokümanının karar için gereken özü."""
    device_id: str
    platform: str | None
    claimed_at: float  # epoch saniye; alan yoksa 0.0


class _Unknown:
    """Okuma hatası / Firestore istemcisi yok. `None` ("kayıt yok") ile
    KARIŞTIRILMAZ: None sahiplenmeye yol açar, bilinmeyen açmaz (K5)."""

    def __repr__(self) -> str:  # pragma: no cover - teşhis
        return "_UNKNOWN"


_UNKNOWN = _Unknown()

_cache: dict[str, tuple[Claim | None, float]] = {}
_cache_lock = threading.Lock()


def _now() -> dt.datetime:
    """Sunucu saati (UTC). Testler zamanı buradan dondurur."""
    return dt.datetime.now(dt.timezone.utc)


def _device_ref(uid: str):
    client = firestore_client.get_client()
    if client is None:
        return None
    return (client.collection("users").document(uid)
            .collection("private").document("device"))


def _cached(uid: str) -> tuple[bool, Claim | None]:
    """(memo'da var mı, kayıt). Kilit altında tek sözlük erişimi."""
    with _cache_lock:
        kayit = _cache.get(uid)
    if kayit is None:
        return False, None
    claim, yazilma = kayit
    if time.monotonic() - yazilma > _CACHE_TTL_SECONDS:
        return False, None
    return True, claim


def _remember(uid: str, claim: Claim | None) -> None:
    with _cache_lock:
        _cache[uid] = (claim, time.monotonic())
        # Sınırsız büyüme yok: kaba bir kapak yeter, LRU şart değil.
        if len(_cache) > 10000:
            _cache.clear()


def _forget(uid: str) -> None:
    with _cache_lock:
        _cache.pop(uid, None)


def _epoch(value: Any) -> float:
    """Firestore Timestamp (datetime alt sınıfı) / sayı → epoch saniye."""
    if value is None:
        return 0.0
    if hasattr(value, "timestamp"):
        try:
            return float(value.timestamp())
        except Exception:
            return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _parse(data: dict[str, Any]) -> Claim | None:
    device_id = data.get("deviceId")
    if not device_id:
        return None
    platform = data.get("platform")
    return Claim(device_id=str(device_id),
                 platform=str(platform) if platform else None,
                 claimed_at=_epoch(data.get("claimedAt")))


def _stored(uid: str, *, refresh: bool = False) -> Claim | None | _Unknown:
    """Kayıtlı cihaz; memo'dan, gerekirse Firestore'dan.

    ``refresh=True`` memo'yu atlar, Firestore'u okur ve memo'yu tazeler.
    Üç sonuç ayrı: Claim (var) · None (doküman yok) · _UNKNOWN (okunamadı).
    """
    if not refresh:
        var, claim = _cached(uid)
        if var:
            return claim

    ref = _device_ref(uid)
    if ref is None:
        return _UNKNOWN
    try:
        snapshot = ref.get()
        data = (snapshot.to_dict() or {}) if snapshot.exists else {}
    except Exception as exc:
        logger.warning("Cihaz kaydı okunamadı (%s): %s", uid, exc)
        return _UNKNOWN

    claim = _parse(data)
    _remember(uid, claim)
    return claim


def _claim(uid: str, device_id: str, *, auth_time: int,
           platform: str | None) -> bool:
    """Kaydı bu cihaza yazar; yazıldıysa True.

    `platform` HER ZAMAN yazılır — bilinmiyorsa `None`. Eski değeri korumak
    (merge'de alanı atlamak) denendi ve yanlıştı: `_claim` cihaz
    DEĞİŞTİĞİNDE çağrılır, "eski değer" kaybeden cihazın platformudur ve
    409 başlığı onu "öbür cihaz" diye söylerdi — Android'de oturumu iPhone
    alan kullanıcı ekranda "android cihazında giriş yapıldı" okurdu.
    Bilinmeyen platform boş başlık → ekranda "—"; ölçülmeyen söylenmez.
    Korumalı istekler platformu `X-Device-Platform` ile taşır (36+
    istemciler), o yüzden otomatik devralmada da çoğunlukla bilinir.
    `claimedAt` sunucu saati: K2'nin kıyas noktası.
    """
    ref = _device_ref(uid)
    if ref is None:
        return False
    simdi = _now()
    yeni_platform = str(platform) if platform else None
    veri: dict[str, Any] = {
        "deviceId": device_id,
        "platform": yeni_platform,
        "authTime": int(auth_time or 0),
        "claimedAt": simdi,
        "lastSeenAt": simdi,
    }
    try:
        ref.set(veri, merge=True)
    except Exception as exc:
        logger.warning("Cihaz kaydı yazılamadı (%s): %s", uid, exc)
        return False

    _remember(uid, Claim(device_id=device_id, platform=yeni_platform,
                         claimed_at=simdi.timestamp()))

    # Platform aynası (AP-turu): private/** istemciye ve toplu istatistik
    # taramasına kapalı/pahalı; adminStats'ın platform kırılımı profildeki
    # bu tek alandan beslenir. Best-effort — cihaz devri bunun yüzünden
    # düşmez. Alanı olmayan eski kullanıcılar "bilinmiyor" sayılır.
    if platform:
        try:
            client = firestore_client.get_client()
            if client is not None:
                client.collection("users").document(uid).set(
                    {"platform": str(platform)}, merge=True)
        except Exception as exc:
            logger.warning("Platform aynası yazılamadı (%s): %s", uid, exc)
    return True


def _paid_subscriber(uid: str) -> bool:
    """K3: kilit yalnız ÜCRETLİ abonede. Deneme (in_trial) ve FORCE_PLUS
    `is_subscriber`'ı açar ama burayı AÇMAZ."""
    return bool(entitlements.get_subscription(uid).get("active"))


def _baslik_degeri(value: str | None) -> str:
    """HTTP başlığına güvenle sığan kısa ASCII; boşsa ''."""
    if not value:
        return ""
    return "".join(ch for ch in str(value)
                   if ch.isascii() and ch.isprintable())[:32]


def _iso(claimed_at: float) -> str:
    if not claimed_at:
        return ""
    return dt.datetime.fromtimestamp(claimed_at, dt.timezone.utc).isoformat(
        timespec="seconds")


def _conflict(kayit: Claim, lang: str) -> HTTPException:
    # `detail` düz metin kalır: istemci onu friendlyError ile gösteriyor.
    # Öbür cihazın bilgisi başlıklarda — kapı ekranı "{platform} · {saat}"
    # yazar. Başlık değerleri latin-1 olmak zorunda, o yüzden süzülür.
    return HTTPException(
        status_code=DEVICE_CONFLICT_STATUS,
        detail=text("device.conflict", lang),
        headers={
            "X-Device-Conflict": "1",
            "X-Device-Other-Platform": _baslik_degeri(kayit.platform),
            "X-Device-Claimed-At": _iso(kayit.claimed_at),
        },
    )


def enforce_single_device(uid: str, device_id: str | None, *,
                          auth_time: int, platform: str | None = None,
                          lang: str = DEFAULT_LANG) -> None:
    """Ücretli abonenin isteğini kayıtlı cihazla karşılaştırır.

    Sıralama maliyet için önemli: abonelik kontrolü önce — ücretsiz ve
    deneme kullanıcısında ne Firestore okuması ne başka iş yapılır.
    `platform` isteğin `X-Device-Platform` başlığından gelir; otomatik
    devralmada kayda yazılır ki kaybeden cihazın 409 ekranı DOĞRU cihazı
    söylesin (eski istemci başlık göndermez → `None` → "—").
    """
    # 1 — Başlık yok: eski istemci; kilitleme. Başlıksız istekle kilidi
    # ATLAMAK abonelik paylaşan iki GÜNCEL cihaz için işe yaramaz: ikisi de
    # başlık gönderir.
    if device_id is None or not device_id.strip():
        return

    # 2 — Yalnız ücretli abone (K3).
    if not _paid_subscriber(uid):
        return

    # 3 — Bilinmiyor: geçir, YAZMA (K5).
    kayit = _stored(uid)
    if kayit is _UNKNOWN:
        logger.warning("Cihaz kilidi atlandı, kayıt okunamadı: uid=%s", uid)
        return

    # 4 — Kayıt yok: memo "yok" diyorsa Firestore'a bir kez daha bak (başka
    # instance sahiplenmiş olabilir); hâlâ yoksa sessiz ilk sahiplenme.
    if kayit is None:
        kayit = _stored(uid, refresh=True)
        if kayit is _UNKNOWN:
            return
        if kayit is None:
            _claim(uid, device_id, auth_time=auth_time, platform=platform)
            return

    # 5 — Aynı cihaz: memo'dan geç.
    if kayit.device_id == device_id:
        return

    # 6 — Uyumsuz: memo'ya güvenme, Firestore'u yeniden oku (K4).
    kayit = _stored(uid, refresh=True)
    if kayit is _UNKNOWN:
        return
    if kayit is None:
        # Bu arada serbest bırakılmış (DELETE /claim / admin) — sahiplen.
        _claim(uid, device_id, auth_time=auth_time, platform=platform)
        return
    # 6a — Tazelenince eşit çıktı: bayat memo'ydu, sahte 409 yok.
    if kayit.device_id == device_id:
        return
    # 6b — Son giriş kazanır (K2): giriş, kaydın devralınmasından SONRAysa
    # bu cihaz devralır; eski cihaz bir sonraki isteğinde 409 alır.
    if float(auth_time or 0) > kayit.claimed_at:
        _claim(uid, device_id, auth_time=auth_time, platform=platform)
        logger.info("Cihaz otomatik devralındı: uid=%s", uid)
        return
    # 6c — Eski giriş: çakışma.
    raise _conflict(kayit, lang)


def claim_device(uid: str, device_id: str, *, auth_time: int,
                 platform: str | None) -> dict[str, Any]:
    """Cihazı AÇIKÇA devralır ("Bu cihazda kullan"). `claimed` dürüst:
    yazılamadıysa False — istemci kapıyı kapatmaz."""
    yazildi = _claim(uid, device_id, auth_time=auth_time, platform=platform)
    if yazildi:
        logger.info("Cihaz devralındı: uid=%s", uid)
    return {"claimed": yazildi}


def release_device(uid: str, device_id: str | None) -> dict[str, Any]:
    """Çıkışta serbest bırakma (K7): yalnız kayıt BU cihazınsa silinir.

    Başka cihazın kaydını silmek, eski cihazın çıkışıyla yeni cihazın
    kilidini düşürmek olurdu. Memo'ya değil Firestore'a bakılır.
    """
    if device_id is None or not device_id.strip():
        return {"released": False}
    kayit = _stored(uid, refresh=True)
    if not isinstance(kayit, Claim) or kayit.device_id != device_id:
        return {"released": False}
    ref = _device_ref(uid)
    if ref is None:
        return {"released": False}
    try:
        ref.delete()
    except Exception as exc:
        logger.warning("Cihaz kaydı silinemedi (%s): %s", uid, exc)
        return {"released": False}
    _forget(uid)
    logger.info("Cihaz serbest bırakıldı: uid=%s", uid)
    return {"released": True}


def force_release(uid: str) -> bool:
    """Yönetici kaçış kapısı (S2): kaydı cihazdan bağımsız siler, memo
    düşer. Diğer instance'ların memo'su en geç 60 sn'de düşer; uyumsuz
    istek zaten yeniden okuduğu için yeni cihaz beklemeden sahiplenir.
    Dönüş: silinecek kayıt var mıydı. Altyapı hatası fırlatılır — admin
    "sıfırlandı" sanmasın."""
    ref = _device_ref(uid)
    if ref is None:
        raise RuntimeError("Firestore erişilemiyor.")
    kayit = _stored(uid, refresh=True)
    ref.delete()
    _forget(uid)
    return isinstance(kayit, Claim)


def device_status(uid: str, device_id: str | None) -> dict[str, Any]:
    """Teşhis/ayarlar yüzeyi: kilit bu kullanıcıda etkin mi, kayıt kimde."""
    locked = _paid_subscriber(uid)
    kayit = _stored(uid)
    claimed = isinstance(kayit, Claim)
    this_device = claimed and kayit.device_id == device_id
    other = None
    if claimed and not this_device:
        other = {"platform": kayit.platform,
                 "claimedAt": _iso(kayit.claimed_at) or None}
    return {"locked": locked, "claimed": claimed,
            "this_device": this_device, "other": other}


def clear_cache() -> None:
    """Test yardımcı — süreç içi memo'yu boşaltır."""
    with _cache_lock:
        _cache.clear()
