"""Rytho'nun İLK SÖZÜ — soru biçimli bildirimin sohbete yazılması (SS-turu).

Cihaz bulgusu: akşam check-in bildirimi bir SORU ama dokununca soru
kullanıcının GİRİŞ KUTUSUNA yazılıyordu — kullanıcı kendi sorusunu
soruyormuş gibi. Artık soru gerçekten Rytho'nun mesajı olarak konuşmada
duruyor ve kullanıcı cevaplıyor.

Buradaki en önemli test `test_tohum_KULLANICI_VERISI_SILMEZ`: ilk tasarım
tohumlarken `_evict_oldest_if_needed` çağırıyordu ve 20 konusu dolu bir
kullanıcının en eski GERÇEK konuşmasını her akşam, kullanıcı hiçbir şey
yapmadan kalıcı olarak siliyordu.
"""
from __future__ import annotations

import datetime as dt

import pytest

from services import chat_history


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

    @property
    def id(self):
        return self._yol.rsplit("/", 1)[-1]

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
        self._sayac = 0

    def document(self, ad=None):
        if ad is None:
            self._sayac += 1
            ad = f"oto{len(self._depo)}-{self._sayac}"
        return _SahteDoc(self._depo, f"{self._yol}/{ad}")

    # Tahliye yolu bunları kullanır; testte ÇAĞRILMAMALARI beklenir.
    def order_by(self, *a, **k):
        raise AssertionError(
            "Tohumlama tahliye sorgusu koşturdu — kullanici verisi risk altinda")

    def stream(self):
        raise AssertionError("Tohumlama koleksiyonu taradi")


class _SahteClient:
    def __init__(self, depo):
        self._depo = depo

    def collection(self, ad):
        return _SahteKoleksiyon(self._depo, ad)


@pytest.fixture()
def depo(monkeypatch):
    veriler: dict = {}
    monkeypatch.setattr(chat_history.firestore_client, "get_client",
                        lambda: _SahteClient(veriler))
    return veriler


KONU = "users/u1/conversations/ask-2026-09-08"
SORU = "Bugün iş tarafında bir hareket görünüyordu — nasıl geçti?"


def _mesajlar(depo, kimlik="ask-2026-09-08"):
    onek = f"users/u1/conversations/{kimlik}/messages/"
    return [v for k, v in depo.items() if k.startswith(onek)]


# ---------------------------------------------------------------------------
# Tohumlama
# ---------------------------------------------------------------------------

def test_tohum_konu_ve_tek_ai_mesaji_yazar(depo):
    kimlik = chat_history.seed_assistant_message("u1", SORU, "tr",
                                                 "2026-09-08")
    assert kimlik == "ask-2026-09-08"
    konu = depo[KONU]
    assert konu["messageCount"] == 1
    assert konu["openedBy"] == "rytho"
    assert konu["seedQuestion"] == SORU
    assert konu["lang"] == "tr"
    assert konu["title"]                      # başlık sorudan
    mesajlar = _mesajlar(depo)
    assert len(mesajlar) == 1
    # 'AI' BİLEREK: istemci ayrımı `sender != 'AI'` ile yapıyor; başka bir
    # değer kullanıcı balonu olarak çizilirdi.
    assert mesajlar[0]["sender"] == "AI"
    assert mesajlar[0]["text"] == SORU


def test_tohum_kisa_omurlu(depo):
    """Cevaplanmayan soru kendi kendini toplamalı: 30 gün DEĞİL.

    Uzun ömürlü olsaydı cevaplanmamış tohumlar arşiv listesini ve panel
    sayaçlarını ay boyunca şişirirdi.
    """
    chat_history.seed_assistant_message("u1", SORU, "tr", "2026-09-08")
    konu = depo[KONU]
    omur = konu["expireAt"] - konu["createdAt"]
    assert omur == dt.timedelta(days=chat_history.SEED_RETENTION_DAYS)
    assert omur < dt.timedelta(days=chat_history.RETENTION_DAYS)


def test_ayni_gun_ikinci_cagri_cogaltmaz(depo):
    """Zamanlayıcı saatlik koşuyor ve gönderim düşerse yeniden deniyor."""
    a = chat_history.seed_assistant_message("u1", SORU, "tr", "2026-09-08")
    b = chat_history.seed_assistant_message("u1", SORU, "tr", "2026-09-08")
    assert a == b
    assert len(_mesajlar(depo)) == 1
    assert depo[KONU]["messageCount"] == 1


