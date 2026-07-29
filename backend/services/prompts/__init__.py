"""Dile göre prompt ve persona modülleri.

Prompt'lar dilden bağımsız bir şablona çevirilerin doldurulmasıyla üretilmiyor;
her dil kendi modülünde kendi metnini taşıyor. Gerekçe: bunlar arayüz etiketi
değil, karakter tanımı. Türkçedeki samimi "sen" dili İngilizceye birebir
çevrildiğinde ton bozulur — İngilizcede aynı sıcaklık farklı cümle yapısıyla
kurulur. Kelime kelime çeviri, personayı düzleştirir.

Kullanım:
    from services import prompts
    p = prompts.get("en")
    p.SYSTEM_INSTRUCTION
"""
from __future__ import annotations

from types import ModuleType

from core import i18n
from services.prompts import en as _en
from services.prompts import tr as _tr

_MODULES: dict[str, ModuleType] = {"tr": _tr, "en": _en}


def get(lang: str | None) -> ModuleType:
    """Dilin prompt modülü; tanınmayan dil varsayılana düşer."""
    return _MODULES.get(lang or "", _MODULES[i18n.DEFAULT])


def sign_name(lang: str | None, sign_key: str) -> str:
    """Burç anahtarının (``leo``) o dildeki adı."""
    return get(lang).SIGN_NAMES.get(sign_key, sign_key)
