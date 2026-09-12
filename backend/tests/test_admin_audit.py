"""Denetim izi v2 (AD3): imleç, ön-iz (fail-closed), süzgeçli sayfalama.

Değişmezler:
- `core.cursor`: datetime `$ts` ile gidip gelir; bozuk/liste-olmayan
  imleç ValueError.
- `_audit(zorunlu=True)`: iz yazılamazsa 503 ve EYLEM YAPILMAZ —
  delete_account / update_user / set_min_build / add_payout ÇAĞRILMAZ.
- Başarılı ön-izli eylem: tek doküman, `phase` intent → done, `doneAt`.
- `audit_list`: eşitlik süzgeçleri + `at` aralığı + limit+1 → nextCursor;
  ikinci sayfa çakışmaz; `GET /admin/audit` bozuk imlece 400.

Buradaki `SahteFirestore` B1 testlerinin ortak sahtesidir (export ve
system testleri de içe aktarır): where(==,>=,<,>) · çoklu order_by ·
start_after(liste|sözlük) · limit · count · DELETE_FIELD · indeks
yoklaması için `bozuk_indeksler` kancası.
"""
from __future__ import annotations

import datetime as dt
import itertools
from typing import Any

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from core import auth, config, cursor
from core import firestore as firestore_client
from services import admin_service
from api import admin as admin_api

try:
    from google.cloud.firestore_v1 import DELETE_FIELD as _SIL
except Exception:  # pragma: no cover
    _SIL = object()

from main import app


# ---------------------------------------------------------------------------
# Ortak sahte Firestore
# ---------------------------------------------------------------------------

class FailedPrecondition(Exception):
    """google.api_core.exceptions.FailedPrecondition'ın adaşı — servis sınıf
    ADINA bakar, modüle değil."""


class _Anlik:
    def __init__(self, doc_id, veri):
        self.id = doc_id
        self._veri = veri
        self.exists = veri is not None

    def to_dict(self):
        return dict(self._veri) if self._veri is not None else None


class _Dokuman:
    def __init__(self, depo, yol):
        self._depo = depo
        self._yol = yol

    @property
    def id(self):
        return self._yol.rsplit("/", 1)[-1]

    def get(self, transaction=None):
        return _Anlik(self.id, self._depo.docs.get(self._yol))

    def set(self, veri, merge=False):
        mevcut = dict(self._depo.docs.get(self._yol) or {}) if merge else {}
        for k, v in veri.items():
            if v is _SIL:
                mevcut.pop(k, None)
            else:
                mevcut[k] = v
        self._depo.docs[self._yol] = mevcut

    def collection(self, ad):
        return _Koleksiyon(self._depo, f"{self._yol}/{ad}")


def _deger(satir, alan):
    return satir[0] if alan == "__name__" else satir[1].get(alan)


