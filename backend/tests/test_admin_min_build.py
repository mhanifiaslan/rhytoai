"""Zorunlu güncelleme anahtarı — admin uçları (PBZ).

Değişmezler:
- `/admin/min-build` GET/POST admin claim'siz 403.
- Negatif / 100000 üstü eşik 422; gerekçe (≥3 karakter) ZORUNLU.
- K9: `min_build > 0` ise `appBuild >= min_build` olan en az bir kullanıcı
  canlı görülmüş olmalı — yoksa 400 ve doküman DOKUNULMAZ. Yazım hatasıyla
  (350 yerine 35) herkesi kilitlemek böyle imkânsız.
- Sıfır (geri alma) her zaman kabul.
- Başarılı yazım: config/app {minBuild, reason, updatedBy, updatedAt} +
  denetim izi `config.min_build` + memo sıfırlanır → kapı AYNI süreçte
  hemen devreye girer.
- GET: {min_build, env_floor, doc, below_min_live}.

Çalıştırma:  .venv\\Scripts\\python.exe -m pytest tests/test_admin_min_build.py -q
"""
from __future__ import annotations

import datetime as dt
import itertools

import pytest
from fastapi.testclient import TestClient

from core import app_gate, config
from main import app

YOL = "/api/v1/admin/min-build"
KAPILI_YOL = "/api/v1/astrology/olmayan-uc"  # kapı geçerse 404, kilitliyse 426


# ---------------------------------------------------------------------------
# Bellek içi sahte Firestore — kullanılan yüzeyler:
# users: where(filter).limit(1).stream(), where(filter).count().get()
# config/app: document().get()/set(merge) · adminAudit: document().set()
# ---------------------------------------------------------------------------

class _Anlik:
    def __init__(self, doc_id, veri):
        self.id = doc_id
        self._veri = veri
        self.exists = veri is not None

    def to_dict(self):
        return dict(self._veri) if self._veri else None


class _Sorgu:
    def __init__(self, satirlar):
        self._satirlar = list(satirlar)

    def where(self, filter=None):
        alan, islem, deger = filter.field_path, filter.op_string, filter.value

        def uyar(v):
            x = v[1].get(alan)
            if x is None:  # alanı olmayan doküman eşitsizliğe girmez
                return False
            return {">=": x >= deger, "<": x < deger,
                    ">": x > deger, "==": x == deger}[islem]
        return _Sorgu([v for v in self._satirlar if uyar(v)])

    def limit(self, n):
        return _Sorgu(self._satirlar[:n])

    def stream(self):
        return [_Anlik(d, v) for d, v in self._satirlar]

    def count(self):
        adet = len(self._satirlar)

        class _Sonuc:
            def get(self):
                class _Deger:
                    value = adet
                return [[_Deger()]]
        return _Sonuc()


class _Dokuman:
    def __init__(self, depo, yol):
        self._depo = depo
        self._yol = yol

    def get(self):
        return _Anlik(self._yol.rsplit("/", 1)[-1], self._depo.docs.get(self._yol))

    def set(self, veri, merge=False):
        mevcut = dict(self._depo.docs.get(self._yol) or {}) if merge else {}
        mevcut.update(veri)
        self._depo.docs[self._yol] = mevcut


class _Koleksiyon(_Sorgu):
    def __init__(self, depo, ad):
        super().__init__([(y.split("/", 1)[1], v)
                          for y, v in depo.docs.items()
                          if y.startswith(ad + "/") and y.count("/") == 1])
        self._depo = depo
        self._ad = ad

    def document(self, doc_id=None):
        if doc_id is None:
            doc_id = f"oto{next(self._depo.sayac)}"
        return _Dokuman(self._depo, f"{self._ad}/{doc_id}")


class SahteFirestore:
    def __init__(self, docs=None):
        self.docs = dict(docs or {})
        self.sayac = itertools.count(1)

    def collection(self, ad):
        return _Koleksiyon(self, ad)

    def izler(self):
        return [v for k, v in self.docs.items() if k.startswith("adminAudit/")]


