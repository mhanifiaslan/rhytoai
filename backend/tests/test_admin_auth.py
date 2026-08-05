"""Admin kimliği (W4): custom claim + require_admin değişmezleri.

Bir numaralı değişmez: **DEV_MODE'un dev-user'ı admin DEĞİLDİR.**
Geliştirme kolaylığı yönetim yetkisine dönüşemez; yerel deneme için ayrı
ve açık bayrak RYTHO_DEV_ADMIN gerekir.
"""
from __future__ import annotations

import asyncio

import pytest
from fastapi import HTTPException

from core import auth, config


class _SahteToken:
    credentials = "token"


def _kullanici(monkeypatch, decoded):
    """get_current_user'ı sahte doğrulanmış token'la çalıştırır."""
    monkeypatch.setattr(auth, "_init_firebase", lambda: True)
    monkeypatch.setattr(auth, "_verify", lambda t: decoded)
    return asyncio.run(auth.get_current_user(
        credentials=_SahteToken(), lang="tr"))


def test_claim_tasiyan_token_admin(monkeypatch):
    user = _kullanici(monkeypatch, {"uid": "u", "admin": True})
    assert user.admin is True
    assert auth.require_admin(user) is user


def test_claimsiz_token_admin_degil(monkeypatch):
    user = _kullanici(monkeypatch, {"uid": "u"})
    assert user.admin is False
    with pytest.raises(HTTPException) as h:
        auth.require_admin(user)
    assert h.value.status_code == 403


def test_claim_true_disinda_hicbir_deger_gecmez(monkeypatch):
    # "true" dizgisi, 1, ya da baska truthy degerler claim SAYILMAZ —
    # yalnizca gercek boolean True.
    for deger in ("true", 1, "1", {}, []):
        user = _kullanici(monkeypatch, {"uid": "u", "admin": deger})
        assert user.admin is False, repr(deger)


def test_dev_mode_dev_user_admin_DEGIL(monkeypatch):
    """Bir numaralı değişmez: DEV_MODE tek başına yetki veremez."""
    monkeypatch.setattr(config, "DEV_MODE", True)
    monkeypatch.setattr(config, "DEV_ADMIN", False)
    monkeypatch.setattr(auth, "_init_firebase", lambda: False)
    user = asyncio.run(auth.get_current_user(credentials=None, lang="tr"))
    assert user.uid == "dev-user"
    assert user.admin is False
    with pytest.raises(HTTPException):
        auth.require_admin(user)


def test_dev_admin_bayragi_acikca_izin_verir(monkeypatch):
    monkeypatch.setattr(config, "DEV_MODE", True)
    monkeypatch.setattr(config, "DEV_ADMIN", True)
    monkeypatch.setattr(auth, "_init_firebase", lambda: False)
    user = asyncio.run(auth.get_current_user(credentials=None, lang="tr"))
    assert user.admin is True