def test_tohum_KULLANICI_VERISI_SILMEZ(depo):
    """SS-turu'nun en kritik bekçisi.

    İlk tasarım tohumlarken `_evict_oldest_if_needed` çağırıyordu. 20
    konusu dolu bir kullanıcıda bu, her akşam en eski GERÇEK konuşmayı
    kalıcı siler (tombstone yok, geri alma yok) — kullanıcı hiçbir şey
    yapmadan. Bugün tahliye YALNIZ `write_turn` içinden koşuyor, yani her
    silme kullanıcının kendi eyleminin sonucu. Sahte koleksiyon
    `order_by`/`stream` çağrılırsa PATLAR.
    """
    for i in range(25):
        depo[f"users/u1/conversations/eski{i}"] = {
            "title": f"gercek konu {i}", "messageCount": 8,
        }
    chat_history.seed_assistant_message("u1", SORU, "tr", "2026-09-08")
    kalan = [k for k in depo if k.startswith("users/u1/conversations/eski")]
    assert len(kalan) == 25          # hiçbiri silinmedi


def test_bos_metin_tohumlamaz(depo):
    assert chat_history.seed_assistant_message("u1", "  ", "tr", "g") is None
    assert depo == {}


def test_firestore_yoksa_sessiz(monkeypatch):
    monkeypatch.setattr(chat_history.firestore_client, "get_client",
                        lambda: None)
    assert chat_history.seed_assistant_message("u1", SORU, "tr", "g") is None


def test_firestore_firlatirsa_sessiz(monkeypatch):
    class _Patlayan:
        def collection(self, ad):
            raise RuntimeError("firestore down")

    monkeypatch.setattr(chat_history.firestore_client, "get_client",
                        lambda: _Patlayan())
    # Bildirim akışı bir arşiv yazımı yüzünden düşmemeli.
    assert chat_history.seed_assistant_message("u1", SORU, "tr", "g") is None


# ---------------------------------------------------------------------------
# prepare(): bağlam konu dokümanından gelir
# ---------------------------------------------------------------------------

def test_prepare_tohum_sorusunu_ve_bekleme_durumunu_tasir(depo):
    chat_history.seed_assistant_message("u1", SORU, "tr", "2026-09-08")
    hazir = chat_history.prepare("u1", "ask-2026-09-08")
    assert hazir.create is False
    assert hazir.message_count == 1
    assert hazir.seed_question == SORU
    assert hazir.seed_pending is True


def test_cevaplandiktan_sonra_bekleme_biter(depo):
    """5. turda model hâlâ 'bu benim soruma cevap' sanmamalı."""
    chat_history.seed_assistant_message("u1", SORU, "tr", "2026-09-08")
    depo[KONU]["messageCount"] = 3          # soru + cevap + yanıt
    hazir = chat_history.prepare("u1", "ask-2026-09-08")
    assert hazir.seed_question == SORU      # bağlam korunur
    assert hazir.seed_pending is False      # iddia düşer


def test_sirodan_konuda_tohum_alanlari_bos(depo):
    depo["users/u1/conversations/k1"] = {"title": "x", "messageCount": 4}
    hazir = chat_history.prepare("u1", "k1")
    assert hazir.seed_question is None
    assert hazir.seed_pending is False


# ---------------------------------------------------------------------------
# Tohum + tur zinciri
# ---------------------------------------------------------------------------

def test_tohumun_uzerine_yazilan_tur_sayaci_dogru(depo):
    """Tohum(1) + kullanıcı + yanıt = 3; başlık DEĞİŞMEZ."""
    chat_history.seed_assistant_message("u1", SORU, "tr", "2026-09-08")
    baslik = depo[KONU]["title"]
    hazir = chat_history.prepare("u1", "ask-2026-09-08")
    chat_history.write_turn("u1", hazir, "Kötü geçti", "Duydum seni…", "tr")

    assert depo[KONU]["messageCount"] == 3
    assert depo[KONU]["title"] == baslik          # merge yolu, üzerine yazmaz
    assert depo[KONU]["seedQuestion"] == SORU     # korunur
    gonderenler = [m["sender"] for m in
                   sorted(_mesajlar(depo), key=lambda m: m["createdAt"])]
    assert gonderenler == ["AI", "USER", "AI"]


def test_cevap_verilince_omur_uzar(depo):
    """Cevaplanan tohum sıradan bir konuşmaya dönüşür (30 gün)."""
    chat_history.seed_assistant_message("u1", SORU, "tr", "2026-09-08")
    kisa = depo[KONU]["expireAt"]
    hazir = chat_history.prepare("u1", "ask-2026-09-08")
    chat_history.write_turn("u1", hazir, "iyiydi", "güzel", "tr")
    assert depo[KONU]["expireAt"] > kisa


# ---------------------------------------------------------------------------
# Prompt: fısıltı en sonda ve iddiası koşullu
# ---------------------------------------------------------------------------

