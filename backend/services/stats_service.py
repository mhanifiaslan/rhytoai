"""Admin istatistik toplayıcısı (W5).

Gecelik `rytho-stats` Scheduler işi (ya da panelden elle tetikleme) tüm
sayımları BURADA yapar ve sonucu `adminStats/{YYYY-MM-DD}` dokümanına yazar;
panel hazır dokümanları okur. Böylece panel açılışında binlerce doküman
taranmaz — toplama gecenin sakin saatinde bir kez koşar.

KRİTİK KURAL: abonelik sayımı HAM Firestore dokümanından yapılır —
`entitlements.is_subscriber` ASLA kullanılmaz. O fonksiyon RYTHO_FORCE_PLUS=1
(test dönemi) iken herkese True döner ve istatistiği zehirler.

Desen emsalleri: sayfalı tarama api/notify.py `_iter_profiles`,
sonuç şeması `RunResult`.
"""
from __future__ import annotations

import datetime as dt
import logging
import time
from typing import Any

from core import app_gate, firestore as firestore_client

logger = logging.getLogger(__name__)

PAGE_SIZE = 500

#: Streak histogram kovaları — panel bu adlarla gösterir.
_STREAK_KOVALARI = ("0", "1-3", "4-7", "8+")


def _streak_kovasi(deger: int) -> str:
    if deger <= 0:
        return "0"
    if deger <= 3:
        return "1-3"
    if deger <= 7:
        return "4-7"
    return "8+"


def _count(sorgu) -> int:
    """Firestore count() aggregation — dokümanları taşımadan sayar.

    Kitaplık/emülatör desteklemiyorsa -1 döner; panel "-" gösterir.
    Sayım uğruna toplama işi düşürülmez.
    """
    try:
        sonuc = sorgu.count().get()
        return int(sonuc[0][0].value)
    except Exception as exc:
        logger.warning("count() basarisiz: %s", exc)
        return -1


def _iter_users(client):
    """Tüm kullanıcı dokümanlarını sayfalayarak dolaşır (notify emsali).

    Filtre YOK: onboarding'i bitirmemiş kullanıcı da sayılmalı (dönüşüm
    oranının paydası). PAGE_SIZE'lık sayfalar bellek güvenliği sağlar.
    """
    son = None
    while True:
        sorgu = (client.collection("users")
                 .order_by("__name__")
                 .limit(PAGE_SIZE))
        if son is not None:
            sorgu = sorgu.start_after({"__name__": son})
        sayfa = list(sorgu.stream())
        if not sayfa:
            return
        for anlik in sayfa:
            veri = anlik.to_dict() or {}
            veri["uid"] = anlik.id
            yield veri
        son = sayfa[-1].id
        if len(sayfa) < PAGE_SIZE:
            return


def _gun_araligi(tarih: dt.date) -> tuple[dt.datetime, dt.datetime]:
    baslangic = dt.datetime.combine(tarih, dt.time.min, tzinfo=dt.timezone.utc)
    return baslangic, baslangic + dt.timedelta(days=1)


