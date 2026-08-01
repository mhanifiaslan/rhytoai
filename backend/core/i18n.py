"""Dil çözümleme — istekten tek bir dil koduna.

Dil, her uca ayrı bir gövde alanı olarak eklenmek yerine ``Accept-Language``
başlığından okunur. Gerekçe: standart olan yol bu, istemci başlığı Dio
interceptor'ında bir kez ayarlar, ve mevcut istek şemalarının hiçbiri
değişmez.

Desteklenmeyen bir dil geldiğinde hata verilmez — varsayılana düşülür.
Kullanıcının uygulamayı kullanamaması, yorumu yabancı dilde görmesinden
kötüdür.
"""
from __future__ import annotations

from fastapi import Header

#: Desteklenen diller. Yeni dil eklemek için: buraya kod, services/prompts
#: altına modül, knowledge/corpus altına dizin.
SUPPORTED: tuple[str, ...] = ("tr", "en")

#: Başlık yoksa veya tanınmıyorsa kullanılacak dil.
DEFAULT = "tr"


def resolve_language(accept_language: str | None) -> str:
    """``Accept-Language`` başlığını desteklenen bir dil koduna indirger.

    Ağırlıkları (``q=``) sırayla değerlendirir; ilk desteklenen dili döndürür.
    Bölgesel varyantlar ana dile katlanır: ``en-GB`` -> ``en``.
    """
    if not accept_language:
        return DEFAULT

    adaylar: list[tuple[float, str]] = []
    for parca in accept_language.split(","):
        parca = parca.strip()
        if not parca:
            continue
        kod, _, nitelik = parca.partition(";")
        kod = kod.strip().lower().split("-")[0]
        agirlik = 1.0
        if nitelik.strip().startswith("q="):
            try:
                agirlik = float(nitelik.strip()[2:])
            except ValueError:
                agirlik = 0.0
        adaylar.append((agirlik, kod))

    # Ağırlığı yüksek olan önce; eşitlikte başlıktaki sıra korunur.
    for _, kod in sorted(adaylar, key=lambda x: -x[0]):
        if kod in SUPPORTED:
            return kod
    return DEFAULT


def get_language(accept_language: str | None = Header(default=None)) -> str:
    """FastAPI bağımlılığı: ``lang: str = Depends(get_language)``."""
    return resolve_language(accept_language)
