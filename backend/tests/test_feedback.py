"""Uygulama içi geri bildirim kanalı (GB-turu) — sunucu yarısı.

Değişmezler:
- `POST /api/v1/account/feedback`: doküman bağlamı BAŞLIKLARDAN alır
  (X-App-Build → appBuild, X-Device-Platform → platform, Accept-Language →
  language); kötü tür / boş metin 422; uid başına günde 10 (11. → 429 +
  `feedback.limit` kullanıcının dilinde); kimliksiz üretimde 401.
- Admin: liste süzgeç + imleç (createdAt DESC, [createdAt, id]); detay
  404; PATCH durum + not + iz `feedback.update`; yanıt dokümana yazılır,
  push kullanıcının GÜNCEL jetonuna ve kendi dilinde başlıkla gider, durum
  new → in_review, iz `feedback.reply`; jetonsuz kullanıcıda `pushSent`
  False ama yanıt yine kaydedilir; dikkat zilinde `newFeedback`.
"""
from __future__ import annotations

import datetime as dt

import pytest
from fastapi.testclient import TestClient

from core import config
from core import firestore as firestore_client
from core.auth import AuthUser, get_current_user
from main import app
from services import admin_service, feedback_service, push_service
from _sahte_firestore import SahteFirestore

_SIMDI = dt.datetime.now(dt.timezone.utc)


@pytest.fixture()
def depo(monkeypatch):
    sahte = SahteFirestore({
        "users/u1": {"displayName": "Ayşe", "email": "ayse@ornek.com",
                     "language": "en", "fcmToken": "tok-u1"},
        "users/u2": {"displayName": "Can", "email": "can@ornek.com",
                     "language": "tr"},
    })
    monkeypatch.setattr(firestore_client, "get_client", lambda: sahte)
    return sahte


@pytest.fixture()
def kullanici():
    """Doğrulanmış (anonim olmayan) oturum — u1."""
    app.dependency_overrides[get_current_user] = lambda: AuthUser(
        uid="u1", email="ayse@ornek.com")
    yield
    app.dependency_overrides.clear()


@pytest.fixture()
def admin(monkeypatch):
    """DEV admin, destek rolü — geri bildirim uçları destek için açık."""
    monkeypatch.setattr(config, "DEV_MODE", True)
    monkeypatch.setattr(config, "DEV_ADMIN", True)
    monkeypatch.setattr(config, "DEV_ADMIN_ROLE", "support")


def _kayit(i: int, uid: str = "u1", tur: str = "bug", durum: str = "new",
           dakika: int | None = None) -> dict:
    return {"uid": uid, "type": tur, "text": f"metin {i}", "screen": None,
            "appBuild": 39, "platform": "android", "language": "tr",
            "createdAt": _SIMDI - dt.timedelta(minutes=dakika if dakika
                                                is not None else i),
            "status": durum, "notes": [], "reply": None,
            "updatedAt": _SIMDI}


def _izler(depo) -> list[dict]:
    return [v for k, v in depo.docs.items() if k.startswith("adminAudit/")]


# ---------------------------------------------------------------------------
# Kullanıcı ucu
# ---------------------------------------------------------------------------

def test_kullanici_ucu_baglami_basliklardan_yazar(depo, kullanici):
    with TestClient(app) as client:
        yanit = client.post(
            "/api/v1/account/feedback",
            json={"type": "bug", "text": "  Harita açılmıyor  ",
                  "screen": "natal_chart"},
            headers={"X-App-Build": "39", "X-Device-Platform": "android",
                     "Accept-Language": "en"})
    assert yanit.status_code == 200, yanit.text
    govde = yanit.json()
    assert govde["status"] == "ok" and govde["id"]
    kayit = depo.docs[f"feedback/{govde['id']}"]
    assert kayit["uid"] == "u1"
    assert kayit["type"] == "bug"
    assert kayit["text"] == "Harita açılmıyor"      # kırpılmış
    assert kayit["screen"] == "natal_chart"
    assert kayit["appBuild"] == 39
    assert kayit["platform"] == "android"
    assert kayit["language"] == "en"
    assert kayit["status"] == "new"
    assert kayit["notes"] == [] and kayit["reply"] is None
    assert isinstance(kayit["createdAt"], dt.datetime)
    assert kayit["createdAt"].tzinfo is not None
    assert kayit["updatedAt"] == kayit["createdAt"]


