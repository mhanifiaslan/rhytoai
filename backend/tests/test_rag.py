"""RAG testleri: toplu embedding paketleme ve sessiz bozulmaya karşı korumalar.

Çalıştırma:  .venv\\Scripts\\python.exe -m pytest tests/test_rag.py -q
"""
import json

import pytest

from core import config
from services import rag_service
from services.rag_service import _KnowledgeBase, _as_contents


# --------------------------------------------------------------------------
# Toplu embedding paketleme — asıl hatanın olduğu yer
# --------------------------------------------------------------------------

def test_her_metin_ayri_content_olur():
    """Düz string listesi verilirse SDK hepsini TEK Content'in parçaları sayar
    ve tek embedding döndürür. Her metin ayrı bir Content olmak zorunda."""
    icerikler = _as_contents(["bir", "iki", "uc"])

    assert len(icerikler) == 3
    for icerik, beklenen in zip(icerikler, ["bir", "iki", "uc"]):
        assert list(icerik.keys()) == ["parts"]
        assert len(icerik["parts"]) == 1, "bir Content'te birden fazla parça olmamalı"
        assert icerik["parts"][0]["text"] == beklenen


def test_bos_liste_bos_paket_uretir():
    assert _as_contents([]) == []


# --------------------------------------------------------------------------
# Kısmi sonuç koruması
# --------------------------------------------------------------------------

def _sahte_korpus(kb: _KnowledgeBase, adet: int) -> list:
    from services.rag_service import Chunk
    return [Chunk(doc="d", title=f"b{i}", text=f"metin {i}") for i in range(adet)]


def test_eksik_vektor_onbellege_yazilmaz(tmp_path, monkeypatch):
    """Kısmi embedding yazılırsa her açılışta yeniden denenir ve arama sessizce
    anahtar kelime modunda kalır."""
    onbellek = tmp_path / "rag_embeddings.json"
    monkeypatch.setattr(rag_service, "_embed_cache_file", lambda lang: onbellek)

    kb = _KnowledgeBase()
    parcalar = _sahte_korpus(kb, 5)
    monkeypatch.setattr(rag_service, "_load_chunks", lambda lang: parcalar)
    # 5 parça istenirken 2 vektör dönmüş gibi davran
    monkeypatch.setattr(kb, "_embed_texts", lambda texts: [[0.1], [0.2]])

    kb._ensure_loaded()

    assert not onbellek.exists(), "eksik embedding önbelleğe yazılmamalı"
    assert kb.semantic_ready() is False


def test_tam_vektor_onbellege_yazilir(tmp_path, monkeypatch):
    onbellek = tmp_path / "rag_embeddings.json"
    monkeypatch.setattr(rag_service, "_embed_cache_file", lambda lang: onbellek)

    kb = _KnowledgeBase()
    parcalar = _sahte_korpus(kb, 3)
    monkeypatch.setattr(rag_service, "_load_chunks", lambda lang: parcalar)
    monkeypatch.setattr(kb, "_embed_texts",
                        lambda texts: [[float(i)] for i in range(len(texts))])

    kb._ensure_loaded()

    assert onbellek.exists()
    kayit = json.loads(onbellek.read_text(encoding="utf-8"))
    assert len(kayit["embeddings"]) == 3
    assert kb.semantic_ready() is True


def test_embed_texts_anahtar_yokken_none_doner(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_API_KEY", None)
    kb = _KnowledgeBase()
    assert kb._embed_texts(["deneme"]) is None


# --------------------------------------------------------------------------
# Arama modu gözlemlenebilir olmalı
# --------------------------------------------------------------------------

def test_arama_modu_disa_acik(monkeypatch):
    """Anlamsal aramanın anahtar kelimeye düşmesi görünür olmalı; daha önce
    hiçbir yerde görünmediği için fark edilmemişti."""
    monkeypatch.setattr(rag_service.knowledge_base, "semantic_ready", lambda: True)
    assert rag_service.search_mode() == "vector"

    monkeypatch.setattr(rag_service.knowledge_base, "semantic_ready", lambda: False)
    assert rag_service.search_mode() == "keyword"


def test_vektor_yoksa_arama_anahtar_kelimeye_duser(monkeypatch):
    kb = _KnowledgeBase()
    from services.rag_service import Chunk, _tokenize

    parcalar = [
        Chunk(doc="d", title="ay", text="ay evresi dolunay yorumu",
              keywords=_tokenize("ay evresi dolunay yorumu")),
        Chunk(doc="d", title="mars", text="mars retro gerilim",
              keywords=_tokenize("mars retro gerilim")),
    ]
    monkeypatch.setattr(rag_service, "_load_chunks", lambda lang: parcalar)
    monkeypatch.setattr(kb, "_embed_texts", lambda texts: None)
    monkeypatch.setattr(kb, "_embed_query",
                        lambda q: pytest.fail("vektör yokken sorgu gömülmemeli"))

    sonuc = kb.search("dolunay yorumu")

    assert kb.semantic_ready() is False
    assert sonuc, "anahtar kelime modunda da sonuç dönmeli"
    assert sonuc[0]["title"] == "ay"


# --------------------------------------------------------------------------
# Çok dillilik
# --------------------------------------------------------------------------

def test_her_dil_ayri_taban_kullanir():
    """Tek tabanda karıştırılsaydı İngilizce sorgu Türkçe pasajlarla skorlanır
    ve yorum kalitesi düşerdi."""
    tr = rag_service.base_for("tr")
    en = rag_service.base_for("en")

    assert tr is not en
    assert tr.lang == "tr" and en.lang == "en"
    # Aynı dil için aynı örnek dönmeli (tembel önbellek)
    assert rag_service.base_for("en") is en


def test_desteklenmeyen_dil_varsayilana_duser():
    assert rag_service.base_for("de").lang == "tr"
    assert rag_service.base_for(None).lang == "tr"


def test_embedding_onbellegi_dil_basina_ayri():
    """Tek dosya olsaydı diller birbirinin vektörlerini geçersiz kılardı."""
    assert (rag_service._embed_cache_file("tr")
            != rag_service._embed_cache_file("en"))


def test_korpus_dizini_dile_gore_secilir():
    tr_dizin = rag_service._corpus_dir("tr")
    en_dizin = rag_service._corpus_dir("en")
    assert tr_dizin.name == "tr"
    assert en_dizin.name == "en"
    # Korpusu olmayan dil varsayılana düşer, boş bağlamla çalışmaz
    assert rag_service._corpus_dir("de").name == "tr"


def test_ingilizce_korpus_yuklenir_ve_turkce_degil():
    """İngilizce korpus gerçekten var ve içeriği İngilizce olmalı."""
    parcalar = rag_service._load_chunks("en")
    assert parcalar, "İngilizce korpus boş"

    metin = " ".join(c.text for c in parcalar).lower()
    assert "day master" in metin
    assert "temperament" in metin
    # Türkçe korpustan sızma olmamalı
    assert "ahlat-ı erbaa" not in metin


def test_turkce_korpus_hala_yuklenir():
    parcalar = rag_service._load_chunks("tr")
    assert parcalar
    metin = " ".join(c.text for c in parcalar).lower()
    assert "day master" in metin or "günün efendisi" in metin
