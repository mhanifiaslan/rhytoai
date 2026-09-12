"""Kullanıcı listesi sorgu katmanı (AD4): arama aynası + süzgeç modu + imleç.

Değişmezler:
- Arama Türkçe normalize edilir ("İST" → "ist"): ayna alanında önek.
- İmleç sürekliliği: sayfalar çakışmaz, birleşimi tam listedir (iki mod).
- `activeSince` sıralamayı lastSeenDaily'ye, `belowBuild` appBuild'e
  ZORLAR; belowBuild başka süzgeçle YASAK; bilinmeyen sort/alan ValueError.
- `disabled` yalnız true süzer; alanı olmayan eski doküman "devre dışı
  değil"e düşmez ama süzgeçsiz listede görünür.
- Satırda fcmToken ASLA; limit 100'e kırpılır.
"""
from __future__ import annotations

import datetime as dt

import pytest

from _sahte_firestore import SahteFirestore
from services import admin_service, search_mirror

_SIMDI = dt.datetime.now(dt.timezone.utc)


def _kullanici(i: int, **ek):
    veri = {"displayName": f"Kişi {i}", "email": f"k{i}@ornek.com",
            "username": f"kisi{i}", "createdAt": _SIMDI - dt.timedelta(days=i),
            "lastSeenDaily": (_SIMDI - dt.timedelta(days=i)).date().isoformat(),
            "streakCount": i, "language": "tr", "platform": "android",
            "plan": "free", "appBuild": 30 + i, "fcmToken": f"GIZLI-{i}"}
    veri.update(ek)
    veri.update(search_mirror.compute(veri))
    return veri


@pytest.fixture()
def depo(monkeypatch):
    sahte = SahteFirestore()
    for i in range(1, 8):
        sahte.docs[f"users/u{i}"] = _kullanici(i)
    sahte.docs["users/u2"].update({"plan": "plus"})
    sahte.docs["users/u3"].update({"plan": "plus", "language": "en",
                                   "authDisabled": True})
    sahte.docs["users/u4"].update({"authDisabled": False})
    # Türkçe I tuzağı: "İstanbul" nameLower "istanbul", "Işık" → "ışık".
    sahte.docs["users/u5"].update({"displayName": "İstanbul Yılmaz"})
    sahte.docs["users/u5"].update(search_mirror.compute(sahte.docs["users/u5"]))
    sahte.docs["users/u6"].update({"displayName": "Işık Kaya"})
    sahte.docs["users/u6"].update(search_mirror.compute(sahte.docs["users/u6"]))
    monkeypatch.setattr(
        "services.admin_service.firestore_client.get_client", lambda: sahte)
    return sahte


def _tum_sayfalar(**params):
    uidler, imlec, tur = [], None, 0
    while True:
        sonuc = admin_service.list_users(cursor=imlec, **params)
        uidler.extend(s["uid"] for s in sonuc["users"])
        imlec = sonuc["nextCursor"]
        tur += 1
        if not imlec:
            return uidler, tur


# --- arama modu -------------------------------------------------------------

def test_arama_turkce_normalize(depo):
    assert [s["uid"] for s in admin_service.list_users(q="İST")["users"]] == ["u5"]
    assert [s["uid"] for s in admin_service.list_users(q="ıŞı")["users"]] == ["u6"]
    # I → ı: "Isik" ile "Işık" bulunmaz (noktasız I tutarlı); "ışık" bulunur.
    assert admin_service.list_users(q="isik")["users"] == []


def test_arama_alanlari_ve_mod(depo):
    eposta = admin_service.list_users(q="K3@", alan="eposta")
    assert eposta["mode"] == "search"
    assert [s["uid"] for s in eposta["users"]] == ["u3"]
    kadi = admin_service.list_users(q="kisi", alan="kullanici", limit=100)
    assert len(kadi["users"]) == 7
    with pytest.raises(ValueError):
        admin_service.list_users(q="x", alan="telefon")


def test_arama_esitlikler_sayfa_icinde(depo):
    sonuc = admin_service.list_users(q="kisi", alan="kullanici", plan="plus")
    assert sorted(s["uid"] for s in sonuc["users"]) == ["u2", "u3"]
    sonuc = admin_service.list_users(q="kisi", alan="kullanici", disabled=True)
    assert [s["uid"] for s in sonuc["users"]] == ["u3"]


def test_arama_imlec_surekliligi(depo):
    uidler, tur = _tum_sayfalar(q="kisi", alan="kullanici", limit=3)
    assert tur == 3
    assert len(uidler) == len(set(uidler)) == 7
    assert uidler == sorted(uidler)  # order_by(usernameLower) artan


# --- süzgeç modu -----------------------------------------------------------

def test_suzgec_esitlikleri(depo):
    plus = admin_service.list_users(plan="plus")
    assert plus["mode"] == "filter"
    assert [s["uid"] for s in plus["users"]] == ["u2", "u3"]  # createdAt desc
    en = admin_service.list_users(language="en")
    assert [s["uid"] for s in en["users"]] == ["u3"]
    devre_disi = admin_service.list_users(disabled=True)
    assert [s["uid"] for s in devre_disi["users"]] == ["u3"]
    # disabled=False süzgeç DEĞİLDİR: alanı olmayanlar da listede.
    assert len(admin_service.list_users(disabled=False)["users"]) == 7


def test_active_since_siralamayi_zorlar(depo):
    tarih = (_SIMDI - dt.timedelta(days=3)).date().isoformat()
    sonuc = admin_service.list_users(active_since=tarih, sort="streakCount")
    assert [s["uid"] for s in sonuc["users"]] == ["u1", "u2", "u3"]
    # lastSeenDaily DESC: u1 en yeni.
    assert sonuc["users"][0]["lastSeenDaily"] > sonuc["users"][-1]["lastSeenDaily"]


def test_below_build_zorlama_ve_yasak(depo):
    sonuc = admin_service.list_users(below_build=34)
    assert [s["uid"] for s in sonuc["users"]] == ["u3", "u2", "u1"]  # appBuild DESC
    with pytest.raises(ValueError):
        admin_service.list_users(below_build=34, plan="plus")
    with pytest.raises(ValueError):
        admin_service.list_users(below_build=34, disabled=True)
    with pytest.raises(ValueError):
        admin_service.list_users(sort="email")


def test_suzgec_imlec_surekliligi(depo):
    uidler, tur = _tum_sayfalar(sort="streakCount", limit=2)
    assert tur == 4
    assert uidler == ["u7", "u6", "u5", "u4", "u3", "u2", "u1"]
    uidler, _ = _tum_sayfalar(plan="plus", sort="createdAt", limit=1)
    assert uidler == ["u2", "u3"]


def test_bozuk_imlec_ve_limit(depo):
    with pytest.raises(ValueError):
        admin_service.list_users(cursor="bozuk!!")
    sonuc = admin_service.list_users(limit=999)
    assert len(sonuc["users"]) == 7  # 100'e kırpıldı, 7 var
    assert admin_service.LIST_LIMIT_MAX == 100


def test_satirda_jeton_yok(depo):
    for sonuc in (admin_service.list_users(),
                  admin_service.list_users(q="kisi", alan="kullanici")):
        duz = str(sonuc)
        assert "GIZLI" not in duz
        assert all("fcmToken" not in s and "hasPush" in s
                   and "authDisabled" in s for s in sonuc["users"])