class _Sorgu:
    def __init__(self, depo, yol, filtreler=(), sira=(), imlec=None, n=None):
        self._depo = depo
        self._yol = yol
        self._filtreler = tuple(filtreler)
        self._sira = tuple(sira)
        self._imlec = imlec
        self._n = n

    def _kopya(self, **degisiklik):
        alanlar = dict(depo=self._depo, yol=self._yol, filtreler=self._filtreler,
                       sira=self._sira, imlec=self._imlec, n=self._n)
        alanlar.update(degisiklik)
        return _Sorgu(**alanlar)

    def where(self, filter=None):
        return self._kopya(filtreler=self._filtreler + (
            (filter.field_path, filter.op_string, filter.value),))

    def order_by(self, alan, direction="ASCENDING"):
        return self._kopya(sira=self._sira + ((alan, direction == "DESCENDING"),))

    def limit(self, n):
        return self._kopya(n=n)

    def start_after(self, imlec):
        if isinstance(imlec, dict):
            imlec = [imlec[alan] for alan, _ in self._sira]
        return self._kopya(imlec=list(imlec))

    def _satirlar(self):
        onek = self._yol + "/"
        satirlar = [(k[len(onek):], v) for k, v in self._depo.docs.items()
                    if k.startswith(onek) and "/" not in k[len(onek):]]
        if self._filtreler and self._sira and (
                self._yol, self._sira[0][0]) in self._depo.bozuk_indeksler:
            raise FailedPrecondition(f"indeks yok: {self._yol}/{self._sira[0][0]}")
        for alan, islem, hedef in self._filtreler:
            def uyar(s, alan=alan, islem=islem, hedef=hedef):
                x = _deger(s, alan)
                if islem == "==":
                    return x == hedef
                if x is None:
                    return False
                return {">=": x >= hedef, "<": x < hedef, ">": x > hedef,
                        "<=": x <= hedef}[islem]
            satirlar = [s for s in satirlar if uyar(s)]
        for alan, _ in self._sira:
            satirlar = [s for s in satirlar if _deger(s, alan) is not None]
        for alan, ters in reversed(self._sira):
            satirlar.sort(key=lambda s, alan=alan: _deger(s, alan), reverse=ters)
        if self._imlec is not None:
            def sonra(s):
                for (alan, ters), c in zip(self._sira, self._imlec):
                    v = _deger(s, alan)
                    if v == c:
                        continue
                    return (v < c) if ters else (v > c)
                return False
            satirlar = [s for s in satirlar if sonra(s)]
        if self._n is not None:
            satirlar = satirlar[:self._n]
        return satirlar

    def stream(self):
        return [_Anlik(d, v) for d, v in self._satirlar()]

    def count(self):
        adet = len(self._satirlar())

        class _Sonuc:
            def get(self):
                class _Deger:
                    value = adet
                return [[_Deger()]]
        return _Sonuc()


class _Koleksiyon(_Sorgu):
    def document(self, doc_id=None):
        if doc_id is None:
            doc_id = f"oto{next(self._depo.sayac)}"
        return _Dokuman(self._depo, f"{self._yol}/{doc_id}")


class SahteFirestore:
    def __init__(self, docs: dict[str, dict] | None = None):
        self.docs: dict[str, dict] = dict(docs or {})
        self.sayac = itertools.count(1)
        #: {(koleksiyon, ilk order_by alanı)} — süzgeç + sıralama bu çifte
        #: düşünce FailedPrecondition fırlatır (indeks yoklaması testi).
        self.bozuk_indeksler: set[tuple[str, str]] = set()
        #: Bu koleksiyona erişim fırlatır (fail-closed testi).
        self.kirik_koleksiyonlar: set[str] = set()

    def collection(self, ad):
        if ad in self.kirik_koleksiyonlar:
            raise RuntimeError(f"{ad} erişilemiyor")
        return _Koleksiyon(self, ad)

    def izler(self) -> list[dict[str, Any]]:
        return [dict(v, _id=k.split("/", 1)[1]) for k, v in self.docs.items()
                if k.startswith("adminAudit/")]


# ---------------------------------------------------------------------------
# core.cursor
# ---------------------------------------------------------------------------

_SIMDI = dt.datetime(2026, 9, 12, 10, 30, 15, 250000, tzinfo=dt.timezone.utc)


def test_cursor_gidis_donus_datetime_ve_dizgi():
    token = cursor.encode([_SIMDI, "abc", 7])
    assert "=" not in token and "+" not in token and "/" not in token
    geri = cursor.decode(token)
    assert geri[0] == _SIMDI
    assert geri[0].tzinfo is not None
    assert geri[1:] == ["abc", 7]


@pytest.mark.parametrize("bozuk", ["", "!!!", "e30", "bnVsbA", "MTIz"])
def test_cursor_bozuk_valueerror(bozuk):
    # "e30" = {}  · "bnVsbA" = null · "MTIz" = 123 — hiçbiri liste değil.
    with pytest.raises(ValueError):
        cursor.decode(bozuk)


# ---------------------------------------------------------------------------
# _audit / _audit_tamamla
# ---------------------------------------------------------------------------

def _sahip():
    return auth.AuthUser(uid="sahip", email="sahip@ornek.com", admin=True,
                         role="owner")


def test_audit_best_effort_firestore_yokken_none(monkeypatch):
    monkeypatch.setattr(firestore_client, "get_client", lambda: None)
    assert admin_api._audit(_sahip(), "x.y") is None