def test_kullanici_ucu_basliksiz_bos_baglam(depo, kullanici):
    with TestClient(app) as client:
        yanit = client.post("/api/v1/account/feedback",
                            json={"type": "other", "text": "selam"})
    assert yanit.status_code == 200
    kayit = depo.docs[f"feedback/{yanit.json()['id']}"]
    assert kayit["appBuild"] is None
    assert kayit["platform"] is None
    assert kayit["screen"] is None
    assert kayit["language"] == "tr"


@pytest.mark.parametrize("govde", [
    {"type": "rant", "text": "x"},          # bilinmeyen tür
    {"type": "bug", "text": ""},             # boş metin
    {"type": "bug", "text": "   \n "},       # boşluktan ibaret
    {"type": "bug", "text": "x" * 2001},     # fazla uzun
    {"type": "bug", "text": "x", "screen": "s" * 61},
    {"text": "tür yok"},
])
def test_kullanici_ucu_kotu_govde_422(depo, kullanici, govde):
    with TestClient(app) as client:
        yanit = client.post("/api/v1/account/feedback", json=govde)
    assert yanit.status_code == 422
    assert not any(k.startswith("feedback/") for k in depo.docs)


def test_gunluk_sinir_onbirinci_429(depo, kullanici):
    """10 kayıt geçer, 11. 429 + kullanıcının dilinde metin; başka
    kullanıcının ve dünün kayıtları sayılmaz."""
    depo.docs["feedback/dun"] = _kayit(0, dakika=36 * 60)   # dün
    depo.docs["feedback/baskasi"] = _kayit(0, uid="u2")
    with TestClient(app) as client:
        for i in range(feedback_service.DAILY_LIMIT):
            yanit = client.post("/api/v1/account/feedback",
                                json={"type": "suggestion", "text": f"n{i}"})
            assert yanit.status_code == 200, (i, yanit.text)
        yanit = client.post("/api/v1/account/feedback",
                            json={"type": "suggestion", "text": "fazla"},
                            headers={"Accept-Language": "en"})
    assert yanit.status_code == 429
    assert yanit.json()["detail"] == (
        "You've reached today's feedback limit — try again tomorrow.")
    bugunku = [v for k, v in depo.docs.items()
               if k.startswith("feedback/") and v["uid"] == "u1"
               and v["createdAt"] >= _SIMDI - dt.timedelta(hours=1)]
    assert len(bugunku) == feedback_service.DAILY_LIMIT


def test_kimliksiz_uretimde_401(depo, monkeypatch):
    monkeypatch.setattr(config, "DEV_MODE", False)
    with TestClient(app) as client:
        yanit = client.post("/api/v1/account/feedback",
                            json={"type": "bug", "text": "x"})
    assert yanit.status_code == 401
    assert not any(k.startswith("feedback/") for k in depo.docs)


# ---------------------------------------------------------------------------
# Admin: liste + detay
# ---------------------------------------------------------------------------

@pytest.fixture()
def dolu_depo(depo):
    for i in range(5):
        depo.docs[f"feedback/f{i}"] = _kayit(i)
    depo.docs["feedback/fx"] = _kayit(2, uid="u2", tur="suggestion",
                                      durum="closed")
    depo.docs["feedback/f2b"] = _kayit(2)          # aynı createdAt (f2)
    depo.docs["feedback/f2b"]["notes"] = [{"text": "n"}]
    return depo


