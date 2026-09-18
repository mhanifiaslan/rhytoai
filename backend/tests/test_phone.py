"""Telefon eşleme kaydının değişmezleri (Revize R2).

Güven zinciri testin merkezinde: numara İSTEMCİDEN alınmaz, doğrulanmış
token claim'inden gelir. Uç seviyesindeki testler bunu tutuyor — gövdeyle
numara gönderen bir istemci HİÇBİR ŞEY kaydettiremez.
"""
from __future__ import annotations

import pytest

from services import phone_service


class _SahteAnlik:
    def __init__(self, data):
        self._data = data

    @property
    def exists(self):
        return self._data is not None

    def to_dict(self):
        return dict(self._data) if self._data else {}


class _SahteDoc:
    def __init__(self, depo, yol):
        self._depo = depo
        self._yol = yol

    def get(self):
        return _SahteAnlik(self._depo.get(self._yol))

    def set(self, data, merge=False):
        mevcut = dict(self._depo.get(self._yol) or {}) if merge else {}
        mevcut.update(data)
        self._depo[self._yol] = mevcut

    def delete(self):
        self._depo.pop(self._yol, None)

    def collection(self, ad):
        return _SahteKoleksiyon(self._depo, f"{self._yol}/{ad}")


class _SahteKoleksiyon:
    def __init__(self, depo, yol):
        self._depo = depo
        self._yol = yol

    def document(self, ad=None):
        if ad is None:  # auto-id (record_attempt)
            ad = f"auto{len([k for k in self._depo if k.startswith(self._yol)])}"
        return _SahteDoc(self._depo, f"{self._yol}/{ad}")


class _SahteClient:
    def __init__(self, depo):
        self._depo = depo

    def collection(self, ad):
        return _SahteKoleksiyon(self._depo, ad)


@pytest.fixture()
def depo(monkeypatch):
    veriler: dict = {}
    monkeypatch.setattr(phone_service.firestore_client, "get_client",
                        lambda: _SahteClient(veriler))
    return veriler


_NUMARA = "+905551112233"


def _hash(n=_NUMARA):
    return phone_service.phone_hash(n)


def test_kayit_iki_yere_yazilir(depo):
    phone_service.sync_phone("u1", _NUMARA)

    assert depo[f"phoneHashes/{_hash()}"]["uid"] == "u1"
    assert depo["users/u1/private/phone"]["hash"] == _hash()


def test_ham_numara_hicbir_yere_yazilmaz(depo):
    """Firestore'a ham numara girmez — Firebase Auth'taki kopya yeter,
    ikincisi yeni bir sizinti yuzeyi olurdu."""
    phone_service.sync_phone("u1", _NUMARA)

    for yol, veri in depo.items():
        for deger in veri.values():
            assert _NUMARA not in str(deger), f"{yol} ham numara iceriyor"


def test_ayni_kullanici_idempotent(depo):
    phone_service.sync_phone("u1", _NUMARA)
    sonuc = phone_service.sync_phone("u1", _NUMARA)
    assert sonuc == {"linked": True, "changed": False}


def test_baska_hesaba_bagli_numara_reddedilir(depo):
    """Bir numara TEK hesaba baglanir; aksi halde rehber eslesmesi ayni
    numara icin iki kisi dondururdu."""
    phone_service.sync_phone("u1", _NUMARA)

    with pytest.raises(phone_service.PhoneTakenError):
        phone_service.sync_phone("u2", _NUMARA)

    assert depo[f"phoneHashes/{_hash()}"]["uid"] == "u1"


def test_numara_degisince_eski_hash_serbest_kalir(depo):
    """Kullanici adi deseninin aynisi: eski kayit sarkarsa numaranin yeni
    sahibi kaydolamaz."""
    phone_service.sync_phone("u1", _NUMARA)
    yeni = "+905559998877"
    phone_service.sync_phone("u1", yeni)

    assert f"phoneHashes/{_hash()}" not in depo
    assert depo[f"phoneHashes/{_hash(yeni)}"]["uid"] == "u1"
    assert depo["users/u1/private/phone"]["hash"] == _hash(yeni)


def test_release_hash_dizinini_temizler(depo):
    phone_service.sync_phone("u1", _NUMARA)
    phone_service.release_phone("u1")
    assert f"phoneHashes/{_hash()}" not in depo


def test_hash_normalize_bosluk(depo):
    assert phone_service.phone_hash(" +905551112233 ") == _hash()