@pytest.fixture()
def depo(monkeypatch):
    """Admin claim açık (DEV_ADMIN), env tabanı 0, memo temiz.

    `core.firestore.get_client` TEK yerden patch'lenir; app_gate ve
    api.admin (denetim izi) aynı modül nesnesini kullanıyor."""
    sahte = SahteFirestore()
    monkeypatch.setattr(app_gate.firestore_client, "get_client", lambda: sahte)
    monkeypatch.setattr(config, "DEV_MODE", True)
    monkeypatch.setattr(config, "DEV_ADMIN", True)
    monkeypatch.setattr(config, "MIN_APP_BUILD", 0)
    app_gate.reset_memo()
    yield sahte
    app_gate.reset_memo()


# Kota kovası Authorization özetine bağlı; her test kendi başlığını verir.
# Bozuk Bearer DEV_MODE'da dev-user'a düşer, DEV_ADMIN onu admin yapar.
def _baslik(ad: str, **ek: str) -> dict:
    return {"Authorization": f"Bearer esik-testi-{ad}", **ek}


def test_claim_sart(depo, monkeypatch):
    monkeypatch.setattr(config, "DEV_ADMIN", False)
    with TestClient(app) as client:
        okuma = client.get(YOL, headers=_baslik("claim-get"))
        yazma = client.post(YOL, json={"min_build": 0, "reason": "deneme"},
                            headers=_baslik("claim-post"))
    assert okuma.status_code == 403
    assert yazma.status_code == 403
    assert "config/app" not in depo.docs


@pytest.mark.parametrize("govde", [
    {"min_build": -1, "reason": "geçerli gerekçe"},
    {"min_build": 100001, "reason": "geçerli gerekçe"},
    {"min_build": 0},                       # gerekçe yok
    {"min_build": 0, "reason": "ab"},       # gerekçe kısa
    {"reason": "geçerli gerekçe"},          # eşik yok
])
def test_sema_422(depo, govde):
    with TestClient(app) as client:
        yanit = client.post(YOL, json=govde, headers=_baslik("sema"))
    assert yanit.status_code == 422, govde
    assert "config/app" not in depo.docs
    assert depo.izler() == []


def test_ustunde_kullanici_yoksa_400(depo):
    """K9: 34 görülmüş, 35 hiç görülmemiş → 35 yazılamaz."""
    depo.docs["users/u1"] = {"appBuild": 34}
    with TestClient(app) as client:
        yanit = client.post(YOL, json={"min_build": 35,
                                       "reason": "1.15.0+35 mağazada"},
                            headers=_baslik("yok"))
    assert yanit.status_code == 400
    assert "cihazda" in yanit.json()["detail"]
    assert "config/app" not in depo.docs
    assert depo.izler() == []
    assert app_gate.current_min_build() == 0


def test_alani_olmayan_kullanici_esigi_dogrulamaz(depo):
    """≤34 istemciler alanı hiç taşımaz; onlar 'görülmüş' sayılamaz."""
    depo.docs["users/u1"] = {"displayName": "eski"}
    with TestClient(app) as client:
        yanit = client.post(YOL, json={"min_build": 1, "reason": "deneme x"},
                            headers=_baslik("alansiz"))
    assert yanit.status_code == 400


def test_sifir_her_zaman_kabul(depo):
    """Geri alma kilidin önkoşuluna bağlanamaz — kullanıcı hiç yokken de."""
    with TestClient(app) as client:
        yanit = client.post(YOL, json={"min_build": 0, "reason": "geri alma"},
                            headers=_baslik("sifir"))
    assert yanit.status_code == 200
    assert depo.docs["config/app"]["minBuild"] == 0
    assert [i["action"] for i in depo.izler()] == ["config.min_build"]


