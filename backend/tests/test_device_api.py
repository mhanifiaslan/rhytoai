"""Cihaz uçları (TC-turu) — HTTP sözleşmesi.

Değişmezler:

* `GET /device/status`, `POST /device/claim`, `DELETE /device/claim`
  **`require_plus` ARKASINDA DEĞİL**: kilit 409 fırlatsa bile 200. Aksi
  hâlde devralma imkânsız — 409'a düşen cihaz `/claim`'e de 409 alırdı.
* `POST /claim` token'daki `auth_time`'ı yazar; başlıksız 400; `claimed`
  dürüst (yazılamadıysa false).
* `DELETE /claim` yalnız sahipse siler; değilse `released: false`.
* Korumalı uçta 409 sözleşmesi: `detail` düz metin, öbür cihaz başlıklarda
  (`X-Device-Conflict`, `X-Device-Other-Platform`, `X-Device-Claimed-At`).
  Mobil kapı ekranı bu başlıkları okur.
* Admin `POST /users/{uid}/device/release` claim ister (403), kaydı siler,
  denetim izi `device.release`.

Kimlik `get_current_user` override'ıyla verilir — `auth_time` ancak böyle
kontrol edilir (DEV_MODE'un dev-user'ında 0). `require_admin` aynı
bağımlılıktan türediği için admin bayrağı da oradan geçer.

Çalıştırma:  .venv\\Scripts\\python.exe -m pytest tests/test_device_api.py -q
"""
from __future__ import annotations

import datetime as dt
import itertools

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from core import device, entitlements
from core.auth import AuthUser, get_current_user
from main import app

UTC = dt.timezone.utc
YOL = "/api/v1/device"
ADMIN_YOL = "/api/v1/admin/users/{uid}/device/release"
#: require_plus arkasındaki bir uç. Gövde BOŞ gönderilir: bağımlılıklar
#: (paywall + kilit) gövde doğrulamasından ÖNCE çözülür → kilit 409 verir,
#: vermezse 422. Gerçek rapor üreticisi (kerykeion/LLM) hiç koşmaz.
KORUMALI_YOL = "/api/v1/reports/daily"
BOS_GOVDE: dict = {}
CIHAZ_A = {"X-Device-Id": "cihaz-a"}
CIHAZ_B = {"X-Device-Id": "cihaz-b"}


def _t(saniye: float) -> dt.datetime:
    return dt.datetime.fromtimestamp(saniye, UTC)


# ---------------------------------------------------------------------------
# Bellek içi sahte Firestore — iç içe koleksiyon, otomatik kimlik (audit),
# get/set(merge)/delete. Kapı (app_gate) config/app'ı okur → yok → 0.
# ---------------------------------------------------------------------------

class _Anlik:
    def __init__(self, veri):
        self._veri = veri
        self.exists = veri is not None

    def to_dict(self):
        return dict(self._veri) if self._veri else {}


class _Dokuman:
    def __init__(self, depo, yol):
        self._depo = depo
        self._yol = yol

    def get(self):
        return _Anlik(self._depo.docs.get(self._yol))

    def set(self, veri, merge=False):
        mevcut = dict(self._depo.docs.get(self._yol) or {}) if merge else {}
        mevcut.update(veri)
        self._depo.docs[self._yol] = mevcut

    def delete(self):
        self._depo.docs.pop(self._yol, None)

    def collection(self, ad):
        return _Koleksiyon(self._depo, f"{self._yol}/{ad}")


class _Koleksiyon:
    def __init__(self, depo, yol):
        self._depo = depo
        self._yol = yol

    def document(self, doc_id=None):
        if doc_id is None:
            doc_id = f"oto{next(self._depo.sayac)}"
        return _Dokuman(self._depo, f"{self._yol}/{doc_id}")