# ---------------------------------------------------------------------------
# Teşhis kaydı (2026-09-08 canlı olayı)
#
# Bir kullanıcı SMS alamadı; Google tarafında her şey sağlıklıydı (istek
# 200, SMS faturalandı, engellenmedi) ama "numara doğruydu da operatör mü
# düşürdü, yoksa numara yanlış mı derlendi" sorusunu ayırt edemedik —
# gönderdiğimiz numarayı hiçbir yere yazmıyorduk. record_attempt bunu
# kapatıyor; bu testler MASKENİN maske kalmasını garanti ediyor.
# ---------------------------------------------------------------------------


def _denemeler(depo):
    return [v for k, v in depo.items() if k.startswith("phoneAttempts/")]


def test_deneme_kaydi_yazilir(depo):
    phone_service.record_attempt("u1", "sent", "TR", "+90532***4567")
    kayit = _denemeler(depo)
    assert len(kayit) == 1
    assert kayit[0]["uid"] == "u1"
    assert kayit[0]["stage"] == "sent"
    assert kayit[0]["iso2"] == "TR"
    assert kayit[0]["at"] is not None


def test_deneme_kaydinda_HAM_numara_yok(depo):
    # Maske sunucuda da maske kalmalı: kayıt teşhis içindir, kimlik için değil.
    phone_service.record_attempt("u1", "sent", "TR", "+90532***4567")
    metin = str(_denemeler(depo))
    assert "***" in metin
    assert "+905321234567" not in metin


def test_bilinmeyen_asama_yazilmaz(depo):
    # İstemci ne gönderirse göndersin kayda yalnız bilinen aşamalar girer.
    phone_service.record_attempt("u1", "rastgele", "TR", "+90532***4567")
    assert _denemeler(depo) == []


def test_asiri_uzun_alanlar_kirpilir(depo):
    phone_service.record_attempt("u1", "failed", "TRXX", "x" * 100, "y" * 200)
    kayit = _denemeler(depo)[0]
    assert kayit["iso2"] == "TR"
    assert len(kayit["masked"]) <= 24
    assert len(kayit["code"]) <= 64


def test_firestore_yoksa_sessiz(monkeypatch):
    # Telemetri doğrulama akışını ASLA düşüremez.
    monkeypatch.setattr(phone_service.firestore_client, "get_client",
                        lambda: None)
    phone_service.record_attempt("u1", "sent", "TR", "+90532***4567")


def test_firestore_firlatirsa_sessiz(monkeypatch):
    class _Patlayan:
        def collection(self, ad):
            raise RuntimeError("firestore down")

    monkeypatch.setattr(phone_service.firestore_client, "get_client",
                        lambda: _Patlayan())
    phone_service.record_attempt("u1", "sent", "TR", "+90532***4567")


# ---------------------------------------------------------------------------
# Maske kırpma (kapalı test denetimi, 2026-09-18)
# ---------------------------------------------------------------------------
#
# Maske ilk 3 + *** + son 4 haneydi: 10 haneli bir numarada yalnızca ÜÇ hane
# gizli, yani kayıt pratikte numaranın kendisi. Kırpma SUNUCUDA yapılıyor
# çünkü alanı istemci gönderiyor ve sahadaki eski sürümler tam maskeyi
# göndermeye devam ediyor.


def test_maskenin_son_haneleri_kaydedilmez(depo):
    phone_service.record_attempt("u1", "sent", "TR", "+90532***4567")
    kayit = _denemeler(depo)[0]
    assert kayit["masked"] == "+90532***"
    assert "4567" not in kayit["masked"]


def test_operator_onegi_TESHIS_ICIN_kalir(depo):
    """Kaydın var olma sebebi bu önek: silersek teşhis de gider."""
    phone_service.record_attempt("u1", "failed", "TR", "+90532***4567",
                                 "invalid-phone-number")
    kayit = _denemeler(depo)[0]
    assert kayit["masked"].startswith("+90532")
    assert kayit["code"] == "invalid-phone-number"


def test_maskesiz_gelen_deger_HIC_yazilmaz(depo):
    """Eski ya da kötü niyetli bir istemci ham numara yollarsa alan boş kalır."""
    phone_service.record_attempt("u1", "sent", "TR", "+905321234567")
    kayit = _denemeler(depo)[0]
    assert kayit["masked"] == ""
    assert "5321234567" not in str(kayit)
