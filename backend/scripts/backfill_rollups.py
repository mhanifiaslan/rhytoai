"""adminStats + adminEconomics rollup'larını geçmiş günler için üretir (AD11).

`stats_service.collect(gün, snapshot=False)`: yalnız o günün OLAY
bölümleri (gelir/jeton/AI/bildirim) ve adminEconomics yazılır; geçmiş
günün DAU/plan fotoğrafı uydurulmaz (bugün için `snapshot=True`).
Doğası gereği idempotent: aynı gün ikinci koşu aynı içeriği ezer.

Sıra (docs/konsol-gorevleri.md §3c): revenue_env → search_fields →
usage_totals → rollups(ilk olay günü → bugün).

    python scripts/backfill_rollups.py --from 2026-08-01 --to 2026-09-12 [--apply]
"""
from __future__ import annotations

import datetime as dt
from typing import Any

from _ortak import arg_ayristirici, istemci, ozet  # noqa: E402

BETIK = "backfill_rollups"


def gunler(bas: dt.date, son: dt.date) -> list[dt.date]:
    if son < bas:
        raise SystemExit("--to, --from'dan önce olamaz.")
    return [bas + dt.timedelta(days=i) for i in range((son - bas).days + 1)]


def calistir(client, bas: dt.date, son: dt.date, *,
             apply: bool = False) -> dict[str, Any]:
    from services import stats_service
    bugun = dt.datetime.now(dt.timezone.utc).date()
    hedef = [g for g in gunler(bas, son) if g <= bugun]
    yazilan = 0
    for gun in hedef:
        if apply:
            stats_service.collect(gun, snapshot=(gun == bugun))
        yazilan += 1
    return ozet(BETIK, len(hedef), yazilan * 2, apply,
                ilk=hedef[0].isoformat() if hedef else None,
                son=hedef[-1].isoformat() if hedef else None)


def main(argv: list[str] | None = None) -> int:
    p = arg_ayristirici(__doc__.split("\n")[0])
    p.add_argument("--from", dest="bas", required=True, type=dt.date.fromisoformat)
    p.add_argument("--to", dest="son", type=dt.date.fromisoformat,
                   default=dt.datetime.now(dt.timezone.utc).date())
    args = p.parse_args(argv)
    calistir(istemci(), args.bas, args.son, apply=args.apply)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