class SahteFirestore:
    def __init__(self):
        self.docs: dict = {}
        self.sayac = itertools.count(1)

    def collection(self, ad):
        return _Koleksiyon(self, ad)

    def izler(self):
        return [v for k, v in self.docs.items() if k.startswith("adminAudit/")]


@pytest.fixture()
def depo(monkeypatch):
    """Ücretli abone, deneme kapalı, saat 1000 sn'de donmuş, memo temiz."""
    sahte = SahteFirestore()
    monkeypatch.setattr(device.firestore_client, "get_client", lambda: sahte)
    monkeypatch.setattr(entitlements, "FORCE_PLUS", False)
    monkeypatch.setattr(entitlements, "get_subscription",
                        lambda uid: {"active": True})
    monkeypatch.setattr(entitlements, "in_trial", lambda uid: False)
    monkeypatch.setattr(device, "_now", lambda: _t(1000))
    device.clear_cache()
    yield sahte
    device.clear_cache()
    app.dependency_overrides.clear()


def _giris(uid="u1", auth_time=1500, admin=False):
    app.dependency_overrides[get_current_user] = lambda: AuthUser(
        uid=uid, email="a@b.c", admin=admin, auth_time=auth_time)


def _cihaz_kaydi(depo, uid="u1"):
    return depo.docs.get(f"users/{uid}/private/device")


# ---------------------------------------------------------------------------
# Kapı arkasında DEĞİL
# ---------------------------------------------------------------------------

def test_uclar_require_plus_arkasinda_degil(depo, monkeypatch):
    """Kilit her çağrıda 409 fırlatsa bile üç uç 200 döner."""
    _giris()

    def kilit(*args, **kwargs):
        raise HTTPException(status_code=409, detail="sahte kilit",
                            headers={"X-Device-Conflict": "1"})

    monkeypatch.setattr(device, "enforce_single_device", kilit)
    monkeypatch.setattr(entitlements, "is_subscriber", lambda uid: True)

    with TestClient(app) as client:
        # Kontrol: sahte kilit korumalı yolda gerçekten 409 üretiyor.
        korumali = client.post(KORUMALI_YOL, json=BOS_GOVDE, headers=CIHAZ_A)
        durum = client.get(f"{YOL}/status", headers=CIHAZ_A)
        devral = client.post(f"{YOL}/claim", json={"platform": "ios"},
                             headers=CIHAZ_A)
        birak = client.delete(f"{YOL}/claim", headers=CIHAZ_A)

    assert korumali.status_code == 409
    assert durum.status_code == 200
    assert devral.status_code == 200
    assert birak.status_code == 200


def test_ucretsiz_kullanici_da_uclara_erisir(depo, monkeypatch):
    """Paywall (402) da yok: ücretsiz/deneme kullanıcısı durumunu görebilir
    ve kaydını bırakabilir — abonelik biten kullanıcı kilitte kalmasın."""
    _giris()
    monkeypatch.setattr(entitlements, "is_subscriber", lambda uid: False)
    monkeypatch.setattr(entitlements, "get_subscription",
                        lambda uid: {"active": False})
    with TestClient(app) as client:
        durum = client.get(f"{YOL}/status", headers=CIHAZ_A)
        birak = client.delete(f"{YOL}/claim", headers=CIHAZ_A)
    assert durum.status_code == 200
    assert durum.json()["locked"] is False
    assert birak.status_code == 200


# ---------------------------------------------------------------------------
# POST /claim · DELETE /claim · GET /status
# ---------------------------------------------------------------------------

def test_claim_auth_time_ve_platform_yazar(depo):
    _giris(auth_time=1500)
    with TestClient(app) as client:
        yanit = client.post(f"{YOL}/claim", json={"platform": "ios"},
                            headers=CIHAZ_A)
    assert yanit.status_code == 200
    assert yanit.json() == {"status": "success", "claimed": True}
    k = _cihaz_kaydi(depo)
    assert k["deviceId"] == "cihaz-a"
    assert k["authTime"] == 1500
    assert k["platform"] == "ios"
    assert k["claimedAt"] == _t(1000)
    assert depo.docs["users/u1"]["platform"] == "ios"  # ayna