def test_audit_zorunlu_firestore_yokken_503(monkeypatch):
    monkeypatch.setattr(firestore_client, "get_client", lambda: None)
    with pytest.raises(HTTPException) as h:
        admin_api._audit(_sahip(), "x.y", zorunlu=True)
    assert h.value.status_code == 503
    assert h.value.detail == "Denetim izi yazılamadı; işlem yapılmadı."


def test_audit_kimlik_doner_ve_tamamla_ayni_dokumani_gunceller(monkeypatch):
    depo = SahteFirestore()
    monkeypatch.setattr(firestore_client, "get_client", lambda: depo)
    iz = admin_api._audit(_sahip(), "user.delete", target_uid="u1",
                          params={"reason": "r"}, zorunlu=True, phase="intent")
    assert iz
    kayit = depo.docs[f"adminAudit/{iz}"]
    assert kayit["phase"] == "intent"
    assert kayit["adminRole"] == "owner"
    assert kayit["params"] == {"reason": "r"}
    admin_api._audit_tamamla(iz, {"phase": "done", "rows": 3})
    kayit = depo.docs[f"adminAudit/{iz}"]
    assert kayit["phase"] == "done"
    assert kayit["rows"] == 3
    assert isinstance(kayit["doneAt"], dt.datetime)
    assert kayit["action"] == "user.delete"  # merge — eski alanlar durdu
    assert len(depo.izler()) == 1


def test_audit_tamamla_kimliksiz_sessiz(monkeypatch):
    depo = SahteFirestore()
    monkeypatch.setattr(firestore_client, "get_client", lambda: depo)
    admin_api._audit_tamamla(None, {"phase": "done"})
    assert depo.docs == {}


# ---------------------------------------------------------------------------
# Fail-closed: iz yazılamazsa eylem YAPILMAZ
# ---------------------------------------------------------------------------

class _SahteFbAuth:
    def __init__(self):
        self.guncellenen: list = []
        self.revoke_edilen: list = []

    def update_user(self, uid, disabled=None):
        self.guncellenen.append((uid, disabled))

    def revoke_refresh_tokens(self, uid):
        self.revoke_edilen.append(uid)


@pytest.fixture()
def kirik_iz(monkeypatch):
    """Owner DEV admin; adminAudit koleksiyonu fırlatıyor; yıkıcı
    servisler kayıt tutan sahtelerle değişti."""
    depo = SahteFirestore({"users/u1": {"email": "ayse@ornek.com",
                                        "appBuild": 40}})
    depo.kirik_koleksiyonlar.add("adminAudit")
    monkeypatch.setattr(firestore_client, "get_client", lambda: depo)
    monkeypatch.setattr(config, "DEV_MODE", True)
    monkeypatch.setattr(config, "DEV_ADMIN", True)
    monkeypatch.setattr(config, "DEV_ADMIN_ROLE", "owner")

    silinen: list = []
    from services import account_service
    monkeypatch.setattr(account_service, "delete_account",
                        lambda uid: silinen.append(uid))
    monkeypatch.setattr(admin_service, "user_360",
                        lambda uid: {"profile": {"email": "ayse@ornek.com"}})

    sahte_auth = _SahteFbAuth()
    import sys
    import firebase_admin
    monkeypatch.setattr(firebase_admin, "auth", sahte_auth, raising=False)
    monkeypatch.setitem(sys.modules, "firebase_admin.auth", sahte_auth)

    odemeler: list = []
    from services import partner_service
    monkeypatch.setattr(partner_service, "add_payout",
                        lambda *a: odemeler.append(a) or {"id": "p"})
    return {"depo": depo, "silinen": silinen, "auth": sahte_auth,
            "odemeler": odemeler}


def test_delete_iz_yazilamazsa_503_ve_hesap_durur(kirik_iz):
    with TestClient(app) as client:
        yanit = client.request("DELETE", "/api/v1/admin/users/u1",
                               json={"confirm": "SIL", "reason": "test-sil"})
    assert yanit.status_code == 503
    assert yanit.json()["detail"] == "Denetim izi yazılamadı; işlem yapılmadı."
    assert kirik_iz["silinen"] == []


