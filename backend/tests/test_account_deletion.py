"""Faz 7a testleri: hesap silme.

Silme mağaza zorunlulugu (Apple 5.1.1(v), Google Play) ve tek basina red
sebebi. Ama asil risk redde ugramak degil: bir koleksiyonu atlarsak
"hesabimi sildim" diyen kullanicinin verisi sistemde kalir ve bunu kimse
fark etmez. Bu yuzden testler "silindi mi" degil, HANGI YOLLARIN
DOKUNULDUGUNU dogruluyor.

Calistirma:  .venv\\Scripts\\python.exe -m pytest tests/test_account_deletion.py -q
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from services import account_service

try:
    from main import app
    _APP_IMPORT_ERROR = None
except Exception as exc:  # pragma: no cover
    app = None
    _APP_IMPORT_ERROR = str(exc)

uygulama_gerekir = pytest.mark.skipif(
    _APP_IMPORT_ERROR is not None,
    reason=f"FastAPI uygulamasi ice aktarilamadi: {_APP_IMPORT_ERROR}",
)


# --------------------------------------------------------------------------
# Asgari sahte Firestore
# --------------------------------------------------------------------------

class _Anlik:
    def __init__(self, kimlik, veri, referans):
        self.id = kimlik
        self._veri = veri
        self.reference = referans

    @property
    def exists(self):
        return self._veri is not None

    def to_dict(self):
        return dict(self._veri) if self._veri is not None else None


class _Dokuman:
    def __init__(self, store, yol):
        self._store = store
        self._yol = yol

    def collection(self, ad):
        return _Koleksiyon(self._store, f"{self._yol}/{ad}")

    def get(self):
        return _Anlik(self._yol.rsplit("/", 1)[-1],
                      self._store.veriler.get(self._yol), self)

    def set(self, veri, merge=False):
        self._store.veriler[self._yol] = dict(veri)

    def delete(self):
        self._store.veriler.pop(self._yol, None)
        self._store.silinenler.append(self._yol)


class _Sorgu:
    def __init__(self, store, yol, filtreler=None, limit=None):
        self._store = store
        self._yol = yol
        self._filtreler = filtreler or []
        self._limit = limit

    def where(self, filter=None, **_):
        return _Sorgu(self._store, self._yol,
                      self._filtreler + [(filter.field_path, filter.value)],
                      self._limit)

    def limit(self, n):
        return _Sorgu(self._store, self._yol, self._filtreler, n)

    def stream(self):
        sonuc = []
        for yol, veri in list(self._store.veriler.items()):
            ust, _, kimlik = yol.rpartition("/")
            if ust != self._yol:
                continue
            if any(veri.get(alan) != deger for alan, deger in self._filtreler):
                continue
            sonuc.append(_Anlik(kimlik, veri, _Dokuman(self._store, yol)))
        return sonuc[:self._limit] if self._limit else sonuc


class _Koleksiyon(_Sorgu):
    def document(self, kimlik):
        return _Dokuman(self._store, f"{self._yol}/{kimlik}")


class SahteFirestore:
    """Yol -> veri sozlugu. Yol "users/u1/friends/u2" bicimindedir."""

    def __init__(self, veriler=None):
        self.veriler = dict(veriler or {})
        self.silinenler: list[str] = []

    def collection(self, ad):
        return _Koleksiyon(self, ad)


def ornek_store():
    """Silinmesi gereken her seyi iceren bir kullanici."""
    return SahteFirestore({
        "users/ben": {"username": "gezgin", "birthDate": "1990-05-12"},
        "users/ben/private/memory": {"facts": ["x"]},
        "users/ben/private/subscription": {"active": True},
        "users/ben/private/notifications": {"dailyLastSent": "2026-08-01"},
        "users/ben/friends/arkadas": {"status": "accepted"},
        "users/ben/nudges/n1": {"fromUid": "arkadas", "reaction": "shine"},
        "users/ben/blocked/kotu": {"at": 1},
        # Eklenen kisi (P-turu): ucuncu bir kisinin dogum verisi. Rizasi
        # ALINAMAMIS bir kisinin verisi, sahibi hesabini sildikten sonra
        # sunucuda kalamaz.
        "users/ben/people/p1": {"relation": "partner",
                                "birthDate": "1990-03-12"},
        # Karsi taraftaki izler
        "users/arkadas/friends/ben": {"status": "accepted"},
        "users/arkadas/nudges/n9": {"fromUid": "ben", "reaction": "streak"},
        "users/arkadas/nudges/n8": {"fromUid": "baskasi", "reaction": "shine"},
        # Herkese acik kart ve kullanici adi
        "publicProfiles/ben": {"uid": "ben"},
        "usernames/gezgin": {"uid": "ben"},
        # Kisiye ozel ve paylasimli onbellek
        "aiCache/a1": {"ownerUid": "ben", "value": "natal"},
        "aiCache/a2": {"ownerUid": "ben", "value": "gunluk"},
        "aiCache/a3": {"value": "burc yorumu"},  # paylasimli, sahipsiz
        # Baska kullanicinin verisi — dokunulmamali
        "users/arkadas": {"username": "deniz"},
        "usernames/deniz": {"uid": "arkadas"},
        "publicProfiles/arkadas": {"uid": "arkadas"},
    })


@pytest.fixture
def store(monkeypatch):
    s = ornek_store()
    monkeypatch.setattr(account_service.firestore_client, "get_client",
                        lambda: s)
    monkeypatch.setattr(account_service, "_delete_auth_user", lambda uid: True)
    return s


# --------------------------------------------------------------------------
# Silinmesi gerekenler
# --------------------------------------------------------------------------

@pytest.mark.parametrize("yol", [
    "users/ben",
    "users/ben/private/memory",
    "users/ben/private/subscription",
    "users/ben/private/notifications",
    "users/ben/friends/arkadas",
    "users/ben/nudges/n1",
    "users/ben/blocked/kotu",
    "users/ben/people/p1",
    "publicProfiles/ben",
    "usernames/gezgin",
])
def test_kullanici_verisi_silinir(store, yol):
    account_service.delete_account("ben")
    assert yol not in store.veriler, f"silinmedi: {yol}"


def test_karsi_taraftaki_arkadaslik_silinir(store):
    """Silinmezse arkadasin listesinde var olmayan bir kisi gorunur ve o
    kisiye ikili okuma denenebilir."""
    account_service.delete_account("ben")
    assert "users/arkadas/friends/ben" not in store.veriler


def test_gonderdigim_tepkiler_silinir(store):
    account_service.delete_account("ben")
    assert "users/arkadas/nudges/n9" not in store.veriler


def test_kisiye_ozel_uretimler_silinir(store):
    account_service.delete_account("ben")
    assert "aiCache/a1" not in store.veriler
    assert "aiCache/a2" not in store.veriler


# --------------------------------------------------------------------------
# Silinmemesi gerekenler
# --------------------------------------------------------------------------

def test_paylasimli_onbellek_korunur(store):
    """Bir kullanicinin hesabini silmesi herkesin burc yorumunu silmemeli."""
    account_service.delete_account("ben")
    assert "aiCache/a3" in store.veriler


def test_baskalarinin_verisi_korunur(store):
    account_service.delete_account("ben")
    for yol in ("users/arkadas", "usernames/deniz", "publicProfiles/arkadas",
                "users/arkadas/nudges/n8"):
        assert yol in store.veriler, f"baskasinin verisi silindi: {yol}"


def test_baskasinin_kullanici_adi_serbest_birakilmaz(monkeypatch):
    """Kullanici adi devredilmis olabilir; kayit baskasina aitse silinmemeli."""
    s = SahteFirestore({
        "users/ben": {"username": "gezgin"},
        "usernames/gezgin": {"uid": "baskasi"},  # ad devredilmis
    })
    monkeypatch.setattr(account_service.firestore_client, "get_client",
                        lambda: s)
    monkeypatch.setattr(account_service, "_delete_auth_user", lambda uid: True)

    account_service.delete_account("ben")
    assert "usernames/gezgin" in s.veriler


# --------------------------------------------------------------------------
# Sira ve dayaniklilik
# --------------------------------------------------------------------------

def test_kimlik_en_son_silinir(monkeypatch):
    """Kimligi once silseydik ve veri silme yarida kalsaydi, kullanici geri
    donup tekrar deneyemezdi."""
    s = ornek_store()
    monkeypatch.setattr(account_service.firestore_client, "get_client",
                        lambda: s)

    sira: list[str] = []
    monkeypatch.setattr(account_service, "_delete_auth_user",
                        lambda uid: sira.append("auth") or True)

    account_service.delete_account("ben")
    # Auth cagrisi yapildiginda kullanici dokumani coktan silinmis olmali.
    assert sira == ["auth"]
    assert "users/ben" not in s.veriler


def test_firestore_yoksa_silme_yapilmaz(monkeypatch):
    """Veriyi silemeden kimligi silmek, sahipsiz veri birakmak olurdu."""
    monkeypatch.setattr(account_service.firestore_client, "get_client",
                        lambda: None)

    def kimlik_silinmemeli(uid):
        raise AssertionError("Firestore yokken kimlik silinmemeli")

    monkeypatch.setattr(account_service, "_delete_auth_user",
                        kimlik_silinmemeli)

    with pytest.raises(RuntimeError):
        account_service.delete_account("ben")


def test_sayim_dondurulur(store):
    sayim = account_service.delete_account("ben")
    assert sayim["user"] == 1
    assert sayim["publicProfile"] == 1
    assert sayim["username"] == 1
    assert sayim["friendEdges"] == 1
    assert sayim["sentNudges"] == 1
    assert sayim["aiCache"] == 2
    assert sayim["auth"] == 1


def test_kimlik_silinemezse_sayimda_gorunur(monkeypatch):
    """Veri silindi ama kimlik kaldiysa bu sessizce gecilmemeli."""
    s = ornek_store()
    monkeypatch.setattr(account_service.firestore_client, "get_client",
                        lambda: s)
    monkeypatch.setattr(account_service, "_delete_auth_user", lambda uid: False)

    sayim = account_service.delete_account("ben")
    assert sayim["auth"] == 0


# --------------------------------------------------------------------------
# Uc davranisi
# --------------------------------------------------------------------------

@pytest.fixture
def gercek_kullanici():
    """Dogrulanmis (anonim olmayan) bir oturum.

    Gelistirme modunda `get_current_user` anonim bir kullanici donduruyor ve
    uc onu bilincli olarak reddediyor — silinecek gercek bir hesap yok.
    """
    from core.auth import AuthUser, get_current_user

    app.dependency_overrides[get_current_user] = lambda: AuthUser(
        uid="gercek-uid", email="a@b.c")
    yield
    app.dependency_overrides.clear()


@uygulama_gerekir
def test_uc_yalnizca_kendi_hesabini_siler(monkeypatch, gercek_kullanici):
    """Hedef kimlik govdeden degil, dogrulanmis oturumdan alinmali; aksi
    halde gecerli oturumu olan herkes baskasinin hesabini silebilirdi."""
    from api import account

    silinen: list[str] = []
    monkeypatch.setattr(account.account_service, "delete_account",
                        lambda uid: silinen.append(uid) or {"user": 1})

    with TestClient(app) as client:
        yanit = client.request(
            "DELETE", "/api/v1/account/me",
            json={"uid": "baskasi"},  # yok sayilmali
            headers={"Authorization": "Bearer test-silme"})

    assert yanit.status_code == 200
    assert silinen == ["gercek-uid"], "govdedeki uid dikkate alinmamali"


@uygulama_gerekir
def test_anonim_oturum_silme_yapamaz():
    """Gelistirme modundaki anonim kullanicinin silinecek hesabi yok."""
    with TestClient(app) as client:
        yanit = client.request("DELETE", "/api/v1/account/me",
                               headers={"Authorization": "Bearer test-anon"})
    assert yanit.status_code == 400


@uygulama_gerekir
def test_uc_hata_durumunda_ic_ayrinti_sizdirmaz(monkeypatch, gercek_kullanici):
    from api import account

    def patla(uid):
        raise RuntimeError("gizli_ic_detay")

    monkeypatch.setattr(account.account_service, "delete_account", patla)

    with TestClient(app, raise_server_exceptions=False) as client:
        yanit = client.request("DELETE", "/api/v1/account/me",
                               headers={"Authorization": "Bearer test-hata"})

    assert yanit.status_code == 500
    assert "gizli_ic_detay" not in yanit.text
