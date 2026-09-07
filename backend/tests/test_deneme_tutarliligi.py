# -*- coding: utf-8 -*-
"""KL-turu: deneme kararının TÜM uçlarda aynı anda dönmesi.

Canlıda ölçülen kusur: Profil ekranı "Rytho+" gösterirken `/api/v1/people`
kontenjanı ücretsiz katmanın 1'i olarak döndü ("4/1 kişi"). Sebep,
`in_trial`'ın BOOLEAN sonucunu 15 dakika önbelleklemesiydi — sınır
geçildiğinde önbellekli çağrı "evet", taze çağrı "hayır" diyordu.
"""
import datetime as dt

import pytest

from core import cache, entitlements


@pytest.fixture(autouse=True)
def _temiz_onbellek(monkeypatch):
    """Yalnız bellek katmanı kullanılsın.

    `cache` varsayılan olarak DOSYAYA da yazıyor; sadece `_memory` temizlemek
    yetmiyordu ve önceki pytest koşusundan kalan kayıt testleri düşürüyordu
    (koşu sırasına bağlı, aldatıcı bir kırmızı).
    """
    monkeypatch.setattr(cache, "_persistent_get", lambda key: None)
    monkeypatch.setattr(cache, "_persistent_set",
                        lambda key, value, expires_at, owner_uid=None: None)
    cache._memory.clear()
    yield
    cache._memory.clear()


def _profil(gun_once: float):
    an = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=gun_once)
    return {"createdAt": an}


def test_deneme_biterken_TUM_yollar_ayni_anda_doner(monkeypatch):
    """Onbellek isinmisken bile sinir gecilince her cagri 'hayir' der.

    Kusurun birebir yeniden uretimi: once denemedeyken bir okuma yapilir
    (onbellek isinir), sonra saat ileri alinir. Eski kodda ilk okuma
    `True` sakladigi icin ikinci okuma hala `True` donuyordu.
    """
    from services import profile_service
    # Deneme bitmesine 1 dakika kala olusturulmus hesap
    kalan = entitlements.TRIAL_DAYS * 24 * 3600 - 60
    an = dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=kalan)
    monkeypatch.setattr(profile_service, "get_profile",
                        lambda uid: {"createdAt": an})

    assert entitlements.in_trial("u1") is True          # onbellek isinir
    assert entitlements.is_subscriber("u1") is True

    # Saat 2 dakika ilerler: deneme bitti.
    gercek = dt.datetime
    class _Ileri(dt.datetime):
        @classmethod
        def now(cls, tz=None):
            return gercek.now(tz) + dt.timedelta(minutes=2)
    monkeypatch.setattr(entitlements.dt, "datetime", _Ileri)

    # Onbellek HALA sicak (TTL 15 dk) ama karar taze hesaplaniyor.
    assert entitlements.in_trial("u1") is False
    assert entitlements.is_subscriber("u1") is False
    assert entitlements.trial_days_left("u1") is None


def test_onbellek_profil_okumasini_hala_azaltiyor(monkeypatch):
    """Onarim performansi bozmamali: createdAt bir kez okunur."""
    from services import profile_service
    sayac = {"n": 0}

    def sahte(uid):
        sayac["n"] += 1
        return _profil(1)

    monkeypatch.setattr(profile_service, "get_profile", sahte)
    for _ in range(5):
        entitlements.in_trial("u2")
        entitlements.trial_days_left("u2")
    assert sayac["n"] == 1


def test_createdAt_yoksa_deneme_YOK(monkeypatch):
    from services import profile_service
    monkeypatch.setattr(profile_service, "get_profile", lambda uid: {})
    assert entitlements.in_trial("u3") is False
    assert entitlements.trial_days_left("u3") is None


def test_gelecek_tarihli_createdAt_deneme_ACMAZ(monkeypatch):
    """Saat kaymasi ya da bozuk kayit ucretsiz katmanda birakir."""
    from services import profile_service
    monkeypatch.setattr(profile_service, "get_profile",
                        lambda uid: _profil(-2))   # 2 gun SONRA
    assert entitlements.in_trial("u4") is False


def test_kalan_gun_yukari_yuvarlanir(monkeypatch):
    from services import profile_service
    monkeypatch.setattr(profile_service, "get_profile",
                        lambda uid: _profil(0.5))
    kalan = entitlements.trial_days_left("u5")
    assert kalan == entitlements.TRIAL_DAYS   # 2.5 gun -> 3
