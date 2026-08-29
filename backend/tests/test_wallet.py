"""Token cüzdanının değişmezleri (Revize R1).

Cüzdan PARA taşır; buradaki her test gerçek bir kayıp senaryosunu tutuyor:

* Yarış: iki eşzamanlı istek aynı bakiyeyi iki kez harcayamaz (transaction).
* Webhook yeniden denemesi aynı paketi iki kez yükleyemez (event-id defteri).
* Paket iadesi kullanıcının AYRI ödediği aboneliğini kapatamaz (ürün ayrımı).
* Sönmüş abonelikten kalan aylık hak harcanamaz; satın alınan bakiye yaşar.
"""
from __future__ import annotations

import datetime as dt

import pytest
from fastapi import HTTPException

from core import wallet


# ---------------------------------------------------------------------------
# Bellek içi sahte Firestore — transaction dahil
# ---------------------------------------------------------------------------

class SahteAnlik:
    def __init__(self, data):
        self._data = data

    @property
    def exists(self):
        return self._data is not None

    def to_dict(self):
        return dict(self._data) if self._data else {}


class SahteDoc:
    def __init__(self, depo: dict, yol: str):
        self._depo = depo
        self._yol = yol

    def get(self, transaction=None):
        return SahteAnlik(self._depo.get(self._yol))

    def set(self, data, merge=False):
        mevcut = dict(self._depo.get(self._yol) or {}) if merge else {}
        for k, v in data.items():
            if type(v).__name__ == "Increment":
                mevcut[k] = int(mevcut.get(k, 0)) + v.value
            else:
                mevcut[k] = v
        self._depo[self._yol] = mevcut

    def collection(self, ad):
        return SahteKoleksiyon(self._depo, f"{self._yol}/{ad}")


class SahteKoleksiyon:
    _oto_sayac = 0

    def __init__(self, depo: dict, yol: str):
        self._depo = depo
        self._yol = yol

    def document(self, ad=None):
        # Gerçek istemcide argümansız document() otomatik kimlik üretir —
        # debit defteri (AP-turu) bu yolu kullanıyor.
        if ad is None:
            SahteKoleksiyon._oto_sayac += 1
            ad = f"oto-{SahteKoleksiyon._oto_sayac}"
        return SahteDoc(self._depo, f"{self._yol}/{ad}")


class SahteTransaction:
    def set(self, ref, data):
        ref.set(data)


class SahteClient:
    def __init__(self, depo: dict):
        self._depo = depo

    def collection(self, ad):
        return SahteKoleksiyon(self._depo, ad)

    def transaction(self):
        return SahteTransaction()


@pytest.fixture()
def depo(monkeypatch):
    """Sahte Firestore + kapalı abonelik varsayılanı."""
    veriler: dict = {}
    client = SahteClient(veriler)
    monkeypatch.setattr(wallet.firestore_client, "get_client", lambda: client)
    # Gerçek `transactional` gerçek Transaction ister; sahtede kimliğe iner.
    monkeypatch.setattr("google.cloud.firestore.transactional", lambda f: f)
    # Modül üzerinden yamalanıyor: wallet entitlements'a DİNAMİK erişir
    # (kopyalanmış ad monkeypatch'i görmez — bir kez yaşandı).
    monkeypatch.setattr(wallet.entitlements, "get_subscription",
                        lambda uid: {"active": False})
    monkeypatch.setattr(wallet.entitlements, "is_subscriber",
                        lambda uid: False)
    monkeypatch.setattr(wallet, "TOKENS_ENFORCE", True)
    return veriler


def _cuzdan_yaz(depo, uid="u1", **alanlar):
    depo[f"users/{uid}/private/wallet"] = alanlar


def _cuzdan(depo, uid="u1"):
    return depo.get(f"users/{uid}/private/wallet", {})


def _defter(depo, uid="u1"):
    """Ledger kayıtları (yazım sırasıyla — sahte depo dict'i eklemeli)."""
    onek = f"users/{uid}/private/wallet/ledger/"
    return [v for k, v in depo.items() if k.startswith(onek)]


