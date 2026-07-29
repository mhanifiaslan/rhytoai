"""Kullanıcı profili okuma — sunucu tarafı.

Arkadaş katmanının gizlilik kuralı şudur: **bir kullanıcının ham doğum verisi
(tarih, saat, şehir) hiçbir zaman başka bir istemciye gönderilmez.** Doğum
tarihi + saati + yeri kimlik doğrulama sorularında kullanılan hassas bir
üçlüdür; yalnızca ondan türetilen yorum paylaşılır.

Bu yüzden ikili (dyad) okuma istemciden iki doğum verisi almaz; istemci sadece
arkadaşın kimliğini gönderir ve sunucu her iki profili buradan okur.
"""
from __future__ import annotations

import logging
from typing import Any

from core import firestore as firestore_client

logger = logging.getLogger(__name__)

_DEFAULT_DATE = "2000-01-01"
_DEFAULT_TIME = "12:00"


def _user_doc(uid: str):
    client = firestore_client.get_client()
    if client is None:
        return None
    return client.collection("users").document(uid)


def get_profile(uid: str) -> dict[str, Any] | None:
    """Kullanıcının Firestore profilini döndürür; yoksa ``None``."""
    doc_ref = _user_doc(uid)
    if doc_ref is None:
        return None
    try:
        snapshot = doc_ref.get()
    except Exception as exc:
        logger.warning("Profil okunamadı (%s): %s", uid, exc)
        return None
    return snapshot.to_dict() if snapshot.exists else None


def birth_kwargs(profile: dict[str, Any]) -> dict[str, Any]:
    """Firestore profilini astro_service'in beklediği doğum verisine çevirir.

    İstemcideki `birthPayload` (apps/mobile/lib/core/api.dart) ile aynı
    dönüşümdür; alanlar eksikse aynı varsayılanlara düşer.
    """
    birth_date = profile.get("birthDate") or _DEFAULT_DATE
    birth_time = profile.get("birthTime") or _DEFAULT_TIME
    try:
        year, month, day = (int(p) for p in birth_date.split("-"))
        hour, minute = (int(p) for p in birth_time.split(":")[:2])
    except (ValueError, AttributeError):
        year, month, day = (int(p) for p in _DEFAULT_DATE.split("-"))
        hour, minute = 12, 0

    return {
        "name": profile.get("displayName") or "Gezgin",
        "year": year, "month": month, "day": day,
        "hour": hour, "minute": minute,
        "city": profile.get("birthCity") or "Istanbul",
        "nation": profile.get("birthNation"),
    }


def chart_summary(profile: dict[str, Any] | None) -> str:
    """Sohbete iliştirilecek kompakt harita özeti.

    Sohbet ucu daha önce bu bilgiyi HİÇ almıyordu: istemci yalnızca mesaj ve
    geçmiş gönderiyor, persona da "doğum bilgisi sohbette geçiyorsa dokundur"
    diyordu. Sonuç olarak Rytho, kullanıcı kendi burcunu söylemediği sürece
    haritasından habersiz konuşuyordu — kişiselleştirmenin en temel parçası
    eksikti.

    Ham doğum verisi (tarih/saat/şehir) BURAYA GİRMEZ; yalnızca ondan
    türetilmiş konumlar. Modelin doğum tarihini bilmesine gerek yok.
    """
    if not profile:
        return ""

    satirlar = []
    ucler = [
        ("Güneş", profile.get("sunSign")),
        ("Ay", profile.get("moonSign")),
        ("Yükselen", profile.get("ascendant")),
    ]
    buyuk_uclu = ", ".join(f"{ad}: {deger}" for ad, deger in ucler if deger)
    if buyuk_uclu:
        satirlar.append(f"- {buyuk_uclu}")

    if profile.get("wuXingElement"):
        satirlar.append(f"- Wu Xing elementi: {profile['wuXingElement']}")
    if profile.get("mizac"):
        satirlar.append(f"- Mizaç (Ahlat-ı Erbaa): {profile['mizac']}")

    return "\n".join(satirlar)


def are_friends(uid: str, other_uid: str) -> bool:
    """İki kullanıcı arasında **kabul edilmiş** arkadaşlık var mı?

    İkili okuma pahalı (LLM) ve kişiseldir; arkadaş olmayan biri hakkında
    üretilmesi hem bütçe hem gizlilik açığıdır. Bu yüzden uç bunu doğrular.
    """
    doc_ref = _user_doc(uid)
    if doc_ref is None:
        return False
    try:
        snapshot = doc_ref.collection("friends").document(other_uid).get()
    except Exception as exc:
        logger.warning("Arkadaşlık doğrulanamadı (%s-%s): %s", uid, other_uid, exc)
        return False
    if not snapshot.exists:
        return False
    return (snapshot.to_dict() or {}).get("status") == "accepted"
