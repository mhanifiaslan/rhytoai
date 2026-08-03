"""Tek cihaz kilidi — YALNIZCA aboneler için.

## Neden var

Ürün kararı: bir abonelik tek cihazdan kullanılır. Hesap paylaşımı,
kullanıcı başına LLM maliyeti olan bir üründe doğrudan zarar kalemidir —
beş kişinin paylaştığı tek abonelik, beş kullanıcının maliyetine tek
abonelik geliri demek.

## Nasıl çalışır (WhatsApp modeli)

İstemci her isteğe rastgele üretilmiş `X-Device-Id` başlığı ekler. Aboneli
uçlarda başlıktaki kimlik `users/{uid}/private/device` dokümanıyla
karşılaştırılır:

* Doküman yok → sessiz ilk sahiplenme (kullanıcıya sorulmaz; ilk cihaz
  zaten "onun cihazı").
* Kimlik eşleşiyor → geç.
* Eşleşmiyor → **409** + ``X-Device-Conflict: 1``. İstemci bunu görünce
  oturumu kapatır ve "başka cihazda kullanılıyor" ekranına düşer; kullanıcı
  isterse `POST /device/claim` ile cihazı devralır, ESKİ cihaz bir sonraki
  isteğinde 409 alır. Son devralan kazanır; yarış 409'la yakınsar.

## Bilinçli sınırlar

* **Ücretsiz kullanıcı hiç etkilenmez** — gereksinim "aboneler" diyor ve
  ücretsiz katmanda korunacak birim maliyet zaten yok.
* **Başlık yoksa geç**: eski uygulama sürümleri kimlik göndermez; onları
  kilitlemek, güncelleme yayılana kadar tüm aboneleri kırmak olurdu.
* **`get_current_user`'a DOKUNULMAZ**: kilit yalnızca abonelik gerektiren
  yollarda. Her isteğe Firestore okuması bindirmek, auth katmanının "hızlı
  kal" değişmeziyle çelişirdi; ayrıca süreç içi 60 sn'lik önbellek aynı
  kullanıcının ardışık isteklerinde okumayı zaten sıfırlıyor. Bedeli:
  devralma eski cihaza instance başına en geç 60 sn'de yansır — kabul
  edilebilir, para kaybı değil gecikme.
"""
from __future__ import annotations

import datetime as dt
import logging
import threading
import time
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

#: Süreç içi önbellek ömrü. Devralmanın eski cihaza yansıma gecikmesi de bu.
_CACHE_TTL_SECONDS = 60.0

_cache: dict[str, tuple[str | None, float]] = {}
_cache_lock = threading.Lock()


def _device_ref(uid: str):
    client = firestore_client.get_client()
    if client is None:
        return None
    return (client.collection("users").document(uid)
            .collection("private").document("device"))


def _cached_device_id(uid: str) -> tuple[bool, str | None]:
    """(önbellekte var mı, kimlik). Kilit altında tek sözlük erişimi."""
    with _cache_lock:
        kayit = _cache.get(uid)
    if kayit is None:
        return False, None
    device_id, yazilma = kayit
    if time.monotonic() - yazilma > _CACHE_TTL_SECONDS:
        return False, None
    return True, device_id


def _remember(uid: str, device_id: str | None) -> None:
    with _cache_lock:
        _cache[uid] = (device_id, time.monotonic())
        # Sınırsız büyüme yok: kaba bir kapak yeter, LRU şart değil.
        if len(_cache) > 10000:
            _cache.clear()


def _stored_device_id(uid: str) -> str | None:
    """Kayıtlı cihaz kimliği; önbellekten, gerekirse Firestore'dan."""
    var, device_id = _cached_device_id(uid)
    if var:
        return device_id

    ref = _device_ref(uid)
    if ref is None:
        return None
    try:
        snapshot = ref.get()
        data = (snapshot.to_dict() or {}) if snapshot.exists else {}
        device_id = data.get("deviceId")
    except Exception as exc:
        logger.warning("Cihaz kaydı okunamadı (%s): %s", uid, exc)
        return None

    _remember(uid, device_id)
    return device_id


def _claim(uid: str, device_id: str, platform: str | None = None) -> None:
    ref = _device_ref(uid)
    if ref is None:
        return
    ref.set({
        "deviceId": device_id,
        "platform": platform,
        "claimedAt": dt.datetime.now(dt.timezone.utc),
        "lastSeenAt": dt.datetime.now(dt.timezone.utc),
    })
    _remember(uid, device_id)


def enforce_single_device(uid: str, device_id: str | None,
                          lang: str = DEFAULT_LANG) -> None:
    """Abonenin isteğini kayıtlı cihazla karşılaştırır.

    Sıralama maliyet için önemli: abonelik kontrolü önce — ücretsiz
    kullanıcıda ne Firestore okuması ne başka iş yapılır.
    """
    if device_id is None or not device_id.strip():
        # Eski istemci; kilitleme. Yeni sürüm yayılınca herkes gönderiyor
        # olacak. Başlıksız istekle kilidi ATLAMAK abonelik paylaşan iki
        # GÜNCEL cihaz için işe yaramaz: ikisi de başlık gönderir.
        return

    if not entitlements.is_subscriber(uid):
        return

    kayitli = _stored_device_id(uid)
    if kayitli is None:
        # İlk cihaz: sessiz sahiplenme.
        _claim(uid, device_id)
        return

    if kayitli == device_id:
        return

    raise HTTPException(
        status_code=DEVICE_CONFLICT_STATUS,
        detail=text("device.conflict", lang),
        headers={"X-Device-Conflict": "1"},
    )


def claim_device(uid: str, device_id: str,
                 platform: str | None = None) -> dict[str, Any]:
    """Cihazı AÇIKÇA devralır (kullanıcı onayından sonra çağrılır)."""
    _claim(uid, device_id, platform)
    logger.info("Cihaz devralındı: uid=%s", uid)
    return {"claimed": True}


def device_status(uid: str, device_id: str | None) -> dict[str, Any]:
    """Giriş akışının 'devralma onayı gösterilsin mi' sorusuna cevap."""
    kayitli = _stored_device_id(uid)
    return {
        "claimed": kayitli is not None,
        "this_device": kayitli is not None and kayitli == device_id,
    }


def clear_cache() -> None:
    """Test yardımcı — süreç içi önbelleği boşaltır."""
    with _cache_lock:
        _cache.clear()
