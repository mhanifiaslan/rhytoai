"""Admin paneli veri servisi (AP-turu) — kullanıcı listesi, Kullanıcı 360,
kullanım/bildirim/denetim okumaları.

Toplama mantığı burada, uçlar (api/admin.py) ince kalır — partner_service
emsali. Her fonksiyon Admin SDK ile okur (kurallar atlanır; istemci bu
koleksiyonlara zaten tamamen kapalı).

## Mahremiyet çizgisi (Kullanıcı 360)

Sayılar evet, İÇERİK hayır: sohbet mesajları, hafıza olguları ve günlük
metinleri bu servisten ASLA dönmez — yalnız adetleri döner. `fcmToken`
değeri de dönmez (`hasPush` bool'a iner): panelin işine token değil
"push alabiliyor mu" yarar ve token bir yetenek anahtarıdır.
"""
from __future__ import annotations

import datetime as dt
import logging
from typing import Any

from core import firestore as firestore_client
from core import wallet
from services.stats_service import _count, _iter_users

logger = logging.getLogger(__name__)

#: Liste satırına giren profil alanları — ham doğum saati/dakikası gibi
#: alanlar listede gereksiz; 360 detayında profil zaten tam döner.
_LIST_FIELDS = ("displayName", "email", "username", "sunSign", "createdAt",
                "lastSeenDaily", "streakCount", "language", "timezone",
                "platform", "onboardingCompleted")

_SORT_FIELDS = {"createdAt", "lastSeenDaily", "streakCount"}


def _client():
    client = firestore_client.get_client()
    if client is None:
        raise RuntimeError("Firestore erişilemiyor.")
    return client


def _ts(value: Any) -> float:
    try:
        return value.timestamp()
    except AttributeError:
        return float(value or 0) if isinstance(value, (int, float)) else 0.0


def list_users(query: str = "", sort: str = "createdAt",
               limit: int = 50) -> list[dict[str, Any]]:
    """Kullanıcı listesi: tam tarama + bellekte önek süzgeci.

    Bu ölçekte (onlarca kullanıcı) doğru araç budur; binlere çıkınca
    Firestore sorgu/indeks katmanı buraya eklenir — sözleşme (parametreler)
    o güne hazır.
    """
    client = _client()
    sort = sort if sort in _SORT_FIELDS else "createdAt"
    q = (query or "").strip().lower()

    satirlar: list[dict[str, Any]] = []
    for veri in _iter_users(client):
        if q:
            aday = " ".join(str(veri.get(alan) or "").lower()
                            for alan in ("email", "username", "displayName"))
            if not any(parca.startswith(q) for parca in aday.split()):
                continue
        satir = {alan: veri.get(alan) for alan in _LIST_FIELDS}
        satir["uid"] = veri["uid"]
        satir["hasPush"] = bool(veri.get("fcmToken"))
        satirlar.append(satir)

    satirlar.sort(key=lambda s: _ts(s.get(sort)), reverse=True)
    return satirlar[:limit]


def _private_doc(client, uid: str, ad: str) -> dict[str, Any]:
    try:
        anlik = (client.collection("users").document(uid)
                 .collection("private").document(ad).get())
        return (anlik.to_dict() or {}) if getattr(anlik, "exists", False) else {}
    except Exception as exc:
        logger.warning("private/%s okunamadı (%s): %s", ad, uid, exc)
        return {}