def test_liste_sirali_kullanici_adli_ve_imlecli(dolu_depo, admin):
    with TestClient(app) as client:
        yanit = client.get("/api/v1/admin/feedback?limit=3")
        assert yanit.status_code == 200, yanit.text
        govde = yanit.json()
        assert govde["status"] == "ok"
        ilk = [k["id"] for k in govde["items"]]
        assert ilk == ["f0", "f1", "fx"]            # createdAt DESC, id DESC
        assert govde["nextCursor"]
        satir = govde["items"][0]
        assert set(satir) == {"id", "uid", "type", "text", "screen",
                              "appBuild", "platform", "language",
                              "createdAt", "status", "reply", "updatedAt",
                              "noteCount", "user"}
        assert satir["user"] == {"displayName": "Ayşe",
                                 "email": "ayse@ornek.com"}
        assert govde["items"][2]["user"]["displayName"] == "Can"
        assert "notes" not in satir

        yanit = client.get(f"/api/v1/admin/feedback?limit=3"
                           f"&cursor={govde['nextCursor']}")
        ikinci = [k["id"] for k in yanit.json()["items"]]
        assert ikinci == ["f2b", "f2", "f3"]        # çakışma yok
        assert yanit.json()["items"][0]["noteCount"] == 1
        yanit = client.get(f"/api/v1/admin/feedback?limit=3"
                           f"&cursor={yanit.json()['nextCursor']}")
        assert [k["id"] for k in yanit.json()["items"]] == ["f4"]
        assert yanit.json()["nextCursor"] is None
    assert set(ilk) & set(ikinci) == set()


def test_liste_suzgecleri(dolu_depo, admin):
    with TestClient(app) as client:
        yanit = client.get("/api/v1/admin/feedback?status=closed")
        assert [k["id"] for k in yanit.json()["items"]] == ["fx"]
        yanit = client.get("/api/v1/admin/feedback?type=bug&status=new")
        assert len(yanit.json()["items"]) == 6
        assert client.get("/api/v1/admin/feedback?status=x").status_code == 422
        assert client.get("/api/v1/admin/feedback?cursor=!!!").status_code == 400


def test_detay_tam_dokuman_ve_404(dolu_depo, admin):
    with TestClient(app) as client:
        yanit = client.get("/api/v1/admin/feedback/f2b")
        assert yanit.status_code == 200
        kayit = yanit.json()["item"]
        assert kayit["id"] == "f2b"
        assert kayit["notes"] == [{"text": "n"}]
        assert kayit["noteCount"] == 1
        assert kayit["user"]["email"] == "ayse@ornek.com"
        assert client.get("/api/v1/admin/feedback/yok").status_code == 404


def test_admin_olmayan_403(dolu_depo, monkeypatch):
    monkeypatch.setattr(config, "DEV_MODE", True)
    monkeypatch.setattr(config, "DEV_ADMIN", False)
    with TestClient(app) as client:
        assert client.get("/api/v1/admin/feedback").status_code == 403


# ---------------------------------------------------------------------------
# Admin: PATCH
# ---------------------------------------------------------------------------

def test_patch_durum_ve_not_ve_iz(dolu_depo, admin):
    with TestClient(app) as client:
        yanit = client.patch("/api/v1/admin/feedback/f1",
                             json={"status": "in_review",
                                   "note": "  bakılıyor  "})
    assert yanit.status_code == 200, yanit.text
    kayit = dolu_depo.docs["feedback/f1"]
    assert kayit["status"] == "in_review"
    assert len(kayit["notes"]) == 1
    n = kayit["notes"][0]
    assert n["text"] == "bakılıyor"
    assert n["adminUid"] == "dev-user"
    assert isinstance(n["at"], dt.datetime)
    assert kayit["text"] == "metin 1"              # merge — gerisi durdu
    assert kayit["updatedAt"] > _SIMDI
    govde = yanit.json()["item"]
    assert govde["status"] == "in_review" and govde["noteCount"] == 1

    izler = _izler(dolu_depo)
    assert len(izler) == 1
    assert izler[0]["action"] == "feedback.update"
    assert izler[0]["targetUid"] == "u1"
    assert izler[0]["params"] == {"fid": "f1", "status": "in_review",
                                  "hasNote": True}