def _abone_yap(monkeypatch, expires: dt.datetime):
    monkeypatch.setattr(wallet.entitlements, "get_subscription",
                        lambda uid: {"active": True, "expiresAt": expires})
    monkeypatch.setattr(wallet.entitlements, "is_subscriber",
                        lambda uid: True)


_DONEM = dt.datetime(2026, 9, 1, tzinfo=dt.timezone.utc)


# ---------------------------------------------------------------------------
# Harcama sırası
# ---------------------------------------------------------------------------

def test_once_allowance_sonra_purchased(depo, monkeypatch):
    """Yanacak olan önce harcanır; parayla alınan bakiye korunur."""
    _abone_yap(monkeypatch, _DONEM)
    _cuzdan_yaz(depo, allowance=3, allowanceExpiresAt=_DONEM, purchased=10)

    wallet.spend("u1", "natal")  # bedel 5: 3 allowance + 2 purchased

    assert _cuzdan(depo)["allowance"] == 0
    assert _cuzdan(depo)["purchased"] == 8


def test_yetersiz_bakiye_402_ve_baslik(depo, monkeypatch):
    """402'nin yanında X-Paywall-Reason: tokens — istemci paywall yerine
    token mağazasını bu başlıkla seçiyor (detail düz kullanıcı metni)."""
    _abone_yap(monkeypatch, _DONEM)
    _cuzdan_yaz(depo, allowance=1, allowanceExpiresAt=_DONEM, purchased=1)

    with pytest.raises(HTTPException) as exc:
        wallet.spend("u1", "natal")  # bedel 5 > 2

    assert exc.value.status_code == 402
    assert exc.value.headers["X-Paywall-Reason"] == "tokens"
    # Reddedilen istek bakiyeyi DEĞİŞTİRMEZ.
    assert _cuzdan(depo)["allowance"] == 1
    assert _cuzdan(depo)["purchased"] == 1


def test_kuru_calisma_reddetmez(depo, monkeypatch):
    """TOKENS_ENFORCE=0: eski mobil sürümler yayılana kadar üretim bu kipte."""
    monkeypatch.setattr(wallet, "TOKENS_ENFORCE", False)
    _abone_yap(monkeypatch, _DONEM)
    _cuzdan_yaz(depo, allowance=0, allowanceExpiresAt=_DONEM, purchased=0)

    wallet.spend("u1", "natal")  # fırlatmamalı


def test_firestore_yokken_istek_dusmez(monkeypatch):
    """Fail-open: altyapı sorunu kullanıcının suçu değil."""
    monkeypatch.setattr(wallet.firestore_client, "get_client", lambda: None)
    wallet.spend("u1", "chat")  # fırlatmamalı


# ---------------------------------------------------------------------------
# Dönem tazeleme
# ---------------------------------------------------------------------------

def test_tembel_tazeleme_yeni_donemde_hak_verir(depo, monkeypatch):
    """Webhook RENEWAL'i kaçırsa bile kullanıcı yeni dönemde hakkını alır."""
    eski_donem = dt.datetime(2026, 8, 1, tzinfo=dt.timezone.utc)
    _abone_yap(monkeypatch, _DONEM)
    _cuzdan_yaz(depo, allowance=0, allowanceExpiresAt=eski_donem, purchased=0)

    wallet.spend("u1", "chat")  # bedel 1, tazelenen 300'den düşer

    assert _cuzdan(depo)["allowance"] == wallet.MONTHLY_TOKEN_ALLOWANCE - 1


def test_sonmus_abonelikte_allowance_harcanamaz(depo, monkeypatch):
    """Dönem yoksa hak da yok; yalnızca satın alınan bakiye geçerli."""
    _cuzdan_yaz(depo, allowance=50, allowanceExpiresAt=_DONEM, purchased=3)

    wallet.spend("u1", "chat")  # abone DEĞİL: 1 token purchased'dan düşmeli

    assert _cuzdan(depo)["allowance"] == 0
    assert _cuzdan(depo)["purchased"] == 2


def test_reset_allowance_idempotent(depo, monkeypatch):
    """Aynı dönemin tekrarlanan webhook'u hakkı iki kez veremez."""
    wallet.reset_allowance("u1", _DONEM)
    _cuzdan_yaz(depo, **{**_cuzdan(depo), "allowance": 100})  # kısmen harcandı
    wallet.reset_allowance("u1", _DONEM)  # AYNI dönem tekrar

    assert _cuzdan(depo)["allowance"] == 100  # tazelenmedi