def user_360(uid: str) -> dict[str, Any] | None:
    """Tek kullanıcının destek görünümü; kullanıcı yoksa None."""
    client = _client()

    anlik = client.collection("users").document(uid).get()
    if not getattr(anlik, "exists", False):
        return None
    profil = anlik.to_dict() or {}
    profil["uid"] = uid
    profil["hasPush"] = bool(profil.pop("fcmToken", None))

    # Kimlik tarafı bayrağı (AP2): devre dışı hesap panelde görünür olmalı.
    try:
        from firebase_admin import auth as fb_auth
        profil["authDisabled"] = bool(fb_auth.get_user(uid).disabled)
    except Exception:
        profil["authDisabled"] = None  # okunamadı — panel "?" gösterir

    subscription = _private_doc(client, uid, "subscription")
    quota = _private_doc(client, uid, "quota")
    attribution = _private_doc(client, uid, "attribution")

    device_ham = _private_doc(client, uid, "device")
    device = {k: device_ham.get(k)
              for k in ("platform", "claimedAt", "lastSeenAt")}

    # Bildirim META'sı: gövde/soru metinleri (dailyBody vb.) DÖNMEZ.
    notif_ham = _private_doc(client, uid, "notifications")
    notifications = {k: v for k, v in notif_ham.items()
                     if k.endswith("LastSent") or k == "dailyTheme"}

    cuzdan = wallet.get_wallet(uid)

    ledger: list[dict[str, Any]] = []
    try:
        sorgu = (client.collection("users").document(uid)
                 .collection("private").document("wallet")
                 .collection("ledger")
                 .order_by("at", direction="DESCENDING").limit(50))
        for kayit in sorgu.stream():
            veri = kayit.to_dict() or {}
            veri["id"] = kayit.id
            ledger.append(veri)
    except Exception as exc:
        logger.warning("Ledger okunamadı (%s): %s", uid, exc)

    gelir: list[dict[str, Any]] = []
    try:
        from google.cloud.firestore_v1.base_query import FieldFilter
        for kayit in (client.collection("revenueEvents")
                      .where(filter=FieldFilter("uid", "==", uid)).stream()):
            veri = kayit.to_dict() or {}
            veri["id"] = kayit.id
            gelir.append(veri)
        gelir.sort(key=lambda v: _ts(v.get("at")), reverse=True)
    except Exception as exc:
        logger.warning("revenueEvents okunamadı (%s): %s", uid, exc)

    kullanim: list[dict[str, Any]] = []
    kullanim_toplam = {"calls": 0, "estCostUsd": 0.0,
                       "byFeature": {}}  # type: dict[str, Any]
    try:
        from google.cloud.firestore_v1.base_query import FieldFilter
        sorgu = (client.collection("usageEvents")
                 .where(filter=FieldFilter("uid", "==", uid))
                 .order_by("at", direction="DESCENDING").limit(50))
        for kayit in sorgu.stream():
            veri = kayit.to_dict() or {}
            kullanim.append(veri)
            kullanim_toplam["calls"] += 1
            kullanim_toplam["estCostUsd"] = round(
                kullanim_toplam["estCostUsd"]
                + float(veri.get("estCostUsd") or 0), 6)
            oz = str(veri.get("feature") or "unknown")
            kullanim_toplam["byFeature"][oz] = (
                kullanim_toplam["byFeature"].get(oz, 0) + 1)
    except Exception as exc:
        # Composite indeks henüz kurulmadıysa buraya düşer — 360 düşmez.
        logger.warning("usageEvents okunamadı (%s): %s", uid, exc)

    sayilar = {
        "conversations": _count(client.collection("users").document(uid)
                                .collection("conversations")),
        "friends": -1,
    }
    try:
        from google.cloud.firestore_v1.base_query import FieldFilter
        sayilar["friends"] = _count(
            client.collection("users").document(uid).collection("friends")
            .where(filter=FieldFilter("status", "==", "accepted")))
    except Exception:
        pass

    # Kullanıcı ekonomisi (AP2): son 50 kaydın DEĞİL tamamının toplamları.
    toplam_maliyet = 0.0
    toplam_cagri = 0
    try:
        from google.cloud.firestore_v1.base_query import FieldFilter
        for kayit in (client.collection("usageEvents")
                      .where(filter=FieldFilter("uid", "==", uid)).stream()):
            veri = kayit.to_dict() or {}
            toplam_maliyet += float(veri.get("estCostUsd") or 0)
            toplam_cagri += 1
    except Exception as exc:
        logger.warning("Kullanım toplamı okunamadı (%s): %s", uid, exc)
    toplam_gelir = sum(
        (-abs(float(o.get("price") or 0))
         if o.get("eventType") == "REFUND"
         else float(o.get("price") or 0)) for o in gelir)
    ekonomi = {
        "revenueUsd": round(toplam_gelir, 2),
        "aiCostUsd": round(toplam_maliyet, 4),
        "calls": toplam_cagri,
        "marginUsd": round(toplam_gelir * (1 - STORE_CUT)
                           - toplam_maliyet, 4),
        "storeCutRate": STORE_CUT,
    }

    return {
        "profile": profil,
        "subscription": subscription,
        "wallet": cuzdan,
        "ledger": ledger,
        "quota": quota,
        "attribution": attribution,
        "device": device,
        "notifications": notifications,
        "revenueEvents": gelir,
        "usage": {"recent": kullanim, **kullanim_toplam},
        "economics": ekonomi,
        "counts": sayilar,
    }