def test_claim_basliksiz_400(depo):
    _giris()
    with TestClient(app) as client:
        yanit = client.post(f"{YOL}/claim", json={"platform": "ios"})
    assert yanit.status_code == 400
    assert _cihaz_kaydi(depo) is None


def test_claim_yazilamazsa_false(depo, monkeypatch):
    """`claimed` dürüst: Firestore yoksa 200 ama false — istemci kapıyı
    kapatmaz."""
    _giris()
    monkeypatch.setattr(device.firestore_client, "get_client", lambda: None)
    with TestClient(app) as client:
        yanit = client.post(f"{YOL}/claim", json={}, headers=CIHAZ_A)
    assert yanit.status_code == 200
    assert yanit.json()["claimed"] is False


def test_release_yalniz_sahip(depo):
    _giris()
    with TestClient(app) as client:
        client.post(f"{YOL}/claim", json={"platform": "ios"}, headers=CIHAZ_A)
        yabanci = client.delete(f"{YOL}/claim", headers=CIHAZ_B)
        kayit_sonra = dict(_cihaz_kaydi(depo) or {})
        sahip = client.delete(f"{YOL}/claim", headers=CIHAZ_A)
        basliksiz = client.delete(f"{YOL}/claim")
    assert yabanci.json() == {"status": "success", "released": False}
    assert kayit_sonra.get("deviceId") == "cihaz-a"
    assert sahip.json() == {"status": "success", "released": True}
    assert _cihaz_kaydi(depo) is None
    assert basliksiz.status_code == 200
    assert basliksiz.json()["released"] is False


def test_status_sekli(depo):
    _giris()
    with TestClient(app) as client:
        bos = client.get(f"{YOL}/status", headers=CIHAZ_A)
        client.post(f"{YOL}/claim", json={"platform": "ios"}, headers=CIHAZ_A)
        kendi = client.get(f"{YOL}/status", headers=CIHAZ_A)
        obur = client.get(f"{YOL}/status", headers=CIHAZ_B)
    assert bos.json() == {"status": "success", "locked": True,
                          "claimed": False, "this_device": False,
                          "other": None}
    assert kendi.json() == {"status": "success", "locked": True,
                            "claimed": True, "this_device": True,
                            "other": None}
    assert obur.json() == {"status": "success", "locked": True,
                           "claimed": True, "this_device": False,
                           "other": {"platform": "ios",
                                     "claimedAt": "1970-01-01T00:16:40+00:00"}}


# ---------------------------------------------------------------------------
# Korumalı uçta uçtan uca sözleşme (mobil kapı ekranı bunu okur)
# ---------------------------------------------------------------------------

def test_korumali_ucta_409_sozlesmesi(depo, monkeypatch):
    """A'nın kaydı (claimedAt 1000) varken B'nin eski girişi (900) 409."""
    _giris(auth_time=900)
    monkeypatch.setattr(entitlements, "is_subscriber", lambda uid: True)
    depo.docs["users/u1/private/device"] = {
        "deviceId": "cihaz-a", "platform": "android", "claimedAt": _t(1000)}

    with TestClient(app) as client:
        yanit = client.post(KORUMALI_YOL, json=BOS_GOVDE, headers=CIHAZ_B)

    assert yanit.status_code == 409
    assert yanit.headers["x-device-conflict"] == "1"
    assert yanit.headers["x-device-other-platform"] == "android"
    assert yanit.headers["x-device-claimed-at"] == "1970-01-01T00:16:40+00:00"
    assert isinstance(yanit.json()["detail"], str)
    assert "Bu cihazda kullan" in yanit.json()["detail"]
    assert _cihaz_kaydi(depo)["deviceId"] == "cihaz-a"


