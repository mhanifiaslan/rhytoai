"""RAG (Retrieval-Augmented Generation) bilgi tabanı servisi.

`knowledge/corpus/{dil}` altındaki metinler parçalanır, Gemini embedding
API'siyle vektörlenir ve kosinüs benzerliğiyle aranır. Bulunan pasajlar LLM
prompt'una bağlam olarak eklenir.

API anahtarı ya da vektör yoksa TF benzeri anahtar kelime skorlamasına düşer —
servis hiçbir koşulda hata fırlatmaz, en kötü durumda boş bağlam döner.

## Bu katman 12 parça için yazılmıştı, kitap için yeniden kuruldu

Korpus dil başına ~9 KB ve 12-13 parçayken aşağıdaki dördü de görünmüyordu.
Gerçek bir kamu malı klasik (~900 parça) eklendiğinde dördü birden kırılıyor:

1. **Parçalama.** Bölme yalnızca ``##`` başlıklarındandı. Bir kitap bölümü tek
   parçada binlerce kelime olur; embedding o parçanın ORTALAMASINI alır ve
   arama körelir. Artık boyut sınırlı, cümle sınırında, örtüşmeli.
2. **Embedding önbelleği.** Anahtar TÜM korpusun sağlamasıydı: tek dosyaya tek
   satır eklemek 900 parçanın tamamını yeniden vektörletirdi. Artık her parça
   kendi metninin sağlamasıyla anahtarlanıyor — değişmeyen parça yeniden
   vektörlenmez.
3. **Çalışma zamanında vektörleme.** Önbellek `config.CACHE_DIR`'daydı ve o
   Cloud Run'da GEÇİCİ disk. 900 parçada her soğuk başlatma 900 embedding
   çağrısı demekti: gecikme, fatura, ve ilk isteklerde aramanın sessizce
   anahtar kelime moduna düşmesi. Vektörler artık derleme zamanında üretilip
   `knowledge/embeddings/{dil}.json` olarak imaja gömülüyor
   (`scripts/build_embeddings.py`).
4. **Arama.** Kosinüs saf Python'du ve her sorguda tüm parçalar üzerinde
   dönüyordu: 900 parça × 3.072 boyut ≈ 2,8 milyon çarpma, sohbet başına
   saniyeler. Artık normalize edilmiş tek bir numpy matrisi ve tek `matmul`.

Bir de gözlemlenebilirlik: anlamsal aramanın anahtar kelimeye düşmesi bir kez
haftalarca fark edilmedi. `diagnostics()` artık kapsama oranını da veriyor ve
eksik kapsama ERROR olarak loglanıyor.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from core import config, i18n

logger = logging.getLogger(__name__)

#: Parça üst sınırı. Embedding tek bir vektöre indirgediği için uzun metin
#: ayrıntıyı ortalamada eritir; kısa parça ise bağlamı kaybeder.
MAX_CHUNK_CHARS = 1100
#: Bundan kısa gövdeler parça sayılmaz (başlık artığı, boş bölüm).
MIN_CHUNK_CHARS = 40
#: Ardışık parçalar arasındaki örtüşme. Bir cümlenin tam ortasından bölünmesi
#: anlamı öldürür; örtüşme sınırdaki cümlenin iki parçada da bulunmasını sağlar.
CHUNK_OVERLAP_CHARS = 120

#: Tek istekte kaç metin vektörlenecek.
_EMBED_BATCH_SIZE = 32

#: Sorgu vektörü LRU'su (instance ömrü boyunca).
_QUERY_CACHE_MAX = 128

#: Bölüm çeşitliliği için aday havuzu top_k'nın kaç katı olsun.
_DIVERSITY_POOL = 4


def embedding_files(lang: str) -> tuple[Path, Path]:
    """Dilin vektör artefaktı — derleme zamanında üretilir, imaja gömülür.

    İki dosya, ve bu bilinçli: vektörler JSON'a yazılsaydı 900 parça × 3.072
    boyut ≈ **55 MB** metin ederdi (her float ~20 karakter). Aynı veri
    float32 ``.npy`` olarak ~11 MB. Depo ve imaj boyutu arasındaki fark
    beş kat.

    - ``{dil}.json``: model adı, boyut ve parça kimlikleri (sıra = matris satırı)
    - ``{dil}.npy``:  (n, dim) float32 matris

    Dil başına ayrı: tek dosya olsaydı bir dilin korpusu değiştiğinde
    diğerinin vektörleri de boşa düşerdi.
    """
    base = config.KNOWLEDGE_DIR / "embeddings"
    return base / f"{lang}.json", base / f"{lang}.npy"


def read_artifact(lang: str) -> dict[str, np.ndarray]:
    """Artefaktı ``chunk_id -> vektör`` sözlüğü olarak okur.

    Değerler matrisin satırlarına bakan **görünümlerdir**; kopya çıkarılmaz,
    900 parçada bu 11 MB'lık bir farktır.
    """
    meta_path, vec_path = embedding_files(lang)
    if not (meta_path.exists() and vec_path.exists()):
        return {}
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        matris = np.load(vec_path)
    except Exception as exc:
        logger.warning("Vektör artefaktı okunamadı (%s): %s", lang, exc)
        return {}

    if meta.get("model") != config.EMBEDDING_MODEL:
        # Model değiştiyse eski vektörler karşılaştırılabilir değil: aynı
        # uzayda olmayan iki vektörün kosinüsü anlamsızdır.
        logger.warning(
            "Vektör artefaktı '%s' modeliyle üretilmiş, şu an '%s' "
            "kullanılıyor; artefakt yok sayılıyor.",
            meta.get("model"), config.EMBEDDING_MODEL)
        return {}

    ids = meta.get("ids") or []
    if len(ids) != len(matris):
        logger.error("Vektör artefaktı bozuk (%s): %d kimlik, %d satır.",
                     lang, len(ids), len(matris))
        return {}
    return {kimlik: matris[i] for i, kimlik in enumerate(ids)}


def write_artifact(lang: str, vektorler: dict[str, np.ndarray]) -> None:
    """Artefaktı diske yazar (derleme betiği ve yerel geliştirme için)."""
    meta_path, vec_path = embedding_files(lang)
    ids = list(vektorler)
    matris = (np.asarray([vektorler[k] for k in ids], dtype=np.float32)
              if ids else np.zeros((0, 0), dtype=np.float32))
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(vec_path, matris)
    meta_path.write_text(json.dumps({
        "model": config.EMBEDDING_MODEL,
        "dim": int(matris.shape[1]) if ids else 0,
        "count": len(ids),
        "ids": ids,
    }), encoding="utf-8")


@dataclass
class Chunk:
    doc: str
    title: str
    text: str
    embedding: list[float] | None = None
    keywords: set[str] = field(default_factory=set)
    #: Kaynak künyesi (kitap, yazar, çevirmen, lisans). Atıf ve lisans
    #: savunması bunsuz mümkün değil; ticari bir üründe gerekli.
    source: dict[str, str] = field(default_factory=dict)
    #: Metnin sağlaması. Vektör önbelleği buna göre anahtarlanır: metin
    #: değişmedikçe vektör yeniden üretilmez, parça yer değiştirse bile.
    chunk_id: str = ""


def _chunk_id(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]


def _tokenize(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-zçğıöşü]{3,}",
                                  text.lower().replace("ı", "i"))}


# --------------------------------------------------------------------------
# Korpus yükleme ve parçalama
# --------------------------------------------------------------------------

def _corpus_dir(lang: str) -> Path:
    """Dilin korpus dizini; yoksa varsayılan dile düşer.

    Yeni bir dil eklenip korpusu henüz yazılmadığında sistem boş bağlamla
    değil, varsayılan dilin korpusuyla çalışır — kalite düşer ama özellik
    çalışmaya devam eder.
    """
    base = config.KNOWLEDGE_DIR / "corpus"
    hedef = base / lang
    if hedef.is_dir():
        return hedef
    yedek = base / i18n.DEFAULT
    if yedek.is_dir():
        logger.warning("'%s' korpusu yok; '%s' korpusuna düşülüyor.",
                       lang, i18n.DEFAULT)
        return yedek
    return base


_FRONT_MATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    """Dosya başındaki ``---`` bloğunu künye olarak okur.

    Basit ``anahtar: değer`` biçimi; YAML bağımlılığı eklemeye değmez.
    Künye kitap dosyaları için zorunlu (lisans kaydı), kendi yazdığımız
    sentez dosyaları için isteğe bağlı.
    """
    m = _FRONT_MATTER.match(text)
    if not m:
        return {}, text
    kunye: dict[str, str] = {}
    for satir in m.group(1).splitlines():
        if ":" not in satir:
            continue
        anahtar, _, deger = satir.partition(":")
        anahtar, deger = anahtar.strip(), deger.strip()
        if anahtar and deger:
            kunye[anahtar] = deger
    return kunye, text[m.end():]


#: Cümle sonu. Kısaltmalar (Md., vb.) yanlış bölmeye yol açabilir ama
#: sonuç yalnızca parça sınırını kaydırır — anlam kaybı yaratmaz.
_SENTENCE_END = re.compile(r"(?<=[.!?…])\s+")


def _sentences(text: str) -> list[str]:
    return [c for c in _SENTENCE_END.split(text.strip()) if c]


def _hard_wrap(cumle: str) -> list[str]:
    """Tek başına üst sınırı aşan cümleyi kelime sınırında böler.

    Nadir ama gerçek: kaynak metinlerde noktalama olmadan uzayan pasajlar var.
    Bölünmezse tek bir dev parça bütün aramayı çarpıtır.
    """
    parcalar, kalan = [], cumle
    while len(kalan) > MAX_CHUNK_CHARS:
        kesme = kalan.rfind(" ", 0, MAX_CHUNK_CHARS)
        if kesme <= 0:
            kesme = MAX_CHUNK_CHARS
        parcalar.append(kalan[:kesme].strip())
        kalan = kalan[kesme:].strip()
    if kalan:
        parcalar.append(kalan)
    return parcalar


def _split_body(body: str) -> list[str]:
    """Gövdeyi boyut sınırlı, örtüşmeli parçalara böler."""
    if len(body) <= MAX_CHUNK_CHARS:
        return [body]

    parcalar: list[str] = []
    tampon: list[str] = []
    uzunluk = 0

    def bosalt() -> None:
        nonlocal tampon, uzunluk
        if tampon:
            parcalar.append(" ".join(tampon).strip())
        tampon, uzunluk = [], 0

    for cumle in _sentences(body):
        for parca in (_hard_wrap(cumle) if len(cumle) > MAX_CHUNK_CHARS
                      else [cumle]):
            if uzunluk + len(parca) + 1 > MAX_CHUNK_CHARS and tampon:
                bosalt()
                # Örtüşme: önceki parçanın kuyruğu yeni parçanın başına gelir.
                kuyruk = parcalar[-1][-CHUNK_OVERLAP_CHARS:]
                bosluk = kuyruk.find(" ")
                if bosluk > 0:
                    kuyruk = kuyruk[bosluk + 1:]
                # Kuyruk da bütçeye dahildir. Noktalamasız uzun bir pasaj
                # sert bölündüğünde parçanın kendisi zaten üst sınıra yakın
                # olur; kuyruğu eklemek sınırı aşardı. O durumda örtüşmeden
                # vazgeçilir — sınırı korumak örtüşmeden önce gelir.
                if kuyruk and len(kuyruk) + len(parca) + 1 <= MAX_CHUNK_CHARS:
                    tampon.append(kuyruk)
                    uzunluk = len(kuyruk)
            tampon.append(parca)
            uzunluk += len(parca) + 1

    bosalt()
    return [p for p in parcalar if p]


def _load_chunks(lang: str) -> list[Chunk]:
    corpus_dir = _corpus_dir(lang)
    chunks: list[Chunk] = []
    if not corpus_dir.exists():
        logger.warning("Korpus dizini bulunamadı: %s", corpus_dir)
        return chunks

    for md_file in sorted(corpus_dir.glob("*.md")):
        ham = md_file.read_text(encoding="utf-8")
        kunye, govde = _parse_front_matter(ham)

        sections = re.split(r"(?m)^##\s+", govde)
        doc_title = md_file.stem
        if sections and sections[0].strip():
            ilk = sections[0].strip().lstrip("# ").splitlines()
            if ilk:
                doc_title = ilk[0]
        # Künyedeki kitap adı dosya başlığından önce gelir: aynı kitabın
        # bölümleri ayrı dosyalara bölündüğünde başlık tutarlı kalır.
        kitap = kunye.get("book") or doc_title

        for section in sections[1:]:
            lines = section.strip().splitlines()
            if not lines:
                continue
            title = lines[0].strip()
            body = "\n".join(lines[1:]).strip()
            if len(body) < MIN_CHUNK_CHARS:
                continue

            parcalar = _split_body(body)
            for i, parca in enumerate(parcalar):
                # Başlık her parçaya iliştirilir: parça tek başına
                # vektörlendiği için hangi bölümden geldiğini kendi
                # içinde taşımalı, yoksa bağlamsız bir metin gömülür.
                etiket = f"{kitap} — {title}"
                if len(parcalar) > 1:
                    etiket += f" ({i + 1}/{len(parcalar)})"
                metin = f"{etiket}\n{parca}"
                chunks.append(Chunk(
                    doc=md_file.stem, title=title, text=metin,
                    keywords=_tokenize(metin), source=kunye,
                    chunk_id=_chunk_id(metin),
                ))
    return chunks


# --------------------------------------------------------------------------
# Bilgi tabanı
# --------------------------------------------------------------------------

def _as_contents(texts: list[str]) -> list[dict]:
    """Metin listesini, her metin AYRI bir Content olacak şekilde paketler.

    Bu, göründüğü kadar önemsiz değil: ``embed_content(contents=[...str])``
    çağrısında SDK düz string listesini TEK bir Content'in birden fazla parçası
    sayar ve **tek bir embedding** döndürür. Sonuç sessiz bir bozulmadır —
    korpusun yalnızca ilk parçası vektörlenir, arama da anahtar kelime
    örtüşmesine düşer ve hiçbir yerde hata görünmez.
    """
    return [{"parts": [{"text": text}]} for text in texts]


class _KnowledgeBase:
    """Tek bir dilin bilgi tabanı.

    Diller ayrı örneklerde tutulur: korpus, vektörler ve sorgu önbelleği dile
    özgüdür. Tek örnekte karıştırılsaydı İngilizce bir sorgu Türkçe pasajlarla
    skorlanır ve yorum kalitesi düşerdi.
    """

    def __init__(self, lang: str = i18n.DEFAULT):
        self.lang = lang
        self._chunks: list[Chunk] | None = None
        #: (n, dim) float32, satırları L2-normalize. Kosinüs = tek matmul.
        self._matrix: np.ndarray | None = None
        self._query_cache: OrderedDict[str, np.ndarray] = OrderedDict()

    # -- embedding ---------------------------------------------------------

    def _embed_texts(self, texts: list[str]) -> list[list[float]] | None:
        """Metinleri vektörler; hepsi başarılı olmazsa ``None`` döner.

        Kısmi sonuç DÖNDÜRÜLMEZ: eksik vektörle devam etmek, aramanın sessizce
        anahtar kelime moduna düşmesi anlamına gelir ve bu dışarıdan görünmez.
        """
        if not config.GEMINI_API_KEY or not texts:
            return None
        try:
            from google import genai

            client = genai.Client(api_key=config.GEMINI_API_KEY)
            vectors: list[list[float]] = []
            for start in range(0, len(texts), _EMBED_BATCH_SIZE):
                batch = texts[start:start + _EMBED_BATCH_SIZE]
                result = client.models.embed_content(
                    model=config.EMBEDDING_MODEL, contents=_as_contents(batch)
                )
                vectors.extend(e.values for e in result.embeddings)

            if len(vectors) != len(texts):
                logger.error(
                    "Embedding sayısı uyuşmuyor: %d metin istendi, %d vektör "
                    "döndü. Arama anahtar kelime moduna düşecek.",
                    len(texts), len(vectors),
                )
                return None
            return vectors
        except Exception as exc:
            logger.warning("Embedding üretilemedi: %s", exc)
            return None

    # -- yükleme -----------------------------------------------------------

    def _ensure_loaded(self) -> list[Chunk]:
        if self._chunks is not None:
            return self._chunks

        chunks = _load_chunks(self.lang)
        self._chunks = chunks
        if not chunks:
            return chunks

        vektorler = read_artifact(self.lang)
        eksik = [c for c in chunks if c.chunk_id not in vektorler]

        if eksik:
            # Bu satırın ÜRETİMDE görünmesi bir kusurdur: artefakt korpusla
            # uyumsuz demektir ve her soğuk başlatma embedding faturası
            # çıkarır. Derleme betiği çalıştırılmamış olabilir.
            logger.error(
                "Vektör artefaktı korpusla uyumsuz (%s): %d/%d parça eksik. "
                "scripts/build_embeddings.py çalıştırılmalı.",
                self.lang, len(eksik), len(chunks))
            yeni = self._embed_texts([c.text for c in eksik])
            if yeni:
                for chunk, emb in zip(eksik, yeni):
                    vektorler[chunk.chunk_id] = np.asarray(emb,
                                                           dtype=np.float32)
                try:
                    write_artifact(self.lang, vektorler)
                except Exception as exc:
                    logger.warning("Vektör artefaktı yazılamadı: %s", exc)

        self._build_matrix(chunks, vektorler)
        return chunks

    def _build_matrix(self, chunks: list[Chunk],
                      vektorler: dict[str, np.ndarray]) -> None:
        """Vektörleri korpus sırasında tek bir normalize matrise toplar.

        Parça başına Python listesi TUTULMAZ: 900 parça × 3.072 boyut liste
        olarak ~80 MB, float32 matris olarak ~11 MB eder. İkisini birden
        tutmanın anlamı yok, bu yüzden `Chunk.embedding` doldurulmuyor.
        """
        if any(c.chunk_id not in vektorler for c in chunks):
            self._matrix = None
            return
        try:
            matris = np.asarray([vektorler[c.chunk_id] for c in chunks],
                                dtype=np.float32)
        except ValueError:
            # Farklı boyutlu vektörler (model değişimi artığı) — kosinüs
            # hesaplanamaz, anahtar kelime moduna düşülür.
            logger.error("Vektör boyutları tutarsız (%s); anahtar kelime "
                         "moduna düşülüyor.", self.lang)
            self._matrix = None
            return
        if matris.ndim != 2 or matris.shape[1] == 0:
            self._matrix = None
            return
        normlar = np.linalg.norm(matris, axis=1, keepdims=True)
        normlar[normlar == 0] = 1.0
        self._matrix = matris / normlar

    def _embed_query(self, query: str) -> np.ndarray | None:
        """Sorgu vektörünü LRU önbellek üzerinden üretir (normalize)."""
        key = " ".join(query.lower().split())
        if key in self._query_cache:
            self._query_cache.move_to_end(key)
            return self._query_cache[key]
        embs = self._embed_texts([query])
        if not embs:
            return None
        vec = np.asarray(embs[0], dtype=np.float32)
        norm = float(np.linalg.norm(vec))
        if norm == 0:
            return None
        vec = vec / norm
        self._query_cache[key] = vec
        if len(self._query_cache) > _QUERY_CACHE_MAX:
            self._query_cache.popitem(last=False)
        return vec

    # -- arama -------------------------------------------------------------

    def semantic_ready(self) -> bool:
        """Korpusun tamamı vektörlendi mi?

        Kısmi vektörle kosinüs araması yapılamaz: embedding'i olmayan parçalar
        skorlamaya giremez ve sonuçlar sessizce çarpıtılır. Ya hepsi ya hiçbiri.
        """
        chunks = self._ensure_loaded()
        return bool(chunks) and self._matrix is not None \
            and len(self._matrix) == len(chunks)

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        chunks = self._ensure_loaded()
        if not chunks:
            return []

        skorlar = None
        if self.semantic_ready():
            q = self._embed_query(query)
            if q is not None and len(q) == self._matrix.shape[1]:
                skorlar = self._matrix @ q

        if skorlar is None:
            q_tokens = _tokenize(query)
            bolen = len(q_tokens) + 1
            skorlar = np.asarray(
                [len(q_tokens & c.keywords) / bolen for c in chunks],
                dtype=np.float32)

        # Tam sıralama gereksiz: argpartition O(n). Aday havuzu top_k'dan
        # geniş tutulur çünkü aşağıda bölüm çeşitliliği uygulanıyor.
        havuz = min(max(top_k * _DIVERSITY_POOL, top_k), len(chunks))
        aday = np.argpartition(-skorlar, havuz - 1)[:havuz]
        aday = aday[np.argsort(-skorlar[aday])]
        aday = [i for i in aday if float(skorlar[i]) > 0]

        # Bölüm çeşitliliği: kitap korpusu geldiğinde ilk iki sonucun ikisi de
        # AYNI bölümden çıkıyordu (uzun bölümler çok parçaya bölündüğü için
        # komşu parçalar benzer skor alıyor). Prompt bütçesi 2 pasaj; ikisini
        # de aynı bölüme harcamak bağlamın yarısını çöpe atmak demek.
        secilen: list[int] = []
        gorulen: set[tuple[str, str]] = set()
        for i in aday:
            anahtar = (chunks[i].doc, chunks[i].title)
            if anahtar not in gorulen:
                gorulen.add(anahtar)
                secilen.append(i)
            if len(secilen) == top_k:
                break
        # Yeterli farklı bölüm yoksa kalan yerler en yüksek skorlularla dolar.
        if len(secilen) < top_k:
            for i in aday:
                if i not in secilen:
                    secilen.append(i)
                if len(secilen) == top_k:
                    break

        return [{"doc": chunks[i].doc, "title": chunks[i].title,
                 "text": chunks[i].text, "score": round(float(skorlar[i]), 3),
                 "source": chunks[i].source}
                for i in secilen]

    def diagnostics(self) -> dict:
        chunks = self._ensure_loaded()
        return {
            "lang": self.lang,
            "mode": "vector" if self.semantic_ready() else "keyword",
            "chunks": len(chunks),
            "vectors": 0 if self._matrix is None else int(len(self._matrix)),
            "dim": 0 if self._matrix is None else int(self._matrix.shape[1]),
            "model": config.EMBEDDING_MODEL,
            "artifact": all(p.exists() for p in embedding_files(self.lang)),
        }


#: Dil -> bilgi tabanı. Tembel kurulur; her dilin korpusu ilk istekte yüklenir.
_bases: dict[str, _KnowledgeBase] = {}

#: Varsayılan dilin tabanı. Dil parametresi geçmeyen çağrılar ve testler bunu
#: kullanır.
knowledge_base = _KnowledgeBase(i18n.DEFAULT)
_bases[i18n.DEFAULT] = knowledge_base


def base_for(lang: str | None) -> _KnowledgeBase:
    """Dilin bilgi tabanını döndürür (tembel kurulum)."""
    lang = lang if lang in i18n.SUPPORTED else i18n.DEFAULT
    if lang not in _bases:
        _bases[lang] = _KnowledgeBase(lang)
    return _bases[lang]


def search_mode(lang: str | None = None) -> str:
    """Aramanın hangi modda çalıştığı — teşhis için.

    Bu bilginin dışa açık olması önemli: anlamsal aramanın anahtar kelimeye
    düşmesi daha önce hiçbir yerde görünmüyordu ve haftalarca fark edilmedi.
    """
    return "vector" if base_for(lang).semantic_ready() else "keyword"


def diagnostics() -> dict:
    """Desteklenen her dil için bilgi tabanı durumu."""
    return {kod: base_for(kod).diagnostics() for kod in i18n.SUPPORTED}


def retrieve_context(query: str, top_k: int = 3, lang: str | None = None) -> str:
    """Sorguya en uygun kadim metin pasajlarını prompt bağlamı olarak döndürür."""
    results = base_for(lang).search(query, top_k=top_k)
    if not results:
        return ""
    parts = [f"[Kaynak: {r['doc']} / {r['title']}]\n{r['text']}" for r in results]
    return "\n\n---\n\n".join(parts)


def retrieve_passages(query: str, top_k: int = 2,
                      lang: str | None = None) -> list[dict]:
    """Sohbet için ham pasaj listesi (prompt_composer kırpar ve harmanlar)."""
    return base_for(lang).search(query, top_k=top_k)