# ---------------------------------------------------------------------------
# Kredi ve iade
# ---------------------------------------------------------------------------

def test_kredi_idempotent(depo):
    """Webhook yeniden denemesi paketi iki kez yükleyemez."""
    wallet.credit_pack("u1", "rytho_tokens_small", "evt-1")
    wallet.credit_pack("u1", "rytho_tokens_small", "evt-1")

    assert _cuzdan(depo)["purchased"] == 100  # 200 değil


def test_farkli_olaylar_ayri_yuklenir(depo):
    """Aynı paketi gerçekten iki kez almak iki kez yükler."""
    wallet.credit_pack("u1", "rytho_tokens_small", "evt-1")
    wallet.credit_pack("u1", "rytho_tokens_small", "evt-2")

    assert _cuzdan(depo)["purchased"] == 200


def test_iade_sifirda_kelepcelenir(depo):
    """Bakiye harcanmışsa iade eksiye düşürmez — borç defteri tutmayız."""
    wallet.credit_pack("u1", "rytho_tokens_small", "evt-1")
    _cuzdan_yaz(depo, **{**_cuzdan(depo), "purchased": 30})  # 70'i harcandı

    wallet.debit_refund("u1", "rytho_tokens_small", "evt-1")

    assert _cuzdan(depo)["purchased"] == 0


def test_taninmayan_urun_kredi_yuklemez(depo):
    assert wallet.credit_pack("u1", "bilinmeyen_urun", "evt-9") is False
    assert _cuzdan(depo) == {}


def test_llm_iadesi_purchased_a_gider(depo, monkeypatch):
    """İade purchased'a yazılır: devrettiği için asla yanmaz — kullanıcı
    lehine yanılmak doğru."""
    _cuzdan_yaz(depo, allowance=0, allowanceExpiresAt=None, purchased=0)
    wallet.refund_spend("u1", "natal")
    assert _cuzdan(depo)["purchased"] == 5


# ---------------------------------------------------------------------------
# Harcama defteri (AP-turu) — debit kayıtları bakiye mutasyonunu aynalar
# ---------------------------------------------------------------------------
# Not: sahte `transactional → kimlik` indirgemesi (fixture) gerçek retry
# semantiğini göremez; çift-yazım güvencesi gerçek kütüphanenin transaction
# TAMPONUNDAN gelir (yazımlar yalnız başarılı commit'te işlenir ve her
# retry gövdeyi — ledger_ref dahil — sıfırdan kurar).

def test_harcama_defterde_kirilimla_izlenir(depo, monkeypatch):
    """Debit kaydı: feature + tutar + allowance/purchased kırılımı."""
    _abone_yap(monkeypatch, _DONEM)
    _cuzdan_yaz(depo, allowance=2, allowanceExpiresAt=_DONEM, purchased=3)

    wallet.spend("u1", "dyad")  # bedel 3: 2 allowance + 1 purchased

    kayitlar = _defter(depo)
    assert len(kayitlar) == 1
    kayit = kayitlar[0]
    assert kayit["type"] == "debit"
    assert kayit["feature"] == "dyad"
    assert kayit["amount"] == 3
    assert kayit["allowancePart"] == 2
    assert kayit["purchasedPart"] == 1


def test_kuru_calismada_da_debit_yazilir(depo, monkeypatch):
    """ENFORCE=0'da YETERLİ bakiye DÜŞÜYOR (kod gerçeği) — defter bakiye
    mutasyonunu aynalar, bayraktan bağımsız."""
    monkeypatch.setattr(wallet, "TOKENS_ENFORCE", False)
    _abone_yap(monkeypatch, _DONEM)
    _cuzdan_yaz(depo, allowance=10, allowanceExpiresAt=_DONEM, purchased=0)

    wallet.spend("u1", "chat")

    assert _cuzdan(depo)["allowance"] == 9
    assert [k["type"] for k in _defter(depo)] == ["debit"]


