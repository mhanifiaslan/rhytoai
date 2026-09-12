"""AI kullanım telemetrisinin bekçileri (AP-turu).

İki değişmez korunur:

* Telemetri YAN ÜRÜNDÜR: usage_metadata'sız/bozuk yanıt ya da kapalı
  Firestore hiçbir isteği düşürmez.
* gemini_service her GERÇEK model çağrısında `usage_service.record`'u
  feature/uid ile çağırır — maliyet görünürlüğünün tek kaynağı bu.
"""
from __future__ import annotations

import pytest

from services import gemini_service, usage_service


class SahteDoc:
    def __init__(self, depo: list):
        self._depo = depo

    def set(self, data, merge=False):
        self._depo.append(dict(data))


class SahteKoleksiyon:
    def __init__(self, depo: list):
        self._depo = depo

    def document(self, ad=None):
        return SahteDoc(self._depo)


class SahteClient:
    def __init__(self, depo: list):
        self._depo = depo

    def collection(self, ad):
        assert ad == "usageEvents"
        return SahteKoleksiyon(self._depo)


class SahteMeta:
    prompt_token_count = 4000
    candidates_token_count = 800
    thoughts_token_count = 200
    cached_content_token_count = 0


class SahteYanit:
    usage_metadata = SahteMeta()


@pytest.fixture()
def depo(monkeypatch):
    kayitlar: list = []
    monkeypatch.setattr(usage_service.firestore_client, "get_client",
                        lambda: SahteClient(kayitlar))
    return kayitlar


def test_kayit_alanlari_ve_maliyet_formulu(depo):
    usage_service.record("natal", "test-model", SahteYanit(), 1234, uid="u1")

    assert len(depo) == 1
    k = depo[0]
    assert k["uid"] == "u1"
    assert k["feature"] == "natal"
    assert k["model"] == "test-model"
    assert k["promptTokens"] == 4000
    assert k["outputTokens"] == 800
    assert k["thinkingTokens"] == 200
    assert k["latencyMs"] == 1234
    assert k["day"]  # UTC gün anahtarı dolu
    # 4000×$0.30/M girdi + (800+200)×$2.50/M çıktı (düşünme dahil)
    beklenen = (4000 * 0.30 + 1000 * 2.50) / 1_000_000
    assert k["estCostUsd"] == pytest.approx(beklenen, rel=1e-6)


def test_metadatasiz_yanit_sifirlarla_yazilir(depo):
    class Bos:
        pass  # usage_metadata yok

    usage_service.record("chat", "m", Bos(), 10)  # istisna YOK

    assert depo[0]["promptTokens"] == 0
    assert depo[0]["estCostUsd"] == 0
    assert depo[0]["feature"] == "chat"
    assert depo[0]["uid"] is None


def test_firestore_kapaliyken_sessiz(monkeypatch):
    monkeypatch.setattr(usage_service.firestore_client, "get_client",
                        lambda: None)
    usage_service.record("chat", "m", SahteYanit(), 10)  # fırlatmamalı


def test_yazim_hatasi_yutulur(monkeypatch):
    class Patlayan:
        def collection(self, ad):
            raise RuntimeError("bum")

    monkeypatch.setattr(usage_service.firestore_client, "get_client",
                        lambda: Patlayan())
    usage_service.record("chat", "m", SahteYanit(), 10)  # fırlatmamalı


# ---------------------------------------------------------------------------
# gemini_service kancaları
# ---------------------------------------------------------------------------

class _SahteAday:
    finish_reason = "STOP"


class _SahteModelYanit:
    text = "Yıldızlar bugün sakin."
    candidates = [_SahteAday()]
    usage_metadata = SahteMeta()


class _SahteModels:
    def generate_content(self, model, contents, config):
        return _SahteModelYanit()


class _SahteGenai:
    models = _SahteModels()