def test_korumali_ucta_sonraki_giris_devralir(depo, monkeypatch):
    """B'nin girişi (1500) A'nın devralmasından (1000) sonra → 409 YOK,
    kayıt B'ye döner. Boş gövde 422'ye düşer: kilit geçti, rapor üreticisi
    koşmadı."""
    _giris(auth_time=1500)
    monkeypatch.setattr(entitlements, "is_subscriber", lambda uid: True)
    depo.docs["users/u1/private/device"] = {
        "deviceId": "cihaz-a", "platform": "android", "claimedAt": _t(1000)}

    with TestClient(app) as client:
        yanit = client.post(KORUMALI_YOL, json=BOS_GOVDE,
                            headers={**CIHAZ_B, "X-Device-Platform": "iOS"})

    assert yanit.status_code == 422
    k = _cihaz_kaydi(depo)
    assert k["deviceId"] == "cihaz-b"
    # Devralan cihazın platformu yazıldı — A'nın 409 ekranı "iOS" der,
    # kendi platformunu ("android") değil.
    assert k["platform"] == "iOS"

    # A'nın girişi (900) B'nin devralmasından (donmuş saat 1000) ÖNCE → 409.
    _giris(auth_time=900)
    with TestClient(app) as client:
        yanit = client.post(KORUMALI_YOL, json=BOS_GOVDE,
                            headers={**CIHAZ_A, "X-Device-Platform": "android"})
    assert yanit.status_code == 409
    assert yanit.headers["x-device-other-platform"] == "iOS"


def test_korumali_ucta_platformsuz_devralma_bos_birakir(depo, monkeypatch):
    """Eski istemci (başlıksız) devralırsa kaybedenin platformu kayıtta
    KALMAZ; A'nın ekranı "—" görür, kendi platformunu değil."""
    _giris(auth_time=1500)
    monkeypatch.setattr(entitlements, "is_subscriber", lambda uid: True)
    depo.docs["users/u1/private/device"] = {
        "deviceId": "cihaz-a", "platform": "android", "claimedAt": _t(1000)}

    with TestClient(app) as client:
        yanit = client.post(KORUMALI_YOL, json=BOS_GOVDE, headers=CIHAZ_B)

    assert yanit.status_code == 422
    assert _cihaz_kaydi(depo)["platform"] is None


# ---------------------------------------------------------------------------
# Admin kaçış kapısı
# ---------------------------------------------------------------------------

def test_admin_release_claim_sart(depo):
    _giris(uid="u1", admin=False)
    depo.docs["users/u1/private/device"] = {
        "deviceId": "cihaz-a", "platform": "android", "claimedAt": _t(1000)}
    with TestClient(app) as client:
        yanit = client.post(ADMIN_YOL.format(uid="u1"))
    assert yanit.status_code == 403
    assert _cihaz_kaydi(depo)["deviceId"] == "cihaz-a"
    assert depo.izler() == []


def test_admin_release_siler_ve_audit_yazar(depo):
    _giris(uid="admin-1", admin=True)
    depo.docs["users/u1/private/device"] = {
        "deviceId": "cihaz-a", "platform": "android", "claimedAt": _t(1000)}
    with TestClient(app) as client:
        yanit = client.post(ADMIN_YOL.format(uid="u1"))
    assert yanit.status_code == 200
    assert yanit.json() == {"status": "ok", "released": True}
    assert _cihaz_kaydi(depo) is None
    izler = depo.izler()
    assert len(izler) == 1
    assert izler[0]["action"] == "device.release"
    assert izler[0]["targetUid"] == "u1"
    assert izler[0]["adminUid"] == "admin-1"


def test_admin_release_firestore_yokken_500(depo, monkeypatch):
    _giris(uid="admin-1", admin=True)
    monkeypatch.setattr(device.firestore_client, "get_client", lambda: None)
    with TestClient(app) as client:
        yanit = client.post(ADMIN_YOL.format(uid="u1"))
    assert yanit.status_code == 500