def test_patch_yalniz_not_durumu_bozmaz(dolu_depo, admin):
    with TestClient(app) as client:
        client.patch("/api/v1/admin/feedback/f1", json={"note": "a"})
        client.patch("/api/v1/admin/feedback/f1", json={"note": "b"})
    kayit = dolu_depo.docs["feedback/f1"]
    assert kayit["status"] == "new"
    assert [n["text"] for n in kayit["notes"]] == ["a", "b"]
    assert _izler(dolu_depo)[-1]["params"]["status"] is None


@pytest.mark.parametrize("govde, kod", [
    ({}, 400), ({"note": "  "}, 400),
    ({"status": "done"}, 422), ({"note": "x" * 1001}, 422),
])
def test_patch_kotu_govde(dolu_depo, admin, govde, kod):
    with TestClient(app) as client:
        assert client.patch("/api/v1/admin/feedback/f1",
                            json=govde).status_code == kod
    assert _izler(dolu_depo) == []


def test_patch_yok_404_iz_yok(dolu_depo, admin):
    with TestClient(app) as client:
        yanit = client.patch("/api/v1/admin/feedback/yok",
                             json={"status": "closed"})
    assert yanit.status_code == 404
    assert _izler(dolu_depo) == []


# ---------------------------------------------------------------------------
# Admin: yanıt + push
# ---------------------------------------------------------------------------

@pytest.fixture()
def sahte_push(monkeypatch):
    gonderilen: list[list[push_service.Message]] = []

    def send(mesajlar):
        gonderilen.append(list(mesajlar))
        return push_service.SendResult(len(mesajlar), 0, [], [])
    monkeypatch.setattr(push_service, "send", send)
    return gonderilen


def test_yanit_kaydeder_push_gonderir_durum_ilerler(dolu_depo, admin,
                                                    sahte_push):
    with TestClient(app) as client:
        yanit = client.post("/api/v1/admin/feedback/f1/reply",
                            json={"text": "  Düzelttik, teşekkürler.  "})
    assert yanit.status_code == 200, yanit.text
    govde = yanit.json()
    assert govde["pushSent"] is True
    assert govde["reply"]["text"] == "Düzelttik, teşekkürler."
    assert govde["reply"]["adminUid"] == "dev-user"
    assert govde["reply"]["pushSent"] is True
    assert govde["item"]["status"] == "in_review"

    kayit = dolu_depo.docs["feedback/f1"]
    assert kayit["status"] == "in_review"            # new → in_review
    assert kayit["reply"]["text"] == "Düzelttik, teşekkürler."
    assert isinstance(kayit["reply"]["at"], dt.datetime)
    assert kayit["reply"]["pushSent"] is True

    # Push: u1'in güncel jetonuna, u1'in dilinde (en) başlıkla.
    assert len(sahte_push) == 1 and len(sahte_push[0]) == 1
    m = sahte_push[0][0]
    assert m.uid == "u1" and m.token == "tok-u1"
    assert m.title == "💬 A reply from the Rytho team"
    assert m.body == "Düzelttik, teşekkürler."
    assert m.data == {"type": "feedback", "fid": "f1"}

    izler = _izler(dolu_depo)
    assert len(izler) == 1
    assert izler[0]["action"] == "feedback.reply"
    assert izler[0]["targetUid"] == "u1"
    assert izler[0]["params"] == {"fid": "f1", "pushSent": True}


