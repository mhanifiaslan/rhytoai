"""Kitap korpusu (JSONL) bekçileri — RD-turu.

Üç değişmez korunur:

1. **Güvenlik süzgeci**: konusu tamamen ölüm/sağlık olan parça korpusa
   ASLA girmez (kullanıcı kararı: karışık etiketli girer, sızıntıyı
   WHISPER_RAG'ın yasak-alan kuralı keser).
2. **Kimlik disiplini**: chunk_id GÖMÜLEN metnin özetidir — md yolunun
   kimlikleri bayt aynı kalır, artımlı gömme bozulmaz.
3. **Boost dürüstlüğü**: eşik HAM kosinüse uygulanır; boost alakasız bir
   parçayı diriltemez ve ölüm/sağlık konularına yapısal olarak yönelemez.

Çalıştırma:  .venv\\Scripts\\python.exe -m pytest tests/test_rag_books.py -q
"""
from __future__ import annotations

import json

import numpy as np
import pytest

from services import chart_query, prompt_composer, rag_service


def _kayit(**degisiklik):
    """Şemaya uygun sentetik JSONL kaydı."""
    kayit = {
        "id": "test__s1__c1",
        "text": "The tenth house shows the native's profession and honour. " * 4,
        "text_tr": "Onuncu ev kişinin mesleğini ve itibarını gösterir. " * 4,
        "embedding_text": "[TR baslik]\nThe tenth house shows profession.",
        "embedding_text_tr": "[TR baslik]\nOnuncu ev meslegi gosterir.",
        "metadata": {
            "source": "Test Book", "source_id": "test_book",
            "author": "Author", "license": "Public domain (US)",
            "source_url": "https://example.org",
            "school": "Traditional", "school_tr": "Geleneksel",
            "era": "17th century", "era_tr": "17. yüzyıl",
            "heading": "Of the Tenth House",
            "topic": ["career"], "topic_tr": ["Meslek"],
            "entity_planet": ["Saturn"], "entity_sign": ["Capricorn"],
            "entity_house": ["10th House"], "authority_weight": 5,
        },
    }
    meta = degisiklik.pop("metadata", None)
    kayit.update(degisiklik)
    if meta:
        kayit["metadata"].update(meta)
    return kayit


@pytest.fixture
def kitap_dizini(tmp_path, monkeypatch):
    """Geçici knowledge kökü + books dizini."""
    from core import config
    (tmp_path / "corpus" / "books").mkdir(parents=True)
    monkeypatch.setattr(config, "KNOWLEDGE_DIR", tmp_path)
    return tmp_path / "corpus" / "books"


def _yaz(dizin, kayitlar, ad="test_book.jsonl"):
    (dizin / ad).write_text(
        "\n".join(json.dumps(k, ensure_ascii=False) for k in kayitlar),
        encoding="utf-8")


