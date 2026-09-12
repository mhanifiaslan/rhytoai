"""Sayfalama imleci (AD3): sorgu cursor'ı ↔ URL-güvenli dizgi.

Panel "Daha fazla" derken sunucuya son satırın sıralama değerlerini geri
verir; Firestore `start_after` bu değerlerle devam eder. Değerler JSON'a
yazılır, base64url'e sarılır — dolgu (`=`) atılır ki sorgu dizgisinde
kaçış gerekmesin. `datetime` JSON'da yok; `{"$ts": epoch}` olarak taşınır
ve çözümde UTC'ye döner.

Bozuk/kurcalanmış imleç `ValueError` fırlatır; uçlar bunu 400'e çevirir.
İmleç bir yetki belgesi DEĞİLDİR — içinde yalnız sıralama değerleri var,
kurcalanması en fazla başka bir sayfaya düşürür.
"""
from __future__ import annotations

import base64
import datetime as dt
import json
from typing import Any


def _yaz(deger: Any) -> Any:
    if isinstance(deger, dt.datetime):
        if deger.tzinfo is None:
            deger = deger.replace(tzinfo=dt.timezone.utc)
        return {"$ts": deger.timestamp()}
    return deger


def _oku(deger: Any) -> Any:
    if isinstance(deger, dict) and set(deger) == {"$ts"}:
        return dt.datetime.fromtimestamp(float(deger["$ts"]), dt.timezone.utc)
    return deger


def encode(values: list) -> str:
    """Sıralama değerlerini imleç dizgisine çevirir."""
    ham = json.dumps([_yaz(v) for v in values], separators=(",", ":"),
                     ensure_ascii=False)
    return base64.urlsafe_b64encode(ham.encode("utf-8")).decode("ascii").rstrip("=")


def decode(token: str) -> list:
    """İmleç dizgisini değer listesine çevirir; bozuksa ValueError."""
    if not isinstance(token, str) or not token.strip():
        raise ValueError("Geçersiz imleç.")
    try:
        dolgu = "=" * (-len(token) % 4)
        ham = base64.urlsafe_b64decode(token + dolgu)
        veri = json.loads(ham.decode("utf-8"))
    except Exception as exc:
        raise ValueError("Geçersiz imleç.") from exc
    if not isinstance(veri, list):
        raise ValueError("Geçersiz imleç.")
    return [_oku(v) for v in veri]