def test_generate_kaydi_feature_ve_uid_ile(monkeypatch):
    cagrilar: list = []
    monkeypatch.setattr(gemini_service, "_get_client", lambda: _SahteGenai())
    monkeypatch.setattr(gemini_service.usage_service, "record",
                        lambda *a, **kw: cagrilar.append((a, kw)))

    sonuc = gemini_service.generate("selam", feature="natal", uid="u9")

    assert sonuc == "Yıldızlar bugün sakin."
    assert len(cagrilar) == 1
    args, kwargs = cagrilar[0]
    assert args[0] == "natal"
    assert kwargs["uid"] == "u9"
    assert isinstance(args[3], int)  # latency_ms


def test_chat_kaydi_varsayilan_feature(monkeypatch):
    cagrilar: list = []
    monkeypatch.setattr(gemini_service, "_get_client", lambda: _SahteGenai())
    monkeypatch.setattr(gemini_service.usage_service, "record",
                        lambda *a, **kw: cagrilar.append((a, kw)))

    sonuc = gemini_service.chat([], "merhaba", uid="u9")

    assert sonuc == "Yıldızlar bugün sakin."
    assert cagrilar[0][0][0] == "chat"
    assert cagrilar[0][1]["uid"] == "u9"


def test_istisnali_cagri_kayit_uretmez(monkeypatch):
    """Model istisna attıysa yanıt yok → faturalanmadı sayılır, kayıt yok."""
    class PatlayanModels:
        def generate_content(self, model, contents, config):
            raise RuntimeError("500")

    class PatlayanGenai:
        models = PatlayanModels()

    cagrilar: list = []
    monkeypatch.setattr(gemini_service, "_get_client", lambda: PatlayanGenai())
    monkeypatch.setattr(gemini_service.usage_service, "record",
                        lambda *a, **kw: cagrilar.append(a))

    assert gemini_service.generate("selam", feature="natal") is None
    assert cagrilar == []


# ---------------------------------------------------------------------------
# Kullanıcı toplamları (AD6): private/usageTotals Increment ile birikir
# ---------------------------------------------------------------------------

def test_totals_increment_ile_birikir(monkeypatch):
    from _sahte_firestore import SahteFirestore
    depo = SahteFirestore()
    monkeypatch.setattr(usage_service.firestore_client, "get_client",
                        lambda: depo)

    usage_service.record("natal", "m", SahteYanit(), 10, uid="u1")
    usage_service.record("chat", "m", SahteYanit(), 10, uid="u1")

    t = depo.docs["users/u1/private/usageTotals"]
    beklenen = (4000 * 0.30 + 1000 * 2.50) / 1_000_000
    assert t["calls"] == 2
    assert t["estCostUsd"] == pytest.approx(2 * beklenen, rel=1e-6)
    assert t["promptTokens"] == 8000 and t["outputTokens"] == 1600
    assert t["thinkingTokens"] == 400
    assert t["byFeature"]["natal"]["calls"] == 1
    assert t["byFeature"]["chat"]["estCostUsd"] == pytest.approx(beklenen, rel=1e-6)
    assert t["lastAt"]
    # Olay kaydı da yazıldı (2 usageEvents).
    assert len([k for k in depo.docs if k.startswith("usageEvents/")]) == 2


def test_totals_uid_yoksa_yazilmaz(monkeypatch):
    from _sahte_firestore import SahteFirestore
    depo = SahteFirestore()
    monkeypatch.setattr(usage_service.firestore_client, "get_client",
                        lambda: depo)
    usage_service.record("horoscope", "m", SahteYanit(), 10)
    assert not any("usageTotals" in k for k in depo.docs)


def test_totals_hatasi_olayi_dusurmez(monkeypatch):
    """Toplam yazımı patlasa da olay kaydı durur, istisna yok."""
    from _sahte_firestore import SahteFirestore
    depo = SahteFirestore()
    monkeypatch.setattr(usage_service.firestore_client, "get_client",
                        lambda: depo)
    monkeypatch.setattr(usage_service, "_bump_totals",
                        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("bum")))
    usage_service.record("chat", "m", SahteYanit(), 10, uid="u1")
    assert len([k for k in depo.docs if k.startswith("usageEvents/")]) == 1