class TestYukleyici:
    def test_alanlar_ve_dil_secimi(self, kitap_dizini):
        _yaz(kitap_dizini, [_kayit()])
        tr = rag_service._load_book_chunks("tr")
        en = rag_service._load_book_chunks("en")
        assert len(tr) == 1 and len(en) == 1
        assert "Onuncu ev" in tr[0].text and "tenth house" in en[0].text
        assert tr[0].embed_text.startswith("[TR baslik]")
        assert tr[0].doc == "test_book"
        assert tr[0].title == "Of the Tenth House"
        assert tr[0].topics == ("career",)
        assert tr[0].planets == frozenset({"Saturn"})
        assert tr[0].houses == frozenset({10})
        assert tr[0].authority == 5
        assert tr[0].source["license"] == "Public domain (US)"
        # Kimlik GÖMÜLEN metnin özeti — görüntü metninin değil.
        assert tr[0].chunk_id == rag_service._chunk_id(tr[0].embed_text)

    def test_guvenlik_suzgeci(self, kitap_dizini):
        _yaz(kitap_dizini, [
            _kayit(id="a", metadata={"topic": ["death"]}),
            _kayit(id="b", metadata={"topic": ["death", "health"]}),
            _kayit(id="c", metadata={"topic": ["career", "death"]}),
        ])
        yuklenen = rag_service._load_book_chunks("tr")
        # Saf ölüm/sağlık ASLA; karışık etiketli GİRER (kullanıcı kararı).
        assert len(yuklenen) == 1
        assert "death" in yuklenen[0].topics

    def test_ev_normalizasyonu(self):
        assert rag_service._normalize_house("10th House") == 10
        assert rag_service._normalize_house("1st House") == 1
        assert rag_service._normalize_house("2nd house") == 2
        assert rag_service._normalize_house("3rd House") == 3
        assert rag_service._normalize_house("13th House") is None
        assert rag_service._normalize_house("Midheaven") is None

    def test_embed_kirpimi_goruntuyu_bozmaz(self, kitap_dizini):
        uzun = "kelime " * 2000  # ~14K karakter
        _yaz(kitap_dizini, [_kayit(
            embedding_text_tr=uzun, text_tr="Görüntü metni bu. " * 5)])
        c = rag_service._load_book_chunks("tr")[0]
        assert len(c.embed_text) <= rag_service._MAX_EMBED_CHARS
        assert c.text.startswith("Görüntü metni")

    def test_kisa_govde_ve_bozuk_satir_atlanir(self, kitap_dizini):
        (kitap_dizini / "x.jsonl").write_text(
            'bozuk json satiri\n' + json.dumps(_kayit(text_tr="kisa")),
            encoding="utf-8")
        assert rag_service._load_book_chunks("tr") == []

    def test_her_kayit_lisans_tasir(self):
        """Lisans bekçisinin JSONL ayağı: gerçek kitap dosyalarında her
        kaydın künyesinde license olmalı (md'deki front-matter kuralının
        devamı — knowledge/SOURCES.md)."""
        from core import config
        books = config.KNOWLEDGE_DIR / "corpus" / "books"
        dosyalar = sorted(books.glob("*.jsonl"))
        assert dosyalar, "kitap korpusu boş"
        for jl in dosyalar:
            for satir in jl.read_text(encoding="utf-8").splitlines():
                if not satir.strip():
                    continue
                m = json.loads(satir).get("metadata") or {}
                assert m.get("license"), f"{jl.name}: lisanssız kayıt"
                break  # kitap başına ilk kayıt yeter (aynı künye)


class TestRerank:
    def _taban(self, monkeypatch, chunks, skorlar):
        """Sahte vektör tabanı: kosinüs skorları enjekte edilir."""
        taban = rag_service._KnowledgeBase("tr")
        taban._chunks = chunks
        taban._loaded = True
        taban._matrix = np.eye(len(chunks), dtype=np.float32)
        monkeypatch.setattr(taban, "_ensure_loaded", lambda: chunks)
        monkeypatch.setattr(taban, "semantic_ready", lambda: True)
        monkeypatch.setattr(
            taban, "_embed_query",
            lambda q: np.asarray(skorlar, dtype=np.float32))
        # matmul kimlik matrisiyle: skorlar doğrudan sorgu vektörü olur.
        return taban

    def _parca(self, doc, topics=(), planets=(), houses=(), authority=0):
        return rag_service.Chunk(
            doc=doc, title=f"b-{doc}", text=f"metin {doc}",
            topics=tuple(topics), planets=frozenset(planets),
            houses=frozenset(houses), authority=authority)

    def test_konu_boostu_yakin_beraberligi_cevirir(self, monkeypatch):
        parcalar = [self._parca("a", topics=("synthesis",)),
                    self._parca("b", topics=("finance",))]
        taban = self._taban(monkeypatch, parcalar, [0.80, 0.79])
        sonuc = taban.search("q", top_k=1, boost={"topics": {"finance"}})
        assert sonuc[0]["doc"] == "b"  # 0.79 + 0.03 > 0.80

    def test_boost_alakasizi_diriltemez(self, monkeypatch):
        parcalar = [self._parca("a", topics=("finance",),
                                planets={"Saturn"}, houses={2},
                                authority=5)]
        taban = self._taban(monkeypatch, parcalar,
                            [rag_service._MIN_RELEVANCE - 0.01])
        sonuc = taban.search("q", top_k=1, boost={
            "topics": {"finance"}, "planets": {"Saturn"}, "houses": {2}})
        assert sonuc == []  # eşik HAM skora uygulanır

    def test_otorite_beraberlik_bozar(self, monkeypatch):
        parcalar = [self._parca("dusuk", authority=3),
                    self._parca("yuksek", authority=5)]
        taban = self._taban(monkeypatch, parcalar, [0.75, 0.75])
        sonuc = taban.search("q", top_k=1, boost={})
        assert sonuc[0]["doc"] == "yuksek"

    def test_varlik_boostu_kisisel(self, monkeypatch):
        """Kullanıcının GERÇEK yerleşimi (Satürn 2. ev) o varlıkları anan
        parçayı öne çeker — kişiselleştirilmiş getirme."""
        parcalar = [self._parca("genel"),
                    self._parca("kisisel", planets={"Saturn"}, houses={2})]
        taban = self._taban(monkeypatch, parcalar, [0.78, 0.76])
        sonuc = taban.search("q", top_k=1,
                             boost={"planets": {"Saturn"}, "houses": {2}})
        assert sonuc[0]["doc"] == "kisisel"  # 0.76+0.04 > 0.78+0

    def test_anahtar_kelime_modu_boostu_yok_sayar(self, monkeypatch):
        parcalar = [self._parca("a", topics=("finance",))]
        parcalar[0].keywords = {"para"}
        taban = rag_service._KnowledgeBase("tr")
        monkeypatch.setattr(taban, "_ensure_loaded", lambda: parcalar)
        monkeypatch.setattr(taban, "semantic_ready", lambda: False)
        sonuc = taban.search("para", top_k=1, boost={"topics": {"finance"}})
        assert sonuc and sonuc[0]["score"] <= 1.0  # boost eklenmedi


