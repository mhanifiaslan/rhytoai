"""users/{uid} ayna alanları: arama + plan + authDisabled (AD11).

* `emailLower/usernameLower/nameLower` — services/search_mirror.compute;
  panel araması bu alanları önek sorgusuyla okur.
* `plan/planProduct(/planAt)` — `private/subscription` → api/billing
  `_plan_from` (süresi geçmiş kayıt `free`). `planAt` yalnız plan
  DEĞİŞİYORSA damgalanır — aksi halde her koşu yazardı.
* `authDisabled` — Firebase Auth `list_users` (tek geçiş, uid → disabled);
  Auth listesi alınamazsa (yerel ADC yok) bu alan ATLANIR ve rapor eder.

Diff-only: yalnız farklı alanlar merge edilir; ikinci koşu 0 yazım.

    python scripts/backfill_search_fields.py [--apply]
"""
from __future__ import annotations

import datetime as dt
import logging
from typing import Any

from _ortak import arg_ayristirici, istemci, ozet  # noqa: E402

logger = logging.getLogger("backfill_search_fields")
BETIK = "backfill_search_fields"


def auth_bayraklari() -> dict[str, bool] | None:
    """uid → disabled; Auth okunamazsa None (alan atlanır)."""
    try:
        from firebase_admin import auth as fb_auth
        sonuc: dict[str, bool] = {}
        sayfa = fb_auth.list_users()
        while sayfa:
            for kullanici in sayfa.users:
                sonuc[kullanici.uid] = bool(kullanici.disabled)
            sayfa = sayfa.get_next_page()
        return sonuc
    except Exception as exc:
        logger.warning("Auth listesi alınamadı; authDisabled atlanıyor: %s", exc)
        return None


def hesapla(client, veri: dict[str, Any], uid: str,
            bayraklar: dict[str, bool] | None,
            simdi: dt.datetime) -> dict[str, Any]:
    """Tek kullanıcı için yazılacak FARK (boş sözlük = yazım yok)."""
    from api import billing
    from services import search_mirror

    fark: dict[str, Any] = {}
    for alan, deger in search_mirror.compute(veri).items():
        if veri.get(alan) != deger:
            fark[alan] = deger

    anlik = (client.collection("users").document(uid)
             .collection("private").document("subscription").get())
    kayit = (anlik.to_dict() or {}) if getattr(anlik, "exists", False) else {}
    plan = billing._plan_from(kayit, simdi)
    urun = kayit.get("productId") if plan != "free" else None
    if veri.get("plan") != plan:
        fark["plan"] = plan
        fark["planAt"] = simdi
    if (veri.get("planProduct") or None) != (urun or None):
        fark["planProduct"] = urun

    if bayraklar is not None and uid in bayraklar:
        if veri.get("authDisabled") is not bayraklar[uid]:
            fark["authDisabled"] = bayraklar[uid]
    return fark


def calistir(client, *, apply: bool = False,
             bayraklar: dict[str, bool] | None = None) -> dict[str, Any]:
    from services.stats_service import _iter_users
    simdi = dt.datetime.now(dt.timezone.utc)
    incelenen = yazilacak = 0
    for veri in _iter_users(client):
        incelenen += 1
        uid = veri.pop("uid")
        fark = hesapla(client, veri, uid, bayraklar, simdi)
        if not fark:
            continue
        yazilacak += 1
        if apply:
            client.collection("users").document(uid).set(fark, merge=True)
    return ozet(BETIK, incelenen, yazilacak, apply,
                auth=("ok" if bayraklar is not None else "atlandı"))


def main(argv: list[str] | None = None) -> int:
    args = arg_ayristirici(__doc__.split("\n")[0]).parse_args(argv)
    client = istemci()
    calistir(client, apply=args.apply, bayraklar=auth_bayraklari())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
