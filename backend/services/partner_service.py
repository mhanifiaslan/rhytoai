"""Ortak (affiliate) kod sistemi (W7).

Veri modeli (yalnız Admin SDK yazar/okur; Firestore kurallarında eşleşmeyen
yol varsayılan kapalı — kural değişikliği gerekmez):

    partners/{partnerId}:  name, contact, sharePercent, active, createdAt, notes
    partnerCodes/{KOD}:    partnerId, bonusTokens, maxRedemptions,
                           redemptionCount, expiresAt, active, createdAt
    users/{uid}/private/attribution: code, partnerId, at   (TEK sefer)
    partners/{id}/payouts/{n}: amount, currency, at, note

DÜRÜST MODEL: mağaza fiyatı koddan değiştirilemez — kodun kullanıcıya
faydası jeton bonusudur; ortağa faydası, koddan SONRAKİ satın almaların
gelirine atıftır. Kod satın almadan önce girilmiş olmalı; sonradan girilen
kod geçmiş geliri atfetmez.

Benzersizlik deseni: doküman kimliği = BÜYÜK HARF kod (usernames emsali).
"""
from __future__ import annotations

import datetime as dt
import logging
import re
import secrets
import string
from typing import Any

from core import firestore as firestore_client
from core import wallet

logger = logging.getLogger(__name__)

#: Kod biçimi: 4-24 karakter, harf/rakam/altçizgi/tire. Küçük girilse de
#: BÜYÜK saklanır ve aranır.
_KOD_DESENI = re.compile(r"^[A-Z0-9_-]{4,24}$")


class RedeemError(Exception):
    """Kod kullanım hatası; `status` HTTP koduna eşlenir."""

    def __init__(self, status: int, reason: str):
        super().__init__(reason)
        self.status = status
        self.reason = reason


def normalize_code(code: str) -> str:
    kod = (code or "").strip().upper()
    if not _KOD_DESENI.match(kod):
        raise RedeemError(400, "invalid_format")
    return kod


def generate_code(prefix: str = "") -> str:
    """Panel için rastgele kod: OKUNAKLI alfabe (0/O, 1/I karışmaz)."""
    alfabe = "".join(c for c in string.ascii_uppercase + string.digits
                     if c not in "01OIL")
    govde = "".join(secrets.choice(alfabe) for _ in range(8))
    kod = f"{prefix.strip().upper()}{govde}" if prefix else govde
    return normalize_code(kod)


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def redeem(uid: str, raw_code: str) -> dict[str, Any]:
    """Kodu kullanır: atıf yazar + bonus jetonu yükler.

    Transaction içinde: (a) kod aktif + süresi geçmemiş + limiti dolmamış,
    (b) kullanıcının attribution'ı YOK (tek sefer — varsa 409),
    (c) sayaç artar, atıf yazılır. Bonus, transaction başarıyla bittikten
    sonra cüzdana yüklenir (kendi defter kimliğiyle idempotent).
    """
    kod = normalize_code(raw_code)
    client = firestore_client.get_client()
    if client is None:
        raise RedeemError(500, "unavailable")

    kod_ref = client.collection("partnerCodes").document(kod)
    atif_ref = (client.collection("users").document(uid)
                .collection("private").document("attribution"))

    from google.cloud import firestore as gcf

    transaction = client.transaction()

    @gcf.transactional
    def _run(txn) -> dict[str, Any]:
        kod_anlik = kod_ref.get(transaction=txn)
        if not kod_anlik.exists:
            raise RedeemError(404, "not_found")
        veri = kod_anlik.to_dict() or {}
        if veri.get("active") is not True:
            raise RedeemError(400, "inactive")
        son = veri.get("expiresAt")
        if son is not None and hasattr(son, "timestamp") \
                and son.timestamp() < _now().timestamp():
            raise RedeemError(400, "expired")
        limit = veri.get("maxRedemptions")
        sayac = int(veri.get("redemptionCount") or 0)
        if limit is not None and sayac >= int(limit):
            raise RedeemError(400, "exhausted")

        atif_anlik = atif_ref.get(transaction=txn)
        if atif_anlik.exists:
            # Tek sefer: kullanıcı ikinci bir kod kullanamaz — atıf
            # sonradan değiştirilemesin (ortaklar arası çekişme kapısı).
            raise RedeemError(409, "already_redeemed")

        txn.update(kod_ref, {"redemptionCount": sayac + 1})
        txn.set(atif_ref, {"code": kod,
                           "partnerId": veri.get("partnerId"),
                           "at": _now()})
        return {"code": kod,
                "partnerId": veri.get("partnerId"),
                "bonusTokens": int(veri.get("bonusTokens") or 0)}

    sonuc = _run(transaction)

    bonus = sonuc["bonusTokens"]
    if bonus > 0:
        wallet.credit_promo(uid, kod, bonus)

    logger.info("Kod kullanıldı: uid=%s kod=%s ortak=%s bonus=%d",
                uid, kod, sonuc["partnerId"], bonus)
    return sonuc


