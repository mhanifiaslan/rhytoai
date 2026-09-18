"""users/{uid} ayna alanları: arama + plan + authDisabled (AD11).

* `emailLower/usernameLower/nameLower` — services/search_mirror.compute;
  panel araması bu alanları önek sorgusuyla okur.
* `plan/planProduct(/planAt)` — `private/subscription` → api/billing
  `_plan_from` (süresi geçmiş kayıt `free`). `planAt` yalnız plan
  DEĞİŞİYORSA damgalanır — aksi halde her koşu yazardı.
* `authDisabled` — Firebase Auth `list_users` (tek geçiş, uid → disabled);
  Auth listesi alınamazsa (yerel ADC yok) bu alan ATLANIR ve rapor eder.
* `createdAt` — alanı HİÇ olmayan dokümanda Firebase Auth'un hesap oluşma
  damgası. Panel listesi `order_by("createdAt")` ile sorguluyor ve Firestore
  alanı bulunmayan dokümanı sonuç kümesinden DÜŞÜRÜYOR; damga eskiden yalnız
  onboarding'in son adımında yazıldığı için akışı yarım bırakan hesap
  görünmez kalmış. Damga UYDURULMAZ (`simdi` yazılsa kayıt tarihi bugüne
  kayar ve core/entitlements 3 günlük denemeyi sıfırdan açardı); Auth'ta
  damga yoksa alan ATLANIR ve özet bunu söyler.

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


def auth_kayit_damgalari() -> dict[str, dt.datetime]:
    """uid → hesabın Auth'ta OLUŞMA zamanı; okunamazsa boş sözlük.

    Ayrı geçiş: `auth_bayraklari`nin dönüş şekli değişmesin (çağıranlar ve
    bekçi testi bool sözlüğü bekliyor). Betik elle ve nadir koşuyor.
    """
    try:
        from firebase_admin import auth as fb_auth
        sonuc: dict[str, dt.datetime] = {}
        sayfa = fb_auth.list_users()
        while sayfa:
            for kullanici in sayfa.users:
                ms = getattr(kullanici.user_metadata, "creation_timestamp",
                             None)
                if ms:
                    sonuc[kullanici.uid] = dt.datetime.fromtimestamp(
                        ms / 1000, dt.timezone.utc)
            sayfa = sayfa.get_next_page()
        return sonuc
    except Exception as exc:
        logger.warning("Auth kayıt damgaları alınamadı; createdAt atlanıyor: "
                       "%s", exc)
        return {}


def hesapla(client, veri: dict[str, Any], uid: str,
            bayraklar: dict[str, bool] | None,
            simdi: dt.datetime,
            kayit_damgalari: dict[str, dt.datetime] | None = None,
            ) -> dict[str, Any]:
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

    # Kayıt damgası: alan YOKSA Auth'taki gerçek oluşma anından konur. Panel
    # listesi `order_by("createdAt")` ile sorguladığı için alanı olmayan
    # doküman sonuç kümesinden DÜŞÜYOR — onboarding'i yarım bırakan hesap
    # "kim takıldı" sorusunun cevabı olduğu halde görünmüyordu. Var olan damga
    # ezilmez ve damga bulunamazsa UYDURULMAZ: `simdi` yazılsa hem kayıt
    # tarihi bugüne kayar hem 3 günlük deneme sıfırdan başlardı.
    if veri.get("createdAt") is None:
        damga = (kayit_damgalari or {}).get(uid)
        if damga is not None:
            fark["createdAt"] = damga
    return fark


def calistir(client, *, apply: bool = False,
             bayraklar: dict[str, bool] | None = None,
             kayit_damgalari: dict[str, dt.datetime] | None = None,
             ) -> dict[str, Any]:
    from services.stats_service import _iter_users
    simdi = dt.datetime.now(dt.timezone.utc)
    incelenen = yazilacak = 0
    for veri in _iter_users(client):
        incelenen += 1
        uid = veri.pop("uid")
        fark = hesapla(client, veri, uid, bayraklar, simdi, kayit_damgalari)
        if not fark:
            continue
        yazilacak += 1
        if apply:
            client.collection("users").document(uid).set(fark, merge=True)
    return ozet(BETIK, incelenen, yazilacak, apply,
                auth=("ok" if bayraklar is not None else "atlandı"),
                # Prova çıktısı damga geçişinin ATLANDIĞINI ekranda söylemeli:
                # betik elle ve nadir koşuyor, yalnız logger.warning'de kalsa
                # operatör "createdAt neden dolmadı" sorusunu göremez.
                kayit=("ok" if kayit_damgalari else "atlandı"))


def main(argv: list[str] | None = None) -> int:
    args = arg_ayristirici(__doc__.split("\n")[0]).parse_args(argv)
    client = istemci()
    calistir(client, apply=args.apply, bayraklar=auth_bayraklari(),
             kayit_damgalari=auth_kayit_damgalari())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