def test_yazar_audit_ve_kapi_hemen_devreye_girer(depo):
    depo.docs["users/u1"] = {"appBuild": 34}
    depo.docs["users/u2"] = {"appBuild": 35}
    with TestClient(app) as client:
        # Yazımdan önce kapı kapalı: başlıksız da geçer.
        assert client.get(KAPILI_YOL,
                          headers=_baslik("once")).status_code == 404

        yanit = client.post(YOL, json={"min_build": 35,
                                       "reason": "1.15.0+35 mağazada"},
                            headers=_baslik("yaz"))
        assert yanit.status_code == 200
        govde = yanit.json()
        assert govde["min_build"] == 35
        assert govde["below_min_live"] == 1

        # Memo sıfırlandı: aynı süreçte bir sonraki istek kilitli.
        eski = client.get(KAPILI_YOL,
                          headers=_baslik("sonra-eski", **{"X-App-Build": "34"}))
        yeni = client.get(KAPILI_YOL,
                          headers=_baslik("sonra-yeni", **{"X-App-Build": "35"}))
    assert eski.status_code == 426
    assert yeni.status_code == 404

    dokuman = depo.docs["config/app"]
    assert dokuman["minBuild"] == 35
    assert dokuman["reason"] == "1.15.0+35 mağazada"
    assert dokuman["updatedBy"] == "dev-user"
    assert isinstance(dokuman["updatedAt"], dt.datetime)

    izler = depo.izler()
    assert len(izler) == 1
    assert izler[0]["action"] == "config.min_build"
    assert izler[0]["adminUid"] == "dev-user"
    assert izler[0]["params"] == {"min_build": 35,
                                  "reason": "1.15.0+35 mağazada"}


def test_get_durum(depo, monkeypatch):
    monkeypatch.setattr(config, "MIN_APP_BUILD", 10)
    depo.docs["config/app"] = {"minBuild": 35, "reason": "x", "updatedBy": "a"}
    depo.docs["users/u1"] = {"appBuild": 34}
    depo.docs["users/u2"] = {"appBuild": 35}
    depo.docs["users/u3"] = {"appBuild": 36}
    depo.docs["users/u4"] = {"displayName": "alansız"}
    with TestClient(app) as client:
        yanit = client.get(YOL, headers=_baslik("durum"))
    assert yanit.status_code == 200
    govde = yanit.json()
    assert govde["min_build"] == 35
    assert govde["env_floor"] == 10
    assert govde["doc"]["minBuild"] == 35
    assert govde["doc"]["reason"] == "x"
    # Alanı olmayan u4 sayılmaz — o adminStats builds.unknown'da.
    assert govde["below_min_live"] == 1


def test_get_esik_kapaliyken(depo):
    with TestClient(app) as client:
        yanit = client.get(YOL, headers=_baslik("kapali"))
    govde = yanit.json()
    assert govde["min_build"] == 0
    assert govde["doc"] is None
    assert govde["below_min_live"] == 0


def test_env_tabani_dokumandan_buyukse_o_gecerli(depo, monkeypatch):
    """Panel 0 yazsa da env tabanı 40 → etkin eşik 40; yanıt ikisini ayırır."""
    monkeypatch.setattr(config, "MIN_APP_BUILD", 40)
    with TestClient(app) as client:
        yanit = client.post(YOL, json={"min_build": 0, "reason": "geri alma"},
                            headers=_baslik("taban"))
    govde = yanit.json()
    assert govde["min_build"] == 40
    assert govde["env_floor"] == 40
    assert govde["doc"]["minBuild"] == 0


def test_firestore_yokken_500(depo, monkeypatch):
    monkeypatch.setattr(app_gate.firestore_client, "get_client", lambda: None)
    with TestClient(app) as client:
        yanit = client.post(YOL, json={"min_build": 0, "reason": "geri alma"},
                            headers=_baslik("fs-yok"))
    assert yanit.status_code == 500