def test_yetersiz_bakiyede_defter_bos_kalir(depo, monkeypatch):
    """Bakiye yetmeyip yazım olmayan yol (kuru çalışmada bile) hiçbir
    ledger kaydı üretmez — düşmeyen jetonun izi olmaz."""
    monkeypatch.setattr(wallet, "TOKENS_ENFORCE", False)
    _abone_yap(monkeypatch, _DONEM)
    _cuzdan_yaz(depo, allowance=1, allowanceExpiresAt=_DONEM, purchased=0)

    wallet.spend("u1", "natal")  # bedel 5 > 1; ENFORCE=0 → fırlatmaz

    assert _cuzdan(depo)["allowance"] == 1
    assert _defter(depo) == []


def test_llm_iadesi_deftere_yazilir(depo):
    wallet.refund_spend("u1", "natal")
    kayitlar = _defter(depo)
    assert len(kayitlar) == 1
    assert kayitlar[0]["type"] == "spend_refund"
    assert kayitlar[0]["feature"] == "natal"
    assert kayitlar[0]["amount"] == 5


def test_admin_kredisi_defter_ve_bakiye(depo):
    """credit_admin: purchased artar; kayıt gerekçe + adminUid taşır.
    Bilinçli olarak İDEMPOTENT DEĞİL — çift tıklama koruması panelde."""
    wallet.credit_admin("u1", 50, "paket gelmedi, telafi", "admin-1")
    wallet.credit_admin("u1", 50, "paket gelmedi, telafi", "admin-1")

    assert _cuzdan(depo)["purchased"] == 100  # iki ayrı olay
    kayitlar = [k for k in _defter(depo) if k["type"] == "admin"]
    assert len(kayitlar) == 2
    assert kayitlar[0]["reason"] == "paket gelmedi, telafi"
    assert kayitlar[0]["adminUid"] == "admin-1"


def test_admin_kredisi_pozitif_sart(depo):
    assert wallet.credit_admin("u1", 0, "sebep", "admin-1") is False
    assert wallet.credit_admin("u1", -5, "sebep", "admin-1") is False
    assert _cuzdan(depo) == {}


# ---------------------------------------------------------------------------
# Birleşik kapı (sohbet / iching)
# ---------------------------------------------------------------------------

class _Kullanici:
    uid = "u1"


def test_ucretsiz_gunluk_hak_token_dusurmez(depo, monkeypatch):
    monkeypatch.setattr("core.entitlements.consume_quota",
                        lambda uid, key, limit: True)
    harcandi = wallet.charge_metered(_Kullanici(), "chat", 5)
    assert harcandi is False
    assert _cuzdan(depo) == {}


def test_kota_bitince_paket_kurtarir(depo, monkeypatch):
    """Paket almak için abonelik ŞART DEĞİL — bilinçli ürün kararı."""
    monkeypatch.setattr("core.entitlements.consume_quota",
                        lambda uid, key, limit: False)
    _cuzdan_yaz(depo, allowance=0, allowanceExpiresAt=None, purchased=2)

    harcandi = wallet.charge_metered(_Kullanici(), "chat", 5)

    assert harcandi is True
    assert _cuzdan(depo)["purchased"] == 1


def test_kota_ve_paket_yoksa_402(depo, monkeypatch):
    monkeypatch.setattr("core.entitlements.consume_quota",
                        lambda uid, key, limit: False)

    with pytest.raises(HTTPException) as exc:
        wallet.charge_metered(_Kullanici(), "chat", 5)

    assert exc.value.status_code == 402


def test_onbellekli_kapi_pesin_harcamaz(depo, monkeypatch):
    """`metered_callbacks` hemen harcamaz; geri çağrı önbellek kaçırılınca
    çalışır — abone, aynı çekilişe ikinci bakışında ödemesin."""
    _abone_yap(monkeypatch, _DONEM)
    _cuzdan_yaz(depo, allowance=10, allowanceExpiresAt=_DONEM, purchased=0)

    spend_cb, refund_cb = wallet.metered_callbacks(_Kullanici(), "iching", 1)

    assert _cuzdan(depo)["allowance"] == 10  # henüz dokunulmadı
    spend_cb()
    assert _cuzdan(depo)["allowance"] == 8  # iching bedeli 2
    refund_cb()
    assert _cuzdan(depo)["purchased"] == 2  # iade purchased'a