def test_fisilti_kullanici_mesajinin_hemen_ustunde():
    """Soru, cevabın neye cevap olduğu modele en yakın yerde dursun."""
    from services.prompt_composer import compose_chat_message
    from services.prompts import tr as p

    metin = compose_chat_message(
        "Kötü geçti", [], memory="hafıza satırı", chart="harita satırı",
        seed_question=SORU, seed_pending=True, lang="tr")
    assert metin.index(SORU) > metin.index("hafıza satırı")
    assert metin.index(SORU) > metin.index("harita satırı")
    assert metin.index(SORU) < metin.index(p.USER_MESSAGE_LABEL)


def test_fisilti_iddiasi_bekleme_durumuna_bagli():
    from services.prompt_composer import compose_chat_message

    bekleyen = compose_chat_message("Kötü geçti", [], seed_question=SORU,
                                    seed_pending=True, lang="tr")
    gecmis = compose_chat_message("Peki ya yarın?", [], seed_question=SORU,
                                  seed_pending=False, lang="tr")
    assert "CEVABIDIR" in bekleyen
    assert "CEVABIDIR" not in gecmis      # 5. turda iddia edilmez
    assert SORU in gecmis                 # ama bağlam korunur


def test_fisilti_yoksa_mesaj_degismez():
    from services.prompt_composer import compose_chat_message
    assert compose_chat_message("selam", [], lang="tr") == "selam"


def test_fisilti_iki_dilde_de_var():
    from services.prompt_composer import compose_chat_message
    for dil, imza in (("tr", "BU KONUŞMAYI SEN BAŞLATTIN"),
                      ("en", "YOU STARTED THIS CONVERSATION")):
        metin = compose_chat_message("x", [], seed_question="Q",
                                     seed_pending=True, lang=dil)
        assert imza in metin


# ---------------------------------------------------------------------------
# Gemini: contents "model" ile BAŞLAYAMAZ
# ---------------------------------------------------------------------------

def test_gemini_icerigi_user_ile_baslar(monkeypatch):
    """Rytho'nun ilk sözüyle açılan konuşmada geçmiş yalnız AI kalemi olur.

    Geçersiz istek üç yapılandırma varyantını da yakar, `chat` None döner
    ve kullanıcının jetonu iade edilir — tek satırlık koruma buna değer.
    """
    from services import gemini_service

    yakalanan = {}

    class _SahteModels:
        def generate_content(self, model, contents, config):
            yakalanan["contents"] = contents
            raise RuntimeError("dur")

    class _SahteClient:
        models = _SahteModels()

    monkeypatch.setattr(gemini_service, "_get_client", lambda: _SahteClient())
    gemini_service.chat([{"sender": "AI", "text": SORU}], "Kötü geçti", "tr")

    icerik = yakalanan["contents"]
    assert icerik[0]["role"] == "user"
    assert icerik[0]["parts"][0]["text"] == "Kötü geçti"


def test_gemini_bastaki_ai_atlanir_ortadaki_kalir(monkeypatch):
    from services import gemini_service

    yakalanan = {}

    class _SahteModels:
        def generate_content(self, model, contents, config):
            yakalanan["contents"] = contents
            raise RuntimeError("dur")

    class _SahteClient:
        models = _SahteModels()

    monkeypatch.setattr(gemini_service, "_get_client", lambda: _SahteClient())
    gemini_service.chat([
        {"sender": "AI", "text": "tohum"},
        {"sender": "USER", "text": "cevap"},
        {"sender": "AI", "text": "yanit"},
    ], "devam", "tr")

    roller = [c["role"] for c in yakalanan["contents"]]
    assert roller == ["user", "model", "user"]


# ---------------------------------------------------------------------------
# Hafıza: ayrıcalık istemci beyanından DEĞİL sunucu gerçeğinden
# ---------------------------------------------------------------------------

def test_tohum_cevabi_tur_kapisini_atlar(monkeypatch):
    from services import memory_extractor as me

    monkeypatch.setattr(me.entitlements, "consume_quota",
                        lambda uid, key, limit: True)
    monkeypatch.setattr(me.gemini_service, "extract_json",
                        lambda *a, **k: '{"facts": [], "mood": ""}')
    monkeypatch.setattr(me.memory_service, "upsert_facts",
                        lambda *a, **k: {"facts": []})

    # Tek mesaj: normalde MIN_USER_TURNS kapısına takılır.
    assert me.extract_and_store("u1", [], "kötü geçti") is None
    # Sunucu tohumun cevaplanmadığını BİLİYOR → kapı atlanır.
    assert me.extract_and_store("u1", [], "kötü geçti",
                                seed_answer=True) is not None