def test_disable_iz_yazilamazsa_503_ve_kimlik_dokunulmaz(kirik_iz):
    with TestClient(app) as client:
        yanit = client.post("/api/v1/admin/users/u1/disable",
                            json={"disabled": True, "reason": "kotu"})
    assert yanit.status_code == 503
    assert kirik_iz["auth"].guncellenen == []
    assert kirik_iz["auth"].revoke_edilen == []


def test_min_build_iz_yazilamazsa_503_ve_esik_yazilmaz(kirik_iz):
    from core import app_gate
    app_gate.reset_memo()
    with TestClient(app) as client:
        yanit = client.post("/api/v1/admin/min-build",
                            json={"min_build": 0, "reason": "geri alma"})
    assert yanit.status_code == 503
    assert "config/app" not in kirik_iz["depo"].docs


def test_payout_iz_yazilamazsa_503_ve_odeme_yazilmaz(kirik_iz):
    with TestClient(app) as client:
        yanit = client.post("/api/v1/admin/partners/p1/payouts",
                            json={"amount": 10, "currency": "USD"})
    assert yanit.status_code == 503
    assert kirik_iz["odemeler"] == []


def test_delete_basarili_tek_iz_intent_to_done(kirik_iz):
    depo = kirik_iz["depo"]
    depo.kirik_koleksiyonlar.clear()
    with TestClient(app) as client:
        yanit = client.request("DELETE", "/api/v1/admin/users/u1",
                               json={"confirm": "SIL", "reason": "test-sil"})
    assert yanit.status_code == 200
    assert kirik_iz["silinen"] == ["u1"]
    izler = depo.izler()
    assert len(izler) == 1
    assert izler[0]["action"] == "user.delete"
    assert izler[0]["phase"] == "done"
    assert izler[0]["params"] == {"reason": "test-sil",
                                  "email": "ayse@ornek.com"}
    assert isinstance(izler[0]["doneAt"], dt.datetime)


def test_delete_eylem_duserse_iz_failed_kalir(kirik_iz, monkeypatch):
    depo = kirik_iz["depo"]
    depo.kirik_koleksiyonlar.clear()
    from services import account_service

    def patlar(uid):
        raise RuntimeError("Firestore düştü")
    monkeypatch.setattr(account_service, "delete_account", patlar)
    with TestClient(app) as client:
        yanit = client.request("DELETE", "/api/v1/admin/users/u1",
                               json={"confirm": "SIL", "reason": "test-sil"})
    assert yanit.status_code == 500
    izler = depo.izler()
    assert len(izler) == 1
    assert izler[0]["phase"] == "failed"
    assert "Firestore düştü" in izler[0]["error"]


def test_disable_basarili_authdisabled_aynasi(kirik_iz):
    depo = kirik_iz["depo"]
    depo.kirik_koleksiyonlar.clear()
    with TestClient(app) as client:
        yanit = client.post("/api/v1/admin/users/u1/disable",
                            json={"disabled": True, "reason": "kotu"})
    assert yanit.status_code == 200
    assert kirik_iz["auth"].guncellenen == [("u1", True)]
    assert depo.docs["users/u1"]["authDisabled"] is True
    assert depo.docs["users/u1"]["email"] == "ayse@ornek.com"  # merge
    assert [i["phase"] for i in depo.izler()] == ["done"]


# ---------------------------------------------------------------------------
# audit_list + GET /admin/audit
# ---------------------------------------------------------------------------

def _iz(i: int, action: str = "user.credit", admin_uid: str = "a1",
        target: str | None = "u1") -> dict:
    return {"adminUid": admin_uid, "action": action, "targetUid": target,
            "params": {}, "at": _SIMDI - dt.timedelta(minutes=i)}


