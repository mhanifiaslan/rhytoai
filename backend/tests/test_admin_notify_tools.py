"""Bildirim araçları (AD8): notify_runner.run_batch / test_send.

Değişmezler:
- Prova (dry_run) push_service.send'i ÇAĞIRMAZ, hiçbir kayıt yazmaz.
- test_send yalnız verilen uid'e bakar (tarama yok), mark=False: mark_sent,
  notifyRuns ve sohbet tohumu YAZILMAZ.
- Jetonsuz/profilsiz hesap → ValueError (uç 400'e çevirir).
- Koşu bir şey kuyruklamadıysa sabit PUSH_TEST_* profil dilinde gider,
  data {"type": "test"}.
- api/notify.run ince sarmalayıcı: sır kapısı + bayrak doğrulaması aynen.
"""
from __future__ import annotations

import pytest

from core import config
from services import notification_service as ns
from services import notify_runner, prompts, push_service

SAHTE_GOKYUZU = {"moon_phase": {"key": "full_moon", "name": "Dolunay",
                                "illumination": 98}, "retrogrades": []}


def _profil(**alanlar):
    temel = {"fcmToken": "token-1", "onboardingCompleted": True,
             "timezone": "Europe/Istanbul", "language": "tr",
             "sunSign": "Aslan ♌", "streakCount": 5, "quietFrom": 0,
             "quietTo": 0}
    temel.update(alanlar)
    return temel


@pytest.fixture()
def ortam(monkeypatch):
    """Tek profil, gökyüzü sabit, sinyal push'u sabit, kayıtlar izlenir."""
    kayit = {"gonderilen": [], "isaretlenen": [], "kosu": [], "tohum": []}
    profiller = {"u1": _profil()}
    monkeypatch.setattr(notify_runner, "get_sky_now", lambda: SAHTE_GOKYUZU)
    monkeypatch.setattr(notify_runner.profile_service, "get_profile",
                        lambda uid: profiller.get(uid))
    monkeypatch.setattr(notify_runner, "_iter_profiles",
                        lambda: iter([{**p, "uid": u} for u, p in profiller.items()]))
    monkeypatch.setattr(ns, "already_sent", lambda uid, tur, gun: False)
    monkeypatch.setattr(ns, "last_daily_sent", lambda uid: None)
    monkeypatch.setattr(
        ns, "signal_push",
        lambda p, lang, today=None, onceki=None: (
            "Başlık", "Gövde.", "iz", 0, {}))
    monkeypatch.setattr(ns, "mark_sent",
                        lambda uid, tur, gun, extra=None: kayit["isaretlenen"].append(uid))
    monkeypatch.setattr(notify_runner, "_kosu_kaydet",
                        lambda *a, **k: kayit["kosu"].append(a))
    monkeypatch.setattr(notify_runner.chat_history, "seed_assistant_message",
                        lambda *a, **k: kayit["tohum"].append(a) or "cid-1")

    def sahte_send(mesajlar):
        kayit["gonderilen"].extend(mesajlar)
        return push_service.SendResult(sent=len(mesajlar), failed=0,
                                       pruned=[], failed_uids=[])
    monkeypatch.setattr(push_service, "send", sahte_send)
    kayit["profiller"] = profiller
    return kayit


def test_prova_gondermez_kaydetmez(ortam, monkeypatch):
    def gondermemeli(m):
        raise AssertionError("prova gönderim yapmamalı")
    monkeypatch.setattr(push_service, "send", gondermemeli)
    sonuc = notify_runner.run_batch("daily", dry_run=True, force=True)
    assert sonuc.status == "dry-run" and sonuc.queued == 1
    assert sonuc.languages == {"tr": 1}
    assert ortam["isaretlenen"] == [] and ortam["kosu"] == []


def test_kosu_isaretler_ve_kaydeder(ortam):
    sonuc = notify_runner.run_batch("daily", force=True)
    assert sonuc.status == "ok" and sonuc.sent == 1
    assert ortam["isaretlenen"] == ["u1"]
    assert len(ortam["kosu"]) == 1


def test_bilinmeyen_tur_ve_bayrak(ortam):
    with pytest.raises(ValueError):
        notify_runner.run_batch("spam")
    with pytest.raises(ValueError):
        notify_runner.run_batch("daily", ignore_dedupe=True)


