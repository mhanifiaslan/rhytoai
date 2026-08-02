"""RAG testleri: parçalama, vektör artefaktı ve sessiz bozulmaya karşı korumalar.

Bu katmanın kusurlarının ortak özelliği **sessiz** olmaları: hiçbiri hata
vermiyor, yalnızca cevap kalitesi düşüyor. Testlerin çoğu tam da onları
görünür kılmak için var.

Çalıştırma:  .venv\\Scripts\\python.exe -m pytest tests/test_rag.py -q
"""
import json

import numpy as np
import pytest

from core import config
from services import rag_service
from services.rag_service import Chunk, _as_contents, _KnowledgeBase


@pytest.fixture
def gecici_artefakt(tmp_path, monkeypatch):
    """Testler gerçek artefakta dokunmaz."""
    monkeypatch.setattr(config, "KNOWLEDGE_DIR", tmp_path)
    return tmp_path


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


def test_embed_texts_anahtar_yokken_none_doner(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_API_KEY", None)
    assert _KnowledgeBase()._embed_texts(["deneme"]) is None


# --------------------------------------------------------------------------
# Parçalama — kitap için yeniden kuruldu
# --------------------------------------------------------------------------

def test_uzun_govde_boyut_sinirinda_bolunur():
    """Bölme yalnızca ## başlıklarındanken bir kitap bölümü tek parçada
    binlerce kelime oluyordu; embedding o parçanın ORTALAMASINI alır ve
    arama körelir."""
    cumle = "Satürn burada ağır ve yavaş bir etki bırakır. "
    govde = cumle * 120  # ~5.400 karakter
    parcalar = rag_service._split_body(govde)

    assert len(parcalar) > 1
    assert all(len(p) <= rag_service.MAX_CHUNK_CHARS for p in parcalar)


def test_kisa_govde_bolunmez():
    govde = "Kısa bir bölüm."
    assert rag_service._split_body(govde) == [govde]


def test_parcalar_ortusur():
    """Bir cümlenin tam ortasından bölünmesi anlamı öldürür; sınırdaki cümle
    iki parçada da bulunmalı."""
    cumleler = [f"Bu {i} numarali cumledir ve yeterince uzundur."
                for i in range(60)]
    parcalar = rag_service._split_body(" ".join(cumleler))

    assert len(parcalar) > 1
    for onceki, sonraki in zip(parcalar, parcalar[1:]):
        kuyruk = onceki[-rag_service.CHUNK_OVERLAP_CHARS:]
        ortak = [k for k in kuyruk.split() if k and k in sonraki]
        assert ortak, "ardışık parçalar hiç örtüşmüyor"


def test_noktalamasiz_uzun_metin_de_bolunur():
    """Kaynak metinlerde noktalama olmadan uzayan pasajlar var; bölünmezse
    tek bir dev parça bütün aramayı çarpıtır."""
    govde = " ".join(["kelime"] * 2000)
    parcalar = rag_service._split_body(govde)
    assert all(len(p) <= rag_service.MAX_CHUNK_CHARS for p in parcalar)


def test_parca_kimligi_metne_bagli():
    """Vektör önbelleği buna göre anahtarlanıyor: metin değişmedikçe vektör
    yeniden üretilmemeli, parça yer değiştirse bile."""
    assert rag_service._chunk_id("ayni") == rag_service._chunk_id("ayni")
    assert rag_service._chunk_id("ayni") != rag_service._chunk_id("baska")


# --------------------------------------------------------------------------
# Künye — lisans savunması buna bağlı
# --------------------------------------------------------------------------

def test_kunye_okunur_ve_parcaya_islenir(tmp_path, monkeypatch):
    """Eser kamu malı olsa bile ÇEVİRİSİ ayrı telif taşır; hangi baskının
    kullanıldığı korpusun içinde kayıtlı olmalı."""
    korpus = tmp_path / "corpus" / "en"
    korpus.mkdir(parents=True)
    (korpus / "kitap.md").write_text(
        "---\n"
        "book: Tetrabiblos\n"
        "translator: J.M. Ashmand (1822)\n"
        "license: public-domain\n"
        "---\n"
        "# Tetrabiblos\n\n"
        "## Of the Influence of the Planets\n"
        "Saturn is cold and dry, and his influence is chiefly heavy.\n",
        encoding="utf-8")
    monkeypatch.setattr(config, "KNOWLEDGE_DIR", tmp_path)

    parcalar = rag_service._load_chunks("en")

    assert parcalar
    kunye = parcalar[0].source
    assert kunye["book"] == "Tetrabiblos"
    assert kunye["license"] == "public-domain"
    # Künye metnin kendisine karışmamalı
    assert "license" not in parcalar[0].text
    # Kitap adı parçanın başlığına girmeli: parça tek başına vektörleniyor
    assert parcalar[0].text.startswith("Tetrabiblos — ")


def test_kunyesiz_dosya_da_yuklenir(tmp_path, monkeypatch):
    """Kendi yazdığımız sentez dosyalarında künye isteğe bağlı."""
    korpus = tmp_path / "corpus" / "tr"
    korpus.mkdir(parents=True)
    (korpus / "sentez.md").write_text(
        "# Kadim Notlar\n\n## Ay evresi\nDolunay tamamlanma vaktidir ve "
        "geriye bakmayı kolaylaştırır.\n", encoding="utf-8")
    monkeypatch.setattr(config, "KNOWLEDGE_DIR", tmp_path)

    parcalar = rag_service._load_chunks("tr")
    assert parcalar
    assert parcalar[0].source == {}


# --------------------------------------------------------------------------
# Vektör artefaktı — çalışma zamanı vektörlemesinin yerini aldı
# --------------------------------------------------------------------------

def test_artefakt_yazilip_okunur(gecici_artefakt):
    vektorler = {"a": np.array([1.0, 0.0], dtype=np.float32),
                 "b": np.array([0.0, 1.0], dtype=np.float32)}
    rag_service.write_artifact("tr", vektorler)

    geri = rag_service.read_artifact("tr")
    assert set(geri) == {"a", "b"}
    assert np.allclose(geri["a"], [1.0, 0.0])


def test_artefakt_npy_olarak_saklanir(gecici_artefakt):
    """JSON'a yazılsaydı 900 parça x 3072 boyut ~55 MB metin ederdi; aynı veri
    float32 .npy olarak ~11 MB."""
    meta_path, vec_path = rag_service.embedding_files("tr")
    rag_service.write_artifact("tr", {"a": np.zeros(8, dtype=np.float32)})

    assert vec_path.suffix == ".npy"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    assert meta["ids"] == ["a"]
    assert meta["dim"] == 8
    # Vektörlerin kendisi JSON'da OLMAMALI
    assert "vectors" not in meta


def test_model_degisince_artefakt_yok_sayilir(gecici_artefakt, monkeypatch):
    """Aynı uzayda olmayan iki vektörün kosinüsü anlamsızdır; eski vektörlerle
    devam etmek sessiz bir kalite kaybı olurdu."""
    rag_service.write_artifact("tr", {"a": np.ones(4, dtype=np.float32)})
    assert rag_service.read_artifact("tr")

    monkeypatch.setattr(config, "EMBEDDING_MODEL", "baska-model")
    assert rag_service.read_artifact("tr") == {}


def test_bozuk_artefakt_yok_sayilir(gecici_artefakt):
    meta_path, vec_path = rag_service.embedding_files("tr")
    rag_service.write_artifact("tr", {"a": np.ones(4, dtype=np.float32)})
    # Kimlik sayısı ile satır sayısını ayrıştır
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["ids"] = ["a", "b", "c"]
    meta_path.write_text(json.dumps(meta), encoding="utf-8")

    assert rag_service.read_artifact("tr") == {}


def test_artefakt_dil_basina_ayri():
    """Tek dosya olsaydı bir dilin korpusu değişince diğerinin vektörleri de
    boşa düşerdi."""
    assert rag_service.embedding_files("tr") != rag_service.embedding_files("en")


# --------------------------------------------------------------------------
# Kısmi vektör koruması
# --------------------------------------------------------------------------

def _sahte_korpus(adet: int) -> list[Chunk]:
    parcalar = []
    for i in range(adet):
        metin = f"metin {i}"
        parcalar.append(Chunk(doc="d", title=f"b{i}", text=metin,
                              keywords=rag_service._tokenize(metin),
                              chunk_id=rag_service._chunk_id(metin)))
    return parcalar


def test_eksik_vektor_anlamsal_aramayi_kapatir(gecici_artefakt, monkeypatch):
    """Kısmi vektörle kosinüs araması yapılamaz: embedding'i olmayan parçalar
    skorlamaya giremez ve sonuçlar sessizce çarpıtılır."""
    parcalar = _sahte_korpus(5)
    monkeypatch.setattr(rag_service, "_load_chunks", lambda lang: parcalar)

    kb = _KnowledgeBase()
    # 5 parça istenirken 2 vektör dönmüş gibi davran
    monkeypatch.setattr(kb, "_embed_texts", lambda texts: [[0.1], [0.2]])
    kb._ensure_loaded()

    assert kb.semantic_ready() is False


def test_tam_vektor_artefakta_yazilir(gecici_artefakt, monkeypatch):
    parcalar = _sahte_korpus(3)
    monkeypatch.setattr(rag_service, "_load_chunks", lambda lang: parcalar)

    kb = _KnowledgeBase()
    monkeypatch.setattr(kb, "_embed_texts",
                        lambda texts: [[float(i), 1.0] for i in range(len(texts))])
    kb._ensure_loaded()

    assert kb.semantic_ready() is True
    assert rag_service.read_artifact("tr")
    assert len(rag_service.read_artifact("tr")) == 3


def test_artefakt_varken_yeniden_vektorlenmez(gecici_artefakt, monkeypatch):
    """Asıl kazanç bu: soğuk başlatmada embedding çağrısı YAPILMAMALI."""
    parcalar = _sahte_korpus(4)
    monkeypatch.setattr(rag_service, "_load_chunks", lambda lang: parcalar)
    rag_service.write_artifact("tr", {
        c.chunk_id: np.array([1.0, float(i)], dtype=np.float32)
        for i, c in enumerate(parcalar)})

    kb = _KnowledgeBase()
    monkeypatch.setattr(kb, "_embed_texts",
                        lambda texts: pytest.fail(
                            "artefakt varken embedding cagrisi yapildi"))
    kb._ensure_loaded()
    assert kb.semantic_ready() is True


def test_korpusa_tek_parca_eklenince_sadece_o_vektorlenir(gecici_artefakt,
                                                          monkeypatch):
    """Önbellek TÜM korpusun sağlamasıyla anahtarlandığı sürece tek satırlık
    bir düzeltme 900 parçayı yeniden vektörletiyordu."""
    eski = _sahte_korpus(3)
    rag_service.write_artifact("tr", {
        c.chunk_id: np.array([1.0, 0.0], dtype=np.float32) for c in eski})

    yeni = eski + _sahte_korpus(4)[3:]  # 4. parça eklendi
    monkeypatch.setattr(rag_service, "_load_chunks", lambda lang: yeni)

    istenen: list[list[str]] = []

    def sahte_embed(texts):
        istenen.append(list(texts))
        return [[1.0, 0.0] for _ in texts]

    kb = _KnowledgeBase()
    monkeypatch.setattr(kb, "_embed_texts", sahte_embed)
    kb._ensure_loaded()

    assert istenen == [["metin 3"]], f"gereksiz vektorleme: {istenen}"


# --------------------------------------------------------------------------
# Arama
# --------------------------------------------------------------------------

def test_vektor_araması_en_yakini_bulur(gecici_artefakt, monkeypatch):
    parcalar = _sahte_korpus(3)
    monkeypatch.setattr(rag_service, "_load_chunks", lambda lang: parcalar)
    rag_service.write_artifact("tr", {
        parcalar[0].chunk_id: np.array([1.0, 0.0], dtype=np.float32),
        parcalar[1].chunk_id: np.array([0.0, 1.0], dtype=np.float32),
        parcalar[2].chunk_id: np.array([-1.0, 0.0], dtype=np.float32),
    })

    kb = _KnowledgeBase()
    monkeypatch.setattr(kb, "_embed_query",
                        lambda q: np.array([0.0, 1.0], dtype=np.float32))
    sonuc = kb.search("herhangi", top_k=2)

    assert sonuc[0]["title"] == "b1"
    # Negatif skorlu parça hiç dönmemeli
    assert all(s["score"] > 0 for s in sonuc)


def test_ilgisiz_sorgu_bos_doner(gecici_artefakt, monkeypatch):
    """Korpusta karsiligi olmayan soruda pasaj DONMEMELI.

    Esik olculerek konuldu: korpusta karsiligi olan sorgular 0,71-0,84 skor
    aliyor, hic ilgisi olmayanlar 0,49-0,56'da kaliyor. Esik olmadan alakasiz
    bir soruda en yakin pasaj yine donuyor ve model kadim bir metni ilgisiz
    bir konuya baglamaya calisiyordu — cevap zorlama cikiyordu. Kaynak yoksa
    kaynaksiz cevap vermek daha durust.
    """
    parcalar = _sahte_korpus(3)
    monkeypatch.setattr(rag_service, "_load_chunks", lambda lang: parcalar)
    rag_service.write_artifact("tr", {
        c.chunk_id: np.array([1.0, 0.0], dtype=np.float32) for c in parcalar})

    kb = _KnowledgeBase()
    # Esigin ALTINDA kalan bir sorgu vektoru
    dusuk = rag_service._MIN_RELEVANCE - 0.1
    import math
    aci = math.acos(dusuk)
    monkeypatch.setattr(kb, "_embed_query", lambda q: np.array(
        [math.cos(aci), math.sin(aci)], dtype=np.float32))
    assert kb.search("alakasiz soru") == []


def test_esik_yalnizca_vektor_modunda_uygulanir(gecici_artefakt, monkeypatch):
    """Anahtar kelime modunun skoru tamamen farkli bir olcekte (ortusen
    kelime sayisi / sorgu uzunlugu); orada 0,62 esigi her seyi elerdi."""
    parcalar = [
        Chunk(doc="d", title="ay", text="ay evresi dolunay yorumu",
              keywords=rag_service._tokenize("ay evresi dolunay yorumu"),
              chunk_id="1"),
    ]
    monkeypatch.setattr(rag_service, "_load_chunks", lambda lang: parcalar)
    kb = _KnowledgeBase()
    monkeypatch.setattr(kb, "_embed_texts", lambda texts: None)

    sonuc = kb.search("dolunay yorumu ne anlama gelir")
    assert kb.semantic_ready() is False
    assert sonuc, "anahtar kelime modunda esik uygulanmamali"
    assert sonuc[0]["score"] < rag_service._MIN_RELEVANCE


def test_vektor_yoksa_arama_anahtar_kelimeye_duser(gecici_artefakt, monkeypatch):
    parcalar = [
        Chunk(doc="d", title="ay", text="ay evresi dolunay yorumu",
              keywords=rag_service._tokenize("ay evresi dolunay yorumu"),
              chunk_id="1"),
        Chunk(doc="d", title="mars", text="mars retro gerilim",
              keywords=rag_service._tokenize("mars retro gerilim"),
              chunk_id="2"),
    ]
    monkeypatch.setattr(rag_service, "_load_chunks", lambda lang: parcalar)

    kb = _KnowledgeBase()
    monkeypatch.setattr(kb, "_embed_texts", lambda texts: None)
    monkeypatch.setattr(kb, "_embed_query",
                        lambda q: pytest.fail("vektör yokken sorgu gömülmemeli"))

    sonuc = kb.search("dolunay yorumu")

    assert kb.semantic_ready() is False
    assert sonuc, "anahtar kelime modunda da sonuç dönmeli"
    assert sonuc[0]["title"] == "ay"


def test_arama_kunyeyi_de_dondurur(gecici_artefakt, monkeypatch):
    """Atıf gösterilebilmesi için kaynak pasajla birlikte taşınmalı."""
    parca = Chunk(doc="d", title="t", text="satürn ağır",
                  keywords=rag_service._tokenize("satürn ağır"),
                  chunk_id="1", source={"book": "Tetrabiblos"})
    monkeypatch.setattr(rag_service, "_load_chunks", lambda lang: [parca])

    kb = _KnowledgeBase()
    monkeypatch.setattr(kb, "_embed_texts", lambda texts: None)
    sonuc = kb.search("satürn")
    assert sonuc[0]["source"]["book"] == "Tetrabiblos"


def test_top_k_korpustan_buyuk_olabilir(gecici_artefakt, monkeypatch):
    """argpartition k > n olduğunda patlar; korpus küçükken bu gerçek bir yol."""
    parcalar = _sahte_korpus(2)
    monkeypatch.setattr(rag_service, "_load_chunks", lambda lang: parcalar)
    kb = _KnowledgeBase()
    monkeypatch.setattr(kb, "_embed_texts", lambda texts: None)
    assert len(kb.search("metin", top_k=10)) <= 2


def test_bos_korpus_bos_doner(gecici_artefakt, monkeypatch):
    monkeypatch.setattr(rag_service, "_load_chunks", lambda lang: [])
    kb = _KnowledgeBase()
    assert kb.search("herhangi") == []
    assert kb.semantic_ready() is False


# --------------------------------------------------------------------------
# Teşhis — sessiz bozulma görünür olmalı
# --------------------------------------------------------------------------

def test_arama_modu_disa_acik(monkeypatch):
    """Anlamsal aramanın anahtar kelimeye düşmesi görünür olmalı; daha önce
    hiçbir yerde görünmediği için haftalarca fark edilmedi."""
    monkeypatch.setattr(rag_service.knowledge_base, "semantic_ready", lambda: True)
    assert rag_service.search_mode() == "vector"

    monkeypatch.setattr(rag_service.knowledge_base, "semantic_ready", lambda: False)
    assert rag_service.search_mode() == "keyword"


def test_teshis_kapsama_bilgisi_verir(gecici_artefakt, monkeypatch):
    parcalar = _sahte_korpus(3)
    monkeypatch.setattr(rag_service, "_load_chunks", lambda lang: parcalar)
    rag_service.write_artifact("tr", {
        c.chunk_id: np.array([1.0, 0.0], dtype=np.float32) for c in parcalar})

    rapor = _KnowledgeBase("tr").diagnostics()
    assert rapor["chunks"] == 3
    assert rapor["vectors"] == 3
    assert rapor["dim"] == 2
    assert rapor["mode"] == "vector"
    assert rapor["artifact"] is True


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
    assert rag_service.base_for("en") is en


def test_desteklenmeyen_dil_varsayilana_duser():
    assert rag_service.base_for("de").lang == "tr"
    assert rag_service.base_for(None).lang == "tr"


def test_korpus_dizini_dile_gore_secilir():
    assert rag_service._corpus_dir("tr").name == "tr"
    assert rag_service._corpus_dir("en").name == "en"
    # Korpusu olmayan dil varsayılana düşer, boş bağlamla çalışmaz
    assert rag_service._corpus_dir("de").name == "tr"


def test_ingilizce_korpus_yuklenir_ve_turkce_degil():
    """İngilizce korpus gerçekten var ve içeriği İngilizce olmalı."""
    parcalar = rag_service._load_chunks("en")
    assert parcalar

    metin = " ".join(c.text for c in parcalar).lower()
    assert "day master" in metin
    assert "temperament" in metin
    assert "ahlat-ı erbaa" not in metin


# --------------------------------------------------------------------------
# Lisans — ticari üründe bu bir muhafız, bir tercih değil
# --------------------------------------------------------------------------

@pytest.mark.parametrize("lang", ["tr", "en"])
def test_her_korpus_dosyasi_lisans_beyan_eder(lang):
    """Eser kamu malı olsa bile ÇEVİRİSİ ayrı telif taşır (Ashmand 1822 kamu
    malı, Robbins 1940 değil; Wilhelm/Baynes I Ching de telifli). Korpusa
    künyesiz bir dosya eklemek, kaynağı bilinmeyen metni ticari bir ürüne
    sokmak demek. Kayıt: knowledge/SOURCES.md
    """
    dizin = rag_service._corpus_dir(lang)
    dosyalar = sorted(dizin.glob("*.md"))
    assert dosyalar, f"{lang} korpusu boş"

    for md in dosyalar:
        kunye, _ = rag_service._parse_front_matter(
            md.read_text(encoding="utf-8"))
        assert kunye.get("license"), (
            f"{md.name} lisans beyan etmiyor. knowledge/SOURCES.md'ye künyesi "
            f"yazılmalı ve dosya başına 'license:' eklenmeli.")


def test_turkce_korpus_hala_yuklenir():
    parcalar = rag_service._load_chunks("tr")
    assert parcalar
    metin = " ".join(c.text for c in parcalar).lower()
    assert "day master" in metin or "günün efendisi" in metin