@pytest.fixture()
def izli_depo(monkeypatch):
    depo = SahteFirestore()
    for i in range(5):
        depo.docs[f"adminAudit/iz{i}"] = _iz(i)
    depo.docs["adminAudit/izx"] = _iz(2, action="user.delete",
                                      admin_uid="a2", target="u9")
    # Aynı `at` (iz2 ile): __name__ DESC ikincil sıralama bunu ayırır.
    depo.docs["adminAudit/iz2b"] = _iz(2)
    monkeypatch.setattr(firestore_client, "get_client", lambda: depo)
    monkeypatch.setattr(config, "DEV_MODE", True)
    monkeypatch.setattr(config, "DEV_ADMIN", True)
    monkeypatch.setattr(config, "DEV_ADMIN_ROLE", "support")
    return depo


def test_audit_list_sayfalar_cakismaz(izli_depo):
    gorulen: list[str] = []
    imlec = None
    while True:
        sonuc = admin_service.audit_list(limit=3, cursor=imlec)
        assert len(sonuc["entries"]) <= 3
        gorulen.extend(e["id"] for e in sonuc["entries"])
        imlec = sonuc["nextCursor"]
        if imlec is None:
            break
    assert len(gorulen) == 7
    assert len(set(gorulen)) == 7
    # Yeniden eskiye: iz0 (en yeni) ilk, iz4 (en eski) son.
    assert gorulen[0] == "iz0"
    assert gorulen[-1] == "iz4"


def test_audit_list_son_sayfada_cursor_yok(izli_depo):
    sonuc = admin_service.audit_list(limit=50)
    assert len(sonuc["entries"]) == 7
    assert sonuc["nextCursor"] is None


def test_audit_list_suzgecler(izli_depo):
    assert [e["id"] for e in admin_service.audit_list(action="user.delete")
            ["entries"]] == ["izx"]
    assert [e["id"] for e in admin_service.audit_list(admin_uid="a2")
            ["entries"]] == ["izx"]
    assert [e["id"] for e in admin_service.audit_list(target_uid="u9")
            ["entries"]] == ["izx"]
    # at aralığı: [_SIMDI-3dk, _SIMDI-1dk) → iz3, iz2, iz2b, izx
    aralik = admin_service.audit_list(start=_SIMDI - dt.timedelta(minutes=3),
                                      end=_SIMDI - dt.timedelta(minutes=1))
    assert sorted(e["id"] for e in aralik["entries"]) == ["iz2", "iz2b", "iz3", "izx"]


def test_audit_list_bozuk_imlec_valueerror(izli_depo):
    with pytest.raises(ValueError):
        admin_service.audit_list(cursor="!!!")
    with pytest.raises(ValueError):
        admin_service.audit_list(cursor=cursor.encode(["tek"]))


def test_audit_ucu_sayfalama_ve_400(izli_depo):
    with TestClient(app) as client:
        ilk = client.get("/api/v1/admin/audit?limit=4")
        assert ilk.status_code == 200
        govde = ilk.json()
        assert len(govde["entries"]) == 4
        assert govde["nextCursor"]
        ikinci = client.get(f"/api/v1/admin/audit?limit=4&cursor={govde['nextCursor']}")
        assert ikinci.status_code == 200
        assert len(ikinci.json()["entries"]) == 3
        assert ikinci.json()["nextCursor"] is None
        ilk_ids = {e["id"] for e in govde["entries"]}
        assert ilk_ids.isdisjoint({e["id"] for e in ikinci.json()["entries"]})

        bozuk = client.get("/api/v1/admin/audit?cursor=%21%21%21")
        assert bozuk.status_code == 400
        buyuk = client.get("/api/v1/admin/audit?limit=201")
        assert buyuk.status_code == 422
        kotu_gun = client.get("/api/v1/admin/audit?from=2026-9-1")
        assert kotu_gun.status_code == 422


def test_audit_ucu_tarih_araligi_kapsayici(izli_depo):
    gun = _SIMDI.date().isoformat()
    with TestClient(app) as client:
        yanit = client.get(f"/api/v1/admin/audit?from={gun}&to={gun}&action=user.credit")
    assert yanit.status_code == 200
    ids = sorted(e["id"] for e in yanit.json()["entries"])
    assert ids == ["iz0", "iz1", "iz2", "iz2b", "iz3", "iz4"]
