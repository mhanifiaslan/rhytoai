"""revenueEvents ortam etiketi + kullanıcı gelir toplamları (AD11).

Bugüne dek yazılan olaylarda `environment`/`monetary` yok (webhook AD5
öncesi kaydetmiyordu). Kapalı test öncesi gerçek satış olmadığı için
mevcut TÜM olaylar `SANDBOX` etiketlenir; alanı olan doküman ATLANIR
(webhook artık yazıyor — backfill onu ezmez).

`--totals`: `users/{uid}/private/revenueTotals.{ENV}` MUTLAK yeniden
hesaplanır (Increment değil — ikinci koşu birikmez, farklı değilse
yazılmaz). Cüzdan/abonelik durumlarına DOKUNULMAZ.

    python scripts/backfill_revenue_env.py --env SANDBOX [--totals] [--apply]
"""
from __future__ import annotations

from typing import Any

from _ortak import arg_ayristirici, farkli, istemci, ozet, sayfala  # noqa: E402

BETIK = "backfill_revenue_env"


def _parasal(event_type: str) -> bool:
    from api import billing
    return event_type in billing._REVENUE_EVENTS


def etiketle(client, env: str, *, apply: bool = False) -> dict[str, Any]:
    """`environment` alanı olmayan olayları etiketler; `monetary` de yoksa
    tür tablosundan doldurur."""
    env = str(env).upper()
    incelenen = yazilacak = 0
    for anlik in sayfala(client.collection("revenueEvents")):
        incelenen += 1
        veri = anlik.to_dict() or {}
        if veri.get("environment"):
            continue
        yeni: dict[str, Any] = {"environment": env}
        if "monetary" not in veri:
            yeni["monetary"] = _parasal(str(veri.get("eventType") or ""))
        yazilacak += 1
        if apply:
            anlik.reference.set(yeni, merge=True)
    return ozet(BETIK, incelenen, yazilacak, apply, env=env)


def toplamlar(client, *, apply: bool = False) -> dict[str, Any]:
    """Her kullanıcının ortam başına gross/refunds/events toplamı — MUTLAK."""
    kovalar: dict[str, dict[str, dict[str, Any]]] = {}
    incelenen = 0
    for anlik in sayfala(client.collection("revenueEvents")):
        incelenen += 1
        veri = anlik.to_dict() or {}
        uid = str(veri.get("uid") or "")
        if not uid or veri.get("monetary") is False:
            continue
        env = str(veri.get("environment") or "SANDBOX").upper()
        kova = kovalar.setdefault(uid, {}).setdefault(
            env, {"grossUsd": 0.0, "refundsUsd": 0.0, "events": 0})
        tutar = abs(float(veri.get("price") or 0))
        if veri.get("eventType") == "REFUND":
            kova["refundsUsd"] = round(kova["refundsUsd"] + tutar, 4)
        else:
            kova["grossUsd"] = round(kova["grossUsd"] + tutar, 4)
        kova["events"] += 1

    yazilacak = 0
    for uid, ortamlar in kovalar.items():
        ref = (client.collection("users").document(uid)
               .collection("private").document("revenueTotals"))
        mevcut = ref.get()
        mevcut_veri = (mevcut.to_dict() or {}) if getattr(mevcut, "exists", False) else None
        # Aynı ortam kümesi + aynı sayılar → dokunma (mutlak yazım, birikmez).
        if (mevcut_veri is not None and set(mevcut_veri) == set(ortamlar)
                and not farkli(mevcut_veri, ortamlar)):
            continue
        yazilacak += 1
        if apply:
            ref.set(ortamlar)  # mutlak: eski/yanlış ortam kovası kalmaz
    return ozet(f"{BETIK}:totals", incelenen, yazilacak, apply,
                kullanici=len(kovalar))


def main(argv: list[str] | None = None) -> int:
    p = arg_ayristirici(__doc__.split("\n")[0])
    p.add_argument("--env", default="SANDBOX", choices=["SANDBOX", "PRODUCTION"])
    p.add_argument("--totals", action="store_true",
                   help="private/revenueTotals dokümanlarını mutlak yeniden hesapla.")
    args = p.parse_args(argv)
    client = istemci()
    etiketle(client, args.env, apply=args.apply)
    if args.totals:
        toplamlar(client, apply=args.apply)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