# ---------------------------------------------------------------------------
# Panel CRUD yardımcıları (admin.py çağırır; hepsi Admin SDK)
# ---------------------------------------------------------------------------

def list_partners() -> list[dict[str, Any]]:
    client = firestore_client.get_client()
    if client is None:
        return []
    sonuc = []
    for anlik in client.collection("partners").stream():
        veri = anlik.to_dict() or {}
        veri["id"] = anlik.id
        sonuc.append(veri)
    return sonuc


def create_partner(name: str, contact: str, share_percent: float,
                   notes: str = "") -> dict[str, Any]:
    client = firestore_client.get_client()
    if client is None:
        raise RedeemError(500, "unavailable")
    ref = client.collection("partners").document()
    veri = {"name": name.strip(), "contact": contact.strip(),
            "sharePercent": float(share_percent), "active": True,
            "notes": notes.strip(), "createdAt": _now()}
    ref.set(veri)
    veri["id"] = ref.id
    return veri


def update_partner(partner_id: str, alanlar: dict[str, Any]) -> None:
    client = firestore_client.get_client()
    if client is None:
        raise RedeemError(500, "unavailable")
    izinli = {k: v for k, v in alanlar.items()
              if k in {"name", "contact", "sharePercent", "active", "notes"}}
    if izinli:
        client.collection("partners").document(partner_id).update(izinli)


def create_code(partner_id: str, code: str | None, bonus_tokens: int,
                max_redemptions: int | None,
                expires_at: dt.datetime | None) -> dict[str, Any]:
    """Kod üretir/rezerve eder. `create()` var olan kodda düşer —
    usernames benzersizlik deseni: yarışta ikinci istek hata alır."""
    client = firestore_client.get_client()
    if client is None:
        raise RedeemError(500, "unavailable")
    kod = normalize_code(code) if code else generate_code()
    veri = {"partnerId": partner_id,
            "bonusTokens": int(bonus_tokens),
            "maxRedemptions": (int(max_redemptions)
                               if max_redemptions is not None else None),
            "redemptionCount": 0,
            "expiresAt": expires_at,
            "active": True,
            "createdAt": _now()}
    try:
        client.collection("partnerCodes").document(kod).create(veri)
    except Exception:
        raise RedeemError(409, "code_taken")
    veri["code"] = kod
    return veri


def partner_detail(partner_id: str) -> dict[str, Any]:
    """Ortak + kodları + atfedilen gelir + hakediş + ödemeler."""
    client = firestore_client.get_client()
    if client is None:
        raise RedeemError(500, "unavailable")

    from google.cloud.firestore_v1.base_query import FieldFilter

    anlik = client.collection("partners").document(partner_id).get()
    if not getattr(anlik, "exists", False):
        raise RedeemError(404, "not_found")
    ortak = anlik.to_dict() or {}
    ortak["id"] = partner_id

    kodlar = []
    for k in (client.collection("partnerCodes")
              .where(filter=FieldFilter("partnerId", "==", partner_id))
              .stream()):
        veri = k.to_dict() or {}
        veri["code"] = k.id
        kodlar.append(veri)

    # Atfedilen gelir: USD normalize `price` üzerinden (iade düşülür).
    brut = 0.0
    olay = 0
    for g in (client.collection("revenueEvents")
              .where(filter=FieldFilter("partnerId", "==", partner_id))
              .stream()):
        veri = g.to_dict() or {}
        fiyat = float(veri.get("price") or 0)
        brut += -abs(fiyat) if veri.get("eventType") == "REFUND" else fiyat
        olay += 1

    odenen = 0.0
    odemeler = []
    for o in (client.collection("partners").document(partner_id)
              .collection("payouts").stream()):
        veri = o.to_dict() or {}
        veri["id"] = o.id
        odemeler.append(veri)
        odenen += float(veri.get("amount") or 0)

    pay = float(ortak.get("sharePercent") or 0) / 100.0
    hakedis = round(max(brut, 0.0) * pay, 2)
    return {"partner": ortak, "codes": kodlar,
            "attributedGrossUsd": round(brut, 2),
            "attributedEvents": olay,
            "earnedUsd": hakedis,
            "paidUsd": round(odenen, 2),
            "balanceUsd": round(hakedis - odenen, 2),
            "payouts": odemeler}


def add_payout(partner_id: str, amount: float, currency: str,
               note: str = "") -> dict[str, Any]:
    client = firestore_client.get_client()
    if client is None:
        raise RedeemError(500, "unavailable")
    ref = (client.collection("partners").document(partner_id)
           .collection("payouts").document())
    veri = {"amount": float(amount), "currency": currency.strip().upper(),
            "note": note.strip(), "at": _now()}
    ref.set(veri)
    veri["id"] = ref.id
    return veri
