"""Rehber eşleşmesinin değişmezleri (Revize R3).

İki kritik garanti:

* **Karşılıklılık** — tek taraflı açık ayar kapalı tarafı GÖSTERMEZ.
  Aksi, telefon numarası bilinen herkesin uygulamadaki varlığını ifşa
  etmek olurdu (enumeration).
* **Durumsuzluk** — gelen hash listesi hiçbir yere yazılmaz. Test, sahte
  depoda isteğin öncesi ve sonrası arasında YENİ doküman doğmadığını
  doğruluyor.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from core import config

try:
    from main import app
    _APP_IMPORT_ERROR = None
except Exception as exc:  # pragma: no cover - ortama bagli
    app = None
    _APP_IMPORT_ERROR = str(exc)

uygulama_gerekir = pytest.mark.skipif(
    _APP_IMPORT_ERROR is not None,
    reason=f"FastAPI uygulamasi ice aktarilamadi: {_APP_IMPORT_ERROR}",
)


class _SahteAnlik:
    def __init__(self, data, doc_id=None):
        self._data = data
        # Gerçek Firestore snapshot'ında olduğu gibi doküman kimliği. I-turu:
        # /match eşleşen hash'i (doküman kimliği) yanıta koyuyor.
        self.id = doc_id

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
        return _SahteAnlik(self._depo.get(self._yol), self._yol.split("/")[-1])

    def set(self, data, merge=False):
        self._depo[self._yol] = dict(data)

    def collection(self, ad):
        return _SahteKoleksiyon(self._depo, f"{self._yol}/{ad}")


class _SahteKoleksiyon:
    def __init__(self, depo, yol):
        self._depo = depo
        self._yol = yol

    def document(self, ad):
        return _SahteDoc(self._depo, f"{self._yol}/{ad}")


class _SahteClient:
    def __init__(self, depo):
        self._depo = depo

    def collection(self, ad):
        return _SahteKoleksiyon(self._depo, ad)

    def get_all(self, refs):
        return [r.get() for r in refs]


def _depo_kur(monkeypatch, veriler):
    client = _SahteClient(veriler)
    monkeypatch.setattr("api.contacts.firestore_client.get_client",
                        lambda: client)
    return veriler


def _dev_kullanici(monkeypatch):
    """DEV_MODE dev-user kimliğiyle uç çağrısı."""
    monkeypatch.setattr(config, "DEV_MODE", True)


def _istek(client, hashes):
    return client.post("/api/v1/contacts/match", json={"hashes": hashes},
                       headers={"Authorization": "Bearer test"})


def _temel_veri(benim_ayarim=True):
    return {
        "users/dev-user": {"contactMatch": benim_ayarim},
        "phoneHashes/h-arkadas": {"uid": "u-arkadas"},
        "users/u-arkadas": {"contactMatch": True},
        "publicProfiles/u-arkadas": {"displayName": "Deniz",
                                     "username": "deniz",
                                     "sunSign": "Aslan ♌"},
        "phoneHashes/h-kapali": {"uid": "u-kapali"},
        "users/u-kapali": {"contactMatch": False},
        "publicProfiles/u-kapali": {"displayName": "Gizli"},
    }


@uygulama_gerekir
def test_karsilikli_acik_taraflar_eslesir(monkeypatch):
    _dev_kullanici(monkeypatch)
    _depo_kur(monkeypatch, _temel_veri())

    with TestClient(app) as client:
        yanit = _istek(client, ["h-arkadas"])

    assert yanit.status_code == 200
    kartlar = yanit.json()["matches"]
    assert len(kartlar) == 1
    assert kartlar[0]["username"] == "deniz"
    # Eşleşen hash geri döner (I-turu: istemci kişi→app-kullanıcı eşlemesi
    # kurup rehberini aktif/pasif ayırsın).
    assert kartlar[0]["hash"] == "h-arkadas"
    # Kart yalnızca türetilmiş alanlar + eşleşme hash'i taşır — doğum
    # verisi ASLA.
    assert set(kartlar[0]) <= {"uid", "hash", "displayName", "username",
                               "sunSign", "photoUrl"}


@uygulama_gerekir
def test_karsi_taraf_kapaliysa_GORUNMEZ(monkeypatch):
    """Tek taraflı açık ayar ifşa üretmez — enumeration kapısı."""
    _dev_kullanici(monkeypatch)
    _depo_kur(monkeypatch, _temel_veri())

    with TestClient(app) as client:
        yanit = _istek(client, ["h-kapali"])

    assert yanit.status_code == 200
    assert yanit.json()["matches"] == []


@uygulama_gerekir
def test_kendi_ayarim_kapaliysa_403(monkeypatch):
    _dev_kullanici(monkeypatch)
    _depo_kur(monkeypatch, _temel_veri(benim_ayarim=False))

    with TestClient(app) as client:
        yanit = _istek(client, ["h-arkadas"])

    assert yanit.status_code == 403


@uygulama_gerekir
def test_hash_listesi_SAKLANMAZ(monkeypatch):
    """Durumsuzluk: istek sonrası depoda yeni doküman yok."""
    _dev_kullanici(monkeypatch)
    veriler = _depo_kur(monkeypatch, _temel_veri())
    onceki = set(veriler)

    with TestClient(app) as client:
        _istek(client, ["h-arkadas", "h-kapali", "h-hic-yok"])

    assert set(veriler) == onceki, "eşleşme ucu bir şey YAZDI"


@uygulama_gerekir
def test_kendim_eslesmede_donmem(monkeypatch):
    _dev_kullanici(monkeypatch)
    veri = _temel_veri()
    veri["phoneHashes/h-ben"] = {"uid": "dev-user"}
    _depo_kur(monkeypatch, veri)

    with TestClient(app) as client:
        yanit = _istek(client, ["h-ben"])

    assert yanit.json()["matches"] == []


@uygulama_gerekir
def test_tavan_asimi_422(monkeypatch):
    _dev_kullanici(monkeypatch)
    _depo_kur(monkeypatch, _temel_veri())

    with TestClient(app) as client:
        yanit = _istek(client, [f"h{i}" for i in range(2001)])

    assert yanit.status_code == 422
