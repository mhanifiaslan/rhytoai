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


def moon_phase_name(lang: str | None, phase_key: str | None) -> str:
    """Ay evresi anahtarının (``full_moon``) o dildeki adı."""
    if not phase_key:
        return ""
    return get(lang).MOON_PHASES.get(phase_key, phase_key)


def localize_moon_phase(lang: str | None, moon: dict | None) -> dict:
    """Gökyüzü sözlüğündeki ay evresine dile göre ``name`` alanı ekler.

    Hesap paylaşımlı önbellekten geldiği için evre yalnızca anahtar taşır;
    ada çeviri isteğin dilinde, yanıt üretilirken eklenir.
    """
    if not moon:
        return {}
    key = moon.get("key")
    if not key:
        # Anahtarsız gökyüzü (eski önbellek kaydı ya da test verisi):
        # elimizdeki ``name`` neyse onunla devam et, boş metin döndürme.
        return dict(moon)
    return {**moon, "name": moon_phase_name(lang, key)}


def planet_name(lang: str | None, key: str | None) -> str:
    """Gezegen anahtarının (``Saturn``) o dildeki adı."""
    if not key:
        return ""
    return get(lang).PLANET_NAMES.get(key, key)


def aspect_name(lang: str | None, key: str | None) -> str:
    """Açı anahtarının (``square``) o dildeki adı."""
    if not key:
        return ""
    return get(lang).ASPECT_NAMES.get(key, key)


def localize_sky(lang: str | None, sky: dict | None) -> dict:
    """Gökyüzü yükünü isteğin diline çevirir.

    Hesap dilden bağımsızdır ve paylaşımlı önbellekten servis edilir; bu
    yüzden retro listesi, açılar ve ay evresi anahtar taşır. Çeviri **yanıt
    üretilirken** yapılır — aksi halde önbelleği ilk dolduran dil herkese
    servis edilirdi (İngilizce kullanıcı "Satürn retro" görüyordu).
    """
    if not sky:
        return {}
    return {
        **sky,
        "moon_phase": localize_moon_phase(lang, sky.get("moon_phase")),
        "retrogrades": [planet_name(lang, p)
                        for p in (sky.get("retrogrades") or [])],
        "aspects": [
            {**a,
             "p1": planet_name(lang, a.get("p1")),
             "p2": planet_name(lang, a.get("p2")),
             "aspect": aspect_name(lang, a.get("aspect"))}
            for a in (sky.get("aspects") or [])
        ],
    }
