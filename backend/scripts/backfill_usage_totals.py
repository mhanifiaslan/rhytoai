"""users/{uid}/private/usageTotals — usageEvents'ten MUTLAK toplam (AD11).

`usage_service.record` artık her çağrıda Increment ile biriktiriyor; bu
betik geçmiş olayları bir kez toplar ve dokümanı MUTLAK yazar (set,
merge değil): ikinci koşu aynı değeri hesaplar, farklı değilse yazmaz.
Paylaşımlı üretim (uid yok) kullanıcıya yazılmaz.

Yarış notu: betik koşarken gelen yeni çağrı Increment'i, betiğin
mutlak yazımıyla ezilebilir (bir çağrı). Kabul edilmiş sınır — betik
sakin saatte, bir kez koşar.

    python scripts/backfill_usage_totals.py [--apply]
"""
from __future__ import annotations

from typing import Any

from _ortak import arg_ayristirici, farkli, istemci, ozet, sayfala  # noqa: E402

BETIK = "backfill_usage_totals"


def topla(client) -> tuple[int, dict[str, dict[str, Any]]]:
    incelenen = 0
    kovalar: dict[str, dict[str, Any]] = {}
    for anlik in sayfala(client.collection("usageEvents")):
        incelenen += 1
        veri = anlik.to_dict() or {}
        uid = str(veri.get("uid") or "")
        if not uid:
            continue
        k = kovalar.setdefault(uid, {
            "calls": 0, "estCostUsd": 0.0, "promptTokens": 0,
            "outputTokens": 0, "thinkingTokens": 0, "byFeature": {},
            "lastAt": None})
        bedel = float(veri.get("estCostUsd") or 0)
        k["calls"] += 1
        k["estCostUsd"] = round(k["estCostUsd"] + bedel, 8)
        k["promptTokens"] += int(veri.get("promptTokens") or 0)
        k["outputTokens"] += int(veri.get("outputTokens") or 0)
        k["thinkingTokens"] += int(veri.get("thinkingTokens") or 0)
        oz = str(veri.get("feature") or "unknown")
        f = k["byFeature"].setdefault(oz, {"calls": 0, "estCostUsd": 0.0})
        f["calls"] += 1
        f["estCostUsd"] = round(f["estCostUsd"] + bedel, 8)
        at = veri.get("at")
        if at is not None and (k["lastAt"] is None or at > k["lastAt"]):
            k["lastAt"] = at
    return incelenen, kovalar


def calistir(client, *, apply: bool = False) -> dict[str, Any]:
    incelenen, kovalar = topla(client)
    yazilacak = 0
    for uid, k in kovalar.items():
        ref = (client.collection("users").document(uid)
               .collection("private").document("usageTotals"))
        mevcut = ref.get()
        mevcut_veri = (mevcut.to_dict() or {}) if getattr(mevcut, "exists", False) else None
        if mevcut_veri is not None and not farkli(mevcut_veri, k):
            continue
        yazilacak += 1
        if apply:
            ref.set(k)
    return ozet(BETIK, incelenen, yazilacak, apply, kullanici=len(kovalar))


def main(argv: list[str] | None = None) -> int:
    args = arg_ayristirici(__doc__.split("\n")[0]).parse_args(argv)
    calistir(istemci(), apply=args.apply)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