def collect(tarih: dt.date | None = None) -> dict[str, Any]:
    """Günün istatistiklerini toplar ve `adminStats/{tarih}` dokümanına yazar.

    İdempotent: aynı gün için ikinci çalıştırma dokümanı ezer (toplamlar
    yeniden hesaplanır, birikmez). Dönen sözlük yazılanın aynısıdır.
    """
    client = firestore_client.get_client()
    if client is None:
        raise RuntimeError("Firestore erişilemiyor; istatistik toplanamadı.")

    from google.cloud.firestore_v1.base_query import FieldFilter

    tarih = tarih or dt.datetime.now(dt.timezone.utc).date()
    tarih_str = tarih.isoformat()
    baslangic = time.monotonic()
    simdi = dt.datetime.now(dt.timezone.utc)
    gun_bas, gun_son = _gun_araligi(tarih)

    # ---- Kullanıcı taraması: dağılımlar tek geçişte ----
    toplam = 0
    onboarded = 0
    bugun_yeni = 0
    dau = 0
    push = 0
    rehber_acik = 0
    seri_gorunur = 0
    streak_kovalar = {k: 0 for k in _STREAK_KOVALARI}
    dil: dict[str, int] = {}
    saat_dilimi: dict[str, int] = {}
    platformlar: dict[str, int] = {}
    surumler: dict[str, int] = {}
    surum_bilinmiyor = 0
    for veri in _iter_users(client):
        toplam += 1
        if veri.get("onboardingCompleted") is True:
            onboarded += 1
        olusturma = veri.get("createdAt")
        if olusturma is not None and hasattr(olusturma, "timestamp"):
            if gun_bas.timestamp() <= olusturma.timestamp() < gun_son.timestamp():
                bugun_yeni += 1
        if veri.get("lastSeenDaily") == tarih_str:
            dau += 1
        if veri.get("fcmToken"):
            push += 1
        if veri.get("contactMatch") is True:
            rehber_acik += 1
        if veri.get("streakVisible") is True:
            seri_gorunur += 1
        streak_kovalar[_streak_kovasi(
            int(veri.get("streakCount") or 0))] += 1
        d = str(veri.get("language") or "-")
        dil[d] = dil.get(d, 0) + 1
        tz = str(veri.get("timezone") or "-")
        saat_dilimi[tz] = saat_dilimi.get(tz, 0) + 1
        # Platform aynası (AP-turu, core/device._claim yazar); alanı
        # olmayan eski kullanıcılar dürüstçe "bilinmiyor".
        pf = str(veri.get("platform") or "bilinmiyor")
        platformlar[pf] = platformlar.get(pf, 0) + 1
        # Sürüm aynası (PBZ, core/auth.get_current_user yazar). Başlık
        # göndermeyen ≤34 istemciler alanı hiç taşımaz → "bilinmiyor";
        # panel bunu "eşiğin altında" sayısından AYRI gösterir.
        sb = app_gate.parse_build(veri.get("appBuild"))
        if sb > 0:
            surumler[str(sb)] = surumler.get(str(sb), 0) + 1
        else:
            surum_bilinmiyor += 1

    # ---- Sürüm kırılımı: eşiğin altında kaç kişi (PBZ) ----
    # Ayrı count() sorgusu YOK — yukarıdaki tek geçişten türetilir.
    surum_blok: dict[str, Any] = {"byBuild": {}, "min": -1,
                                  "belowMin": -1, "unknown": -1}
    try:
        esik = app_gate.current_min_build()
        surum_blok = {
            "byBuild": surumler,
            "min": esik,
            "belowMin": sum(n for b, n in surumler.items()
                            if int(b) < esik) if esik > 0 else 0,
            "unknown": surum_bilinmiyor,
        }
    except Exception as exc:
        logger.warning("Sürüm kırılımı hesaplanamadı: %s", exc)

    # ---- Abonelikler: HAM collection-group sorgusu (is_subscriber YASAK) ----
    aktif = 0
    urun: dict[str, int] = {}
    magaza: dict[str, int] = {}
    deneme = 0
    iptal_ama_aktif = 0
    try:
        abonelikler = (client.collection_group("private")
                       .where(filter=FieldFilter("active", "==", True))
                       .where(filter=FieldFilter("expiresAt", ">", simdi))
                       .stream())
        for anlik in abonelikler:
            veri = anlik.to_dict() or {}
            aktif += 1
            u = str(veri.get("productId") or "-")
            urun[u] = urun.get(u, 0) + 1
            m = str(veri.get("store") or "-")
            magaza[m] = magaza.get(m, 0) + 1
            if veri.get("isTrial") is True:
                deneme += 1
            if veri.get("willRenew") is False:
                iptal_ama_aktif += 1
    except Exception as exc:
        logger.warning("Abonelik sorgusu düştü (indeks?): %s", exc)
        aktif = -1

    # ---- Gelir: revenueEvents günlük filtre ----
    brut = 0.0
    para_birimi: dict[str, float] = {}
    paket_satis: dict[str, int] = {}
    iade = 0
    try:
        olaylar = (client.collection("revenueEvents")
                   .where(filter=FieldFilter("at", ">=", gun_bas))
                   .where(filter=FieldFilter("at", "<", gun_son))
                   .stream())
        for anlik in olaylar:
            veri = anlik.to_dict() or {}
            fiyat = float(veri.get("price") or 0)
            if veri.get("eventType") == "REFUND":
                iade += 1
                brut -= abs(fiyat)
            else:
                brut += fiyat
                pb = str(veri.get("currency") or "-")
                ham = float(veri.get("priceInPurchasedCurrency") or 0)
                para_birimi[pb] = para_birimi.get(pb, 0.0) + ham
                u = str(veri.get("productId") or "")
                if u.startswith("rytho_tokens_"):
                    paket_satis[u] = paket_satis.get(u, 0) + 1
    except Exception as exc:
        logger.warning("Gelir sorgusu düştü: %s", exc)
        brut = -1.0

    # ---- Jeton akışı: cüzdan defterinin gün dilimi (AP-turu) ----
    # collection_group("ledger") fieldOverride indeksi ister (infra/
    # firestore.indexes.json); indeks henüz kurulmadıysa sorgu düşer ve
    # mevcut duruşla boş/None yazılır — toplama işi düşmez.
    jeton_harcanan: dict[str, int] = {}
    jeton_harcanan_toplam = -1
    jeton_kredi_toplam = -1
    try:
        harcanan_toplam = 0
        kredi_toplam = 0
        for anlik in (client.collection_group("ledger")
                      .where(filter=FieldFilter("at", ">=", gun_bas))
                      .where(filter=FieldFilter("at", "<", gun_son))
                      .stream()):
            veri = anlik.to_dict() or {}
            adet = int(veri.get("amount") or 0)
            if veri.get("type") == "debit":
                harcanan_toplam += adet
                oz = str(veri.get("feature") or "unknown")
                jeton_harcanan[oz] = jeton_harcanan.get(oz, 0) + adet
            elif veri.get("type") in ("credit", "promo", "admin"):
                kredi_toplam += adet
        jeton_harcanan_toplam = harcanan_toplam
        jeton_kredi_toplam = kredi_toplam
    except Exception as exc:
        logger.warning("Ledger sorgusu düştü (indeks?): %s", exc)

    # ---- AI kullanımı: usageEvents gün eşitliği (AP-turu) ----
    ai_cagri = -1
    ai_maliyet = -1.0
    ai_ozellik: dict[str, int] = {}
    try:
        cagri = 0
        maliyet = 0.0
        for anlik in (client.collection("usageEvents")
                      .where(filter=FieldFilter("day", "==", tarih_str))
                      .stream()):
            veri = anlik.to_dict() or {}
            cagri += 1
            maliyet += float(veri.get("estCostUsd") or 0)
            oz = str(veri.get("feature") or "unknown")
            ai_ozellik[oz] = ai_ozellik.get(oz, 0) + 1
        ai_cagri = cagri
        ai_maliyet = round(maliyet, 6)
    except Exception as exc:
        logger.warning("usageEvents sorgusu düştü: %s", exc)

    # ---- Bildirim koşuları: notifyRuns {gün}-{tür} (AP-turu) ----
    bildirim: dict[str, Any] = {}
    try:
        for tur in ("daily", "midday", "checkin", "streak"):
            anlik = (client.collection("notifyRuns")
                     .document(f"{tarih_str}-{tur}").get())
            if getattr(anlik, "exists", False):
                veri = anlik.to_dict() or {}
                bildirim[tur] = {
                    "sent": int(veri.get("sent") or 0),
                    "failed": int(veri.get("failed") or 0),
                    "skippedTotal": sum(
                        int(v or 0)
                        for v in (veri.get("skipped") or {}).values()),
                }
    except Exception as exc:
        logger.warning("notifyRuns okunamadı: %s", exc)

    # ---- Hafif sayımlar: count() aggregation ----
    arkadaslik = _count(
        client.collection_group("friends")
        .where(filter=FieldFilter("status", "==", "accepted")))
    if arkadaslik > 0:
        arkadaslik //= 2  # çift taraflı yazım — tek ilişki iki doküman
    sikayet = _count(client.collection("reports"))
    onbellek = _count(client.collection("aiCache"))
    konusma = _count(client.collection_group("conversations"))
    kullanici_adi = _count(client.collection("usernames"))

    dokuman = {
        "date": tarih_str,
        "generatedAt": simdi,
        "durationMs": int((time.monotonic() - baslangic) * 1000),
        "users": {
            "total": toplam,
            "onboarded": onboarded,
            "newToday": bugun_yeni,
            "dau": dau,
            "push": push,
            "contactMatchOn": rehber_acik,
            "streakVisibleOn": seri_gorunur,
            "usernames": kullanici_adi,
            "streakBuckets": streak_kovalar,
            "byLanguage": dil,
            "byTimezone": saat_dilimi,
            "byPlatform": platformlar,
        },
        "subs": {
            "active": aktif,
            "byProduct": urun,
            "byStore": magaza,
            "trial": deneme,
            "cancelledButActive": iptal_ama_aktif,
        },
        "revenue": {
            "grossToday": round(brut, 2),
            "byCurrency": {k: round(v, 2) for k, v in para_birimi.items()},
            "packSalesToday": paket_satis,
            "refundsToday": iade,
        },
        "social": {
            "friendships": arkadaslik,
            "reportsOpen": sikayet,
        },
        "system": {
            "aiCacheCount": onbellek,
            "conversationsCount": konusma,
        },
        # AP-turu ekleri. Eski dokümanlarda bu anahtarlar yok; panel
        # yokluğu "—" gösterir (geriye uyum sözleşmesi).
        "tokens": {
            "spentToday": jeton_harcanan,
            "spentTotalToday": jeton_harcanan_toplam,
            "creditedToday": jeton_kredi_toplam,
        },
        "ai": {
            "callsToday": ai_cagri,
            "estCostToday": ai_maliyet,
            "byFeature": ai_ozellik,
        },
        "notify": bildirim,
        # PBZ: zorunlu güncelleme paneli. Eski dokümanlarda yok → "—".
        "builds": surum_blok,
    }

    client.collection("adminStats").document(tarih_str).set(dokuman)
    logger.info("adminStats/%s yazıldı (%d kullanıcı, %d ms)",
                tarih_str, toplam, dokuman["durationMs"])
    return dokuman


def read_days(days: int) -> list[dict[str, Any]]:
    """Son N günün hazır istatistik dokümanları (yeniden eskiye).

    Sıralama `date` ALANINA göre — doküman kimliğiyle aynı değer ama
    `__name__` üzerinden azalan sıralama otomatik indekslenmiyor
    (üretimde 400 FailedPrecondition olarak ölçüldü, AP2); tek-alan
    otomatik indeks ise her iki yönü de kapsar.
    """
    client = firestore_client.get_client()
    if client is None:
        return []
    sorgu = (client.collection("adminStats")
             .order_by("date", direction="DESCENDING")
             .limit(max(1, min(days, 365))))
    return [anlik.to_dict() or {} for anlik in sorgu.stream()]