def test_yanit_turkce_kullaniciya_turkce_baslik(dolu_depo, admin, sahte_push):
    dolu_depo.docs["users/u2"]["fcmToken"] = "tok-u2"
    with TestClient(app) as client:
        yanit = client.post("/api/v1/admin/feedback/fx/reply",
                            json={"text": "Not aldık."})
    assert yanit.status_code == 200
    assert sahte_push[0][0].title == "💬 Rytho ekibinden yanıt"
    assert sahte_push[0][0].token == "tok-u2"
    # closed kalır — yalnız new ilerler.
    assert dolu_depo.docs["feedback/fx"]["status"] == "closed"


def test_yanit_jetonsuz_kullanici_pushsent_false(dolu_depo, admin, sahte_push):
    """u2'nin jetonu yok: yanıt yine yazılır, push denenmez."""
    with TestClient(app) as client:
        yanit = client.post("/api/v1/admin/feedback/fx/reply",
                            json={"text": "Uygulamada görürsün."})
    assert yanit.status_code == 200
    assert yanit.json()["pushSent"] is False
    kayit = dolu_depo.docs["feedback/fx"]
    assert kayit["reply"]["text"] == "Uygulamada görürsün."
    assert kayit["reply"]["pushSent"] is False
    assert sahte_push == []
    assert _izler(dolu_depo)[0]["params"] == {"fid": "fx", "pushSent": False}


def test_yanit_uzun_metin_govde_kirpilir(dolu_depo, admin, sahte_push):
    from services import notification_service as ns
    uzun = "a" * 300
    with TestClient(app) as client:
        client.post("/api/v1/admin/feedback/f1/reply", json={"text": uzun})
    govde = sahte_push[0][0].body
    assert len(govde) <= ns.MAX_PUSH_BODY and govde.endswith("…")
    assert dolu_depo.docs["feedback/f1"]["reply"]["text"] == uzun  # tam


def test_yanit_push_duserse_kayit_durur(dolu_depo, admin, monkeypatch):
    def patlar(mesajlar):
        raise RuntimeError("FCM yok")
    monkeypatch.setattr(push_service, "send", patlar)
    with TestClient(app) as client:
        yanit = client.post("/api/v1/admin/feedback/f1/reply",
                            json={"text": "x"})
    assert yanit.status_code == 200
    assert yanit.json()["pushSent"] is False
    assert dolu_depo.docs["feedback/f1"]["reply"]["text"] == "x"


@pytest.mark.parametrize("govde", [{"text": ""}, {"text": "x" * 501}, {}])
def test_yanit_kotu_govde_422(dolu_depo, admin, sahte_push, govde):
    with TestClient(app) as client:
        assert client.post("/api/v1/admin/feedback/f1/reply",
                           json=govde).status_code == 422
    assert sahte_push == [] and _izler(dolu_depo) == []


def test_yanit_yok_404(dolu_depo, admin, sahte_push):
    with TestClient(app) as client:
        assert client.post("/api/v1/admin/feedback/yok/reply",
                           json={"text": "x"}).status_code == 404
    assert sahte_push == []


# ---------------------------------------------------------------------------
# Dikkat zili
# ---------------------------------------------------------------------------

def test_attention_yeni_geri_bildirim(dolu_depo, monkeypatch):
    monkeypatch.setattr(admin_service.stats_service, "read_days",
                        lambda n: [{"generatedAt": _SIMDI}])
    kalemler = {k["tur"]: k for k in admin_service.attention()}
    assert kalemler["newFeedback"] == {
        "tur": "newFeedback", "sayi": 6,
        "rota": "#/geribildirim?status=new", "seviye": "bilgi"}


def test_attention_geri_bildirim_yokken_kalem_yok(depo, monkeypatch):
    monkeypatch.setattr(admin_service.stats_service, "read_days",
                        lambda n: [{"generatedAt": _SIMDI}])
    assert "newFeedback" not in {k["tur"] for k in admin_service.attention()}