#: Mağaza kesintisi tahmini (Play/App Store standart %15 küçük işletme
#: oranı). Panelde her yerde "tahmini" etiketiyle sunulur — gerçek
#: hakediş mağaza raporundan gelir.
STORE_CUT = 0.15


def economics(days: int = 90) -> dict[str, Any]:
    """Kullanıcı bazlı gelir/maliyet/marj tablosu + toplamlar (AP2).

    Kâr formülü TAHMİNİDİR ve dürüstçe etiketlenir:
    marj = gelir × (1 − mağaza kesintisi) − tahmini AI maliyeti.
    Sabit giderler (Cloud Run vb.) kullanıcıya bölünmez — toplam satırında
    ayrıca gösterilir diye maliyet-calismasi.md §4'e işaret edilir.

    Ölçek: tam koleksiyon taramaları — bugünkü boyutta (onlarca kullanıcı,
    yüzlerce olay) doğru araç; binlere çıkınca gün-özetli rollup gerekir.
    """
    client = _client()
    from google.cloud.firestore_v1.base_query import FieldFilter

    baslangic = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)

    gelir: dict[str, float] = {}
    for kayit in (client.collection("revenueEvents")
                  .where(filter=FieldFilter("at", ">=", baslangic)).stream()):
        veri = kayit.to_dict() or {}
        uid = str(veri.get("uid") or "")
        if not uid:
            continue
        fiyat = float(veri.get("price") or 0)
        if veri.get("eventType") == "REFUND":
            fiyat = -abs(fiyat)
        gelir[uid] = round(gelir.get(uid, 0.0) + fiyat, 4)

    maliyet: dict[str, float] = {}
    cagri: dict[str, int] = {}
    for kayit in (client.collection("usageEvents")
                  .where(filter=FieldFilter("at", ">=", baslangic)).stream()):
        veri = kayit.to_dict() or {}
        uid = str(veri.get("uid") or "") or "(paylaşımlı)"
        maliyet[uid] = round(maliyet.get(uid, 0.0)
                             + float(veri.get("estCostUsd") or 0), 6)
        cagri[uid] = cagri.get(uid, 0) + 1

    jeton: dict[str, int] = {}
    try:
        for kayit in (client.collection_group("ledger")
                      .where(filter=FieldFilter("at", ">=", baslangic))
                      .stream()):
            veri = kayit.to_dict() or {}
            if veri.get("type") != "debit":
                continue
            parcalar = kayit.reference.path.split("/")
            uid = parcalar[1] if len(parcalar) > 1 else ""
            if uid:
                jeton[uid] = jeton.get(uid, 0) + int(veri.get("amount") or 0)
    except Exception as exc:
        logger.warning("Ledger taraması düştü (indeks?): %s", exc)

    satirlar: list[dict[str, Any]] = []
    for veri in _iter_users(client):
        uid = veri["uid"]
        g = gelir.get(uid, 0.0)
        m = maliyet.get(uid, 0.0)
        satirlar.append({
            "uid": uid,
            "displayName": veri.get("displayName"),
            "email": veri.get("email"),
            "revenueUsd": round(g, 2),
            "storeCutUsd": round(g * STORE_CUT, 2) if g > 0 else 0.0,
            "aiCostUsd": round(m, 4),
            "calls": cagri.get(uid, 0),
            "tokensSpent": jeton.get(uid, 0),
            "marginUsd": round(g * (1 - STORE_CUT) - m, 4),
        })
    satirlar.sort(key=lambda s: s["marginUsd"], reverse=True)

    toplam_gelir = round(sum(gelir.values()), 2)
    toplam_maliyet = round(sum(maliyet.values()), 4)
    paylasimli = round(maliyet.get("(paylaşımlı)", 0.0), 4)
    return {
        "days": days,
        "users": satirlar,
        "totals": {
            "revenueUsd": toplam_gelir,
            "storeCutUsd": round(max(toplam_gelir, 0) * STORE_CUT, 2),
            "aiCostUsd": toplam_maliyet,
            "sharedAiCostUsd": paylasimli,
            "marginUsd": round(toplam_gelir * (1 - STORE_CUT)
                               - toplam_maliyet, 4),
            "storeCutRate": STORE_CUT,
        },
    }