def test_test_send_kuyruktan_gider_iz_birakmaz(ortam):
    ortam["profiller"]["u2"] = _profil(fcmToken="token-2", language="en")
    sonuc = notify_runner.test_send("u1", "daily")
    assert sonuc == {"sent": 1, "failed": 0, "lang": "tr", "title": "Başlık",
                     "body": "Gövde.", "skippedReason": None, "type": "daily"}
    # Yalnız u1'e gitti; u2 taranmadı bile.
    assert [m.uid for m in ortam["gonderilen"]] == ["u1"]
    assert ortam["isaretlenen"] == [] and ortam["kosu"] == []


def test_test_send_atlanirsa_sabit_metin(ortam, monkeypatch):
    ortam["profiller"]["u1"] = _profil(language="en", notifyDaily=False)
    sonuc = notify_runner.test_send("u1", "daily")
    en = prompts.get("en")
    assert sonuc["title"] == en.PUSH_TEST_TITLE
    assert sonuc["body"] == en.PUSH_TEST_BODY
    assert sonuc["lang"] == "en" and sonuc["sent"] == 1
    assert sonuc["skippedReason"]            # "tercih" gibi görünür gerekçe
    m = ortam["gonderilen"][0]
    assert m.uid == "u1" and m.token == "token-1"
    assert m.data == {"type": "test"}
    assert ortam["isaretlenen"] == [] and ortam["kosu"] == []


def test_test_send_soru_tohumlamaz(ortam, monkeypatch):
    class _Checkin:
        baslik, govde, soru = "Rytho merak ediyor", "Bugün nasıldı?", True
    monkeypatch.setattr(ns, "checkin_push",
                        lambda p, lang, today=None: _Checkin())
    sonuc = notify_runner.test_send("u1", "checkin")
    assert sonuc["body"] == "Bugün nasıldı?"
    assert ortam["tohum"] == []                   # mark=False → tohum yok
    assert ortam["gonderilen"][0].data["route"] == "chat"


def test_test_send_jeton_yoksa_400_mesaji(ortam):
    ortam["profiller"]["u1"] = _profil(fcmToken=None)
    with pytest.raises(ValueError, match="push jetonu yok"):
        notify_runner.test_send("u1", "daily")
    with pytest.raises(ValueError, match="push jetonu yok"):
        notify_runner.test_send("yok", "daily")
    with pytest.raises(ValueError):
        notify_runner.test_send("u1", "spam")
    assert ortam["gonderilen"] == []


def test_push_test_sablonlari_iki_dilde():
    tr, en = prompts.get("tr"), prompts.get("en")
    assert tr.PUSH_TEST_TITLE != en.PUSH_TEST_TITLE
    assert tr.PUSH_TEST_BODY != en.PUSH_TEST_BODY


def test_api_notify_ince_sarmalayici(ortam, monkeypatch):
    """Uç yalnız sır kapısı + bayrak doğrulaması; gövde runner'da."""
    pytest.importorskip("main")
    from fastapi.testclient import TestClient
    from api import notify
    from main import app

    monkeypatch.setattr(config, "NOTIFY_SCHEDULER_SECRET", "dogru")
    cagrilar: list = []

    def sahte_batch(type, **k):
        cagrilar.append((type, k))
        return notify_runner.RunResult(status="ok", type=type, scanned=0,
                                       queued=0, sent=0, failed=0, pruned=0,
                                       skipped={})
    monkeypatch.setattr(notify.notify_runner, "run_batch", sahte_batch)
    with TestClient(app) as client:
        yetkisiz = client.post("/api/v1/notify/run?type=daily")
        bozuk = client.post("/api/v1/notify/run?type=daily&ignore_dedupe=true",
                            headers={"Authorization": "dogru"})
        tamam = client.post(
            "/api/v1/notify/run?type=streak&force=true&dry_run=true",
            headers={"Authorization": "dogru"})
    assert yetkisiz.status_code == 401 and bozuk.status_code == 400
    assert tamam.status_code == 200 and tamam.json()["type"] == "streak"
    assert cagrilar == [("streak", {"dry_run": True, "force": True,
                                    "ignore_dedupe": False})]
    # Geriye uyum: eski adlar api.notify üzerinden de okunur.
    assert notify._jeton_sahipleri is notify_runner._jeton_sahipleri
