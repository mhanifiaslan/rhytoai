"""Backfill betiklerinin ortak parçaları (AD11).

Her betik aynı duruşu paylaşır:

* **Prova varsayılan** — `--apply` verilmeden HİÇBİR yazım yapılmaz; betik
  ne yazacağını sayar ve söyler.
* **İdempotent** — yalnız FARKLI olan yazılır; ikinci koşu 0 yazım
  (tests/test_backfill_scripts.py bunu sahte Firestore ile kanıtlar).
* **Sayfalı** — koleksiyon belleğe alınmaz; `sayfala` 500'lük sayfalarla
  dolaşır (stats_service._iter_users emsali, ama her sorguya uyar).

Kullanım (backend dizininden):
    .venv/Scripts/python.exe scripts/backfill_revenue_env.py --env SANDBOX
    .venv/Scripts/python.exe scripts/backfill_revenue_env.py --env SANDBOX --totals --apply
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Iterator

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

PAGE_SIZE = 500


def istemci():
    """Firestore istemcisi; kurulamazsa açık mesajla çıkar (ADC yok?)."""
    from core import firestore as firestore_client
    client = firestore_client.get_client()
    if client is None:
        raise SystemExit("Firestore erişilemiyor — ADC/GOOGLE_CLOUD_PROJECT?")
    return client


def sayfala(sorgu, n: int = PAGE_SIZE) -> Iterator[Any]:
    """Herhangi bir sorguyu anlık görüntü imleciyle sayfalar.

    `start_after(anlık)` sorgunun kendi sıralamasını (varsayılan
    `__name__`, eşitsizlik varsa o alan) kullanır — collection-group
    sorgularında sözlük imleci (`{"__name__": id}`) tam yol ister, anlık
    görüntü istemez.
    """
    son = None
    while True:
        q = sorgu.limit(n)
        if son is not None:
            q = q.start_after(son)
        sayfa = list(q.stream())
        if not sayfa:
            return
        for anlik in sayfa:
            yield anlik
        if len(sayfa) < n:
            return
        son = sayfa[-1]


def arg_ayristirici(aciklama: str) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=aciklama)
    p.add_argument("--apply", action="store_true",
                   help="Yazımları GERÇEKTEN yap (varsayılan prova).")
    return p


def ozet(ad: str, incelenen: int, yazilacak: int, apply: bool,
         **ek: Any) -> dict[str, Any]:
    """Tek satırlık sonuç + döndürülen sözlük (testler sözlüğe bakar)."""
    sonuc = {"betik": ad, "incelenen": incelenen,
             "yazilan" if apply else "yazilacak": yazilacak,
             "apply": apply, **ek}
    kip = "YAZILDI" if apply else "PROVA (yazım yok; --apply ile uygula)"
    print(f"[{ad}] incelenen={incelenen} "
          f"{'yazılan' if apply else 'yazılacak'}={yazilacak} — {kip}"
          + (f" | {ek}" if ek else ""))
    return sonuc


def farkli(mevcut: dict[str, Any] | None, istenen: dict[str, Any]) -> bool:
    """İstenen alanlar mevcut dokümanla birebir mi (float 6 hane)?"""
    mevcut = mevcut or {}

    def norm(v: Any) -> Any:
        if isinstance(v, float):
            return round(v, 6)
        if isinstance(v, dict):
            return {k: norm(x) for k, x in v.items()}
        return v
    return any(norm(mevcut.get(k)) != norm(v) for k, v in istenen.items())