def usage_summary(days: int = 30) -> dict[str, Any]:
    """usageEvents'in gün/özellik/model kırılımı (AI sekmesi)."""
    client = _client()
    from google.cloud.firestore_v1.base_query import FieldFilter

    baslangic = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)
    by_day: dict[str, dict[str, Any]] = {}
    by_feature: dict[str, dict[str, Any]] = {}
    by_model: dict[str, dict[str, Any]] = {}
    toplam = {"calls": 0, "estCostUsd": 0.0,
              "promptTokens": 0, "outputTokens": 0, "thinkingTokens": 0}

    def _ekle(kova: dict[str, dict[str, Any]], anahtar: str,
              maliyet: float, prompt_t: int, output_t: int) -> None:
        satir = kova.setdefault(anahtar, {"calls": 0, "estCostUsd": 0.0,
                                          "promptTokens": 0,
                                          "outputTokens": 0})
        satir["calls"] += 1
        satir["estCostUsd"] = round(satir["estCostUsd"] + maliyet, 6)
        satir["promptTokens"] += prompt_t
        satir["outputTokens"] += output_t

    for kayit in (client.collection("usageEvents")
                  .where(filter=FieldFilter("at", ">=", baslangic)).stream()):
        veri = kayit.to_dict() or {}
        maliyet = float(veri.get("estCostUsd") or 0)
        prompt_t = int(veri.get("promptTokens") or 0)
        output_t = int(veri.get("outputTokens") or 0)
        thinking_t = int(veri.get("thinkingTokens") or 0)

        toplam["calls"] += 1
        toplam["estCostUsd"] = round(toplam["estCostUsd"] + maliyet, 6)
        toplam["promptTokens"] += prompt_t
        toplam["outputTokens"] += output_t
        toplam["thinkingTokens"] += thinking_t

        _ekle(by_day, str(veri.get("day") or "-"), maliyet, prompt_t, output_t)
        _ekle(by_feature, str(veri.get("feature") or "unknown"),
              maliyet, prompt_t, output_t)
        _ekle(by_model, str(veri.get("model") or "-"),
              maliyet, prompt_t, output_t)

    return {"days": days, "byDay": by_day, "byFeature": by_feature,
            "byModel": by_model, "totals": toplam,
            # Panel jeton bedellerini buradan gösterir — sunucu gerçeği,
            # panel hiçbir bedeli hardcode etmez.
            "costs": dict(wallet.TOKEN_COSTS)}


def notify_runs(days: int = 7) -> list[dict[str, Any]]:
    """notifyRuns dokümanları — kimlik `{gün}-{tür}` olduğu için ada göre
    tersten sıralama gün sırasıdır; indeks gerekmez (adminStats emsali)."""
    client = _client()
    kayitlar: list[dict[str, Any]] = []
    try:
        sorgu = (client.collection("notifyRuns")
                 .order_by("__name__", direction="DESCENDING")
                 .limit(days * 4 + 8))
        for anlik in sorgu.stream():
            veri = anlik.to_dict() or {}
            veri["id"] = anlik.id
            kayitlar.append(veri)
    except Exception as exc:
        logger.warning("notifyRuns okunamadı: %s", exc)
    return kayitlar


def audit_list(limit: int = 50) -> list[dict[str, Any]]:
    client = _client()
    kayitlar: list[dict[str, Any]] = []
    try:
        sorgu = (client.collection("adminAudit")
                 .order_by("at", direction="DESCENDING").limit(limit))
        for anlik in sorgu.stream():
            veri = anlik.to_dict() or {}
            veri["id"] = anlik.id
            kayitlar.append(veri)
    except Exception as exc:
        logger.warning("adminAudit okunamadı: %s", exc)
    return kayitlar