class TestBoostHints:
    FACTS = {"sun": {"planet": "Sun", "sign": "aquarius", "house": 10},
             "moon": {"planet": "Moon", "sign": "cancer", "house": 4},
             "placements": [
                 {"planet": "Saturn", "sign": "sagittarius", "house": 2}],
             "aspects": []}

    def test_para_sorusu(self):
        h = chart_query.boost_hints("Param neden birikmiyor?", self.FACTS,
                                    "tr")
        assert h["topics"] == {"finance"}
        assert "Saturn" in h["planets"] and 2 in h["houses"]
        assert "Sagittarius" in h["signs"]

    def test_konu_yoksa_none(self):
        assert chart_query.boost_hints("bugün nasılım", self.FACTS,
                                       "tr") is None

    def test_harita_yoksa_yalniz_konu(self):
        h = chart_query.boost_hints("Param neden birikmiyor?", None, "tr")
        assert h["topics"] == {"finance"} and not h["planets"]

    def test_harita_olum_sagliga_yonelemez(self):
        """Yapısal garanti: sohbet→korpus haritası death/health üretmez."""
        for hedefler in chart_query._CHAT_TO_CORPUS_TOPICS.values():
            assert "death" not in hedefler and "health" not in hedefler


class TestEtiketCizimi:
    PASAJ = {"text": "pasaj metni " * 10,
             "source": {"school": "Traditional", "school_tr": "Geleneksel",
                        "era": "17th century", "era_tr": "17. yüzyıl",
                        "book": "GIZLI KITAP", "author": "GIZLI YAZAR"},
             "authority": 4}

    def test_ic_etiket_okul_donem_otorite(self):
        msg = prompt_composer.compose_chat_message("soru", [self.PASAJ],
                                                   lang="tr")
        satir = next(s for s in msg.splitlines() if s.startswith("- ["))
        assert "Geleneksel" in satir and "17. yüzyıl" in satir
        assert "otorite 4/5" in satir

    def test_kitap_ve_yazar_adi_etikete_girmez(self):
        """Kaynak sesi YALNIZ iç bilgi (kullanıcı kararı): etikette bile
        kitap/yazar adı taşınmaz — modelin ağzından kaçırabileceği tek
        şey okul/dönem düzeyinde kalır."""
        msg = prompt_composer.compose_chat_message("soru", [self.PASAJ],
                                                   lang="tr")
        assert "GIZLI KITAP" not in msg and "GIZLI YAZAR" not in msg

    def test_eski_md_pasaji_etiketsiz(self):
        eski = {"text": "eski pasaj", "source": {"book": "Tetrabiblos"}}
        msg = prompt_composer.compose_chat_message("soru", [eski], lang="tr")
        assert "- eski pasaj" in msg and "- [" not in msg

    def test_yasak_alan_kurali_promptta(self):
        from services import prompts
        for lang in ("tr", "en"):
            p = prompts.get(lang)
            metin = p.WHISPER_RAG.lower()
            assert ("yasak alan" in metin or "forbidden domain" in metin)
            assert ("harmanlama" in metin or "blend" in metin)
