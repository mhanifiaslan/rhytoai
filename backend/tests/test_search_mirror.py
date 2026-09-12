"""Arama aynası (AD4): TR normalize, diff-only yazım, 24 saat memo, hiç
fırlatmama."""
from __future__ import annotations

import pytest

from _sahte_firestore import SahteFirestore
from services import search_mirror


@pytest.fixture(autouse=True)
def temiz_memo():
    search_mirror.reset_memo()
    yield
    search_mirror.reset_memo()


@pytest.mark.parametrize("ham, beklenen", [
    ("İstanbul", "istanbul"),
    ("ISPARTA", "ısparta"),
    ("  Ayşe@Örnek.COM ", "ayşe@örnek.com"),
    ("ﬁne", "fine"),           # NFKC bitişik harf
    (None, ""),
    (42, "42"),
])
def test_normalize(ham, beklenen):
    assert search_mirror.normalize(ham) == beklenen


def test_compute_alanlari():
    assert search_mirror.compute({"email": "A@B.com", "displayName": "Işık"}) == {
        "emailLower": "a@b.com", "usernameLower": "", "nameLower": "ışık"}


def test_ensure_yalniz_farki_yazar(monkeypatch):
    depo = SahteFirestore({"users/u1": {"email": "A@B.com", "username": "Ali",
                                        "emailLower": "a@b.com"}})
    monkeypatch.setattr(search_mirror.firestore_client, "get_client",
                        lambda: depo)
    assert search_mirror.ensure("u1") is True
    _, yol, veri, merge = depo.yazimlar[-1]
    assert yol == "users/u1" and merge is True
    assert veri == {"usernameLower": "ali", "nameLower": ""}
    assert depo.docs["users/u1"]["emailLower"] == "a@b.com"
    # İkinci çağrı memo'dan: okuma da yazım da yok.
    yazim = len(depo.yazimlar)
    assert search_mirror.ensure("u1") is False
    assert len(depo.yazimlar) == yazim


def test_ensure_memo_suresi_dolunca_yeniden_bakar(monkeypatch):
    depo = SahteFirestore({"users/u1": {"email": "x@y.z"}})
    monkeypatch.setattr(search_mirror.firestore_client, "get_client",
                        lambda: depo)
    saat = [1000.0]
    monkeypatch.setattr(search_mirror, "_now", lambda: saat[0])
    assert search_mirror.ensure("u1") is True
    depo.docs["users/u1"]["email"] = "yeni@y.z"
    assert search_mirror.ensure("u1") is False  # memo taze
    saat[0] += search_mirror.MEMO_TTL + 1
    assert search_mirror.ensure("u1") is True
    assert depo.docs["users/u1"]["emailLower"] == "yeni@y.z"


def test_ensure_profil_verilince_okumaz(monkeypatch):
    depo = SahteFirestore()
    monkeypatch.setattr(search_mirror.firestore_client, "get_client",
                        lambda: depo)
    assert search_mirror.ensure("u9", {"displayName": "İpek"}) is True
    assert depo.docs["users/u9"] == {"emailLower": "", "usernameLower": "",
                                     "nameLower": "ipek"}
    # Profil hash'i değişince memo'ya rağmen yazar.
    assert search_mirror.ensure("u9", {"displayName": "İpek"}) is False
    assert search_mirror.ensure("u9", {"displayName": "Ece"}) is True


def test_ensure_dokuman_yoksa_yazmaz(monkeypatch):
    depo = SahteFirestore()
    monkeypatch.setattr(search_mirror.firestore_client, "get_client",
                        lambda: depo)
    assert search_mirror.ensure("$RCAnonymousID:abc") is False
    assert depo.docs == {}


def test_ensure_hic_firlatmaz(monkeypatch):
    class Patlayan:
        def collection(self, ad):
            raise RuntimeError("bum")
    monkeypatch.setattr(search_mirror.firestore_client, "get_client",
                        lambda: Patlayan())
    assert search_mirror.ensure("u1") is False
    monkeypatch.setattr(search_mirror.firestore_client, "get_client",
                        lambda: None)
    assert search_mirror.ensure("u1") is False
    assert search_mirror.ensure("") is False
