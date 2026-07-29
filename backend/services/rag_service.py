"""RAG (Retrieval-Augmented Generation) bilgi tabanı servisi.

knowledge/corpus altındaki kadim metin dosyaları başlık bazında parçalanır,
Gemini embedding API'siyle (text-embedding-004) vektörlenir ve diske
önbelleklenir. Sorgu anında kosinüs benzerliğiyle en ilgili pasajlar seçilip
LLM prompt'una bağlam olarak eklenir.

API anahtarı yoksa TF benzeri anahtar kelime skorlamasına düşer — servis
hiçbir koşulda hata fırlatmaz, en kötü durumda boş bağlam döner.
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
import re
from collections import OrderedDict
from dataclasses import dataclass, field

from core import config, i18n

logger = logging.getLogger(__name__)

def _embed_cache_file(lang: str):
    """Dil başına ayrı embedding önbelleği.

    Tek dosya kullanılsaydı diller birbirinin önbelleğini geçersiz kılardı:
    korpus sağlaması değişir, her dil değişiminde tüm vektörler yeniden
    üretilirdi.
    """
    return config.CACHE_DIR / f"rag_embeddings_{lang}.json"


@dataclass
class Chunk:
    doc: str
    title: str
    text: str
    embedding: list[float] | None = None
    keywords: set[str] = field(default_factory=set)


def _tokenize(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-zçğıöşü]{3,}", text.lower().replace("ı", "i"))}


def _corpus_dir(lang: str):
    """Dilin korpus dizini; yoksa varsayılan dile düşer.

    Yeni bir dil eklenip korpusu henüz yazılmadığında sistem boş bağlamla
    değil, varsayılan dilin korpusuyla çalışır — yorum kalitesi düşer ama
    özellik çalışmaya devam eder.
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
    # Dil dizinleri hiç yoksa eski düz yapıya düş (geriye dönük uyum).
    return base


def _load_chunks(lang: str) -> list[Chunk]:
    corpus_dir = _corpus_dir(lang)
    chunks: list[Chunk] = []
    if not corpus_dir.exists():
        logger.warning("Korpus dizini bulunamadı: %s", corpus_dir)
        return chunks

    for md_file in sorted(corpus_dir.glob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        # '## Başlık' bölümlerine ayır
        sections = re.split(r"(?m)^##\s+", text)
        doc_title = sections[0].strip().lstrip("# ").splitlines()[0] if sections else md_file.stem
        for section in sections[1:]:
            lines = section.strip().splitlines()
            if not lines:
                continue
            title = lines[0].strip()
            body = "\n".join(lines[1:]).strip()
            if len(body) < 40:
                continue
            chunk_text = f"{doc_title} — {title}\n{body}"
            chunks.append(Chunk(doc=md_file.stem, title=title, text=chunk_text,
                                keywords=_tokenize(chunk_text)))
    return chunks


# Aynı/benzer sorular tekrar geldiğinde embedding API'sine gitmemek için
# küçük bir bellek içi LRU önbelleği (Cloud Run instance ömrü boyunca yaşar).
_QUERY_CACHE_MAX = 128

#: Tek istekte kaç metin vektörleneceği. Korpus büyüdükçe (kitaplar) tek
#: seferde göndermek istek boyutu sınırına takılır.
_EMBED_BATCH_SIZE = 32


def _as_contents(texts: list[str]) -> list[dict]:
    """Metin listesini, her metin AYRI bir Content olacak şekilde paketler.

    Bu, göründüğü kadar önemsiz değil: ``embed_content(contents=[...str])``
    çağrısında SDK düz string listesini TEK bir Content'in birden fazla parçası
    sayar ve **tek bir embedding** döndürür. Sonuç sessiz bir bozulmadır —
    korpusun yalnızca ilk parçası vektörlenir, `search()` de tüm parçalarda
    embedding aramadığı için anahtar kelime örtüşmesine düşer ve hiçbir yerde
    hata görünmez.
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
        self._query_cache: OrderedDict[str, list[float]] = OrderedDict()

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

    def _ensure_loaded(self) -> list[Chunk]:
        if self._chunks is not None:
            return self._chunks

        chunks = _load_chunks(self.lang)
        corpus_hash = hashlib.sha256(
            "".join(c.text for c in chunks).encode("utf-8")
        ).hexdigest()[:16]
        cache_file = _embed_cache_file(self.lang)

        # Diskteki embedding önbelleğini dene
        if cache_file.exists():
            try:
                cached = json.loads(cache_file.read_text(encoding="utf-8"))
                if cached.get("hash") == corpus_hash and len(cached["embeddings"]) == len(chunks):
                    for chunk, emb in zip(chunks, cached["embeddings"]):
                        chunk.embedding = emb
                    self._chunks = chunks
                    return chunks
            except Exception:
                pass

        embeddings = self._embed_texts([c.text for c in chunks]) if chunks else None

        # Önbelleğe YALNIZCA tam sonuç yazılır. Eksik yazılırsa her açılışta
        # uzunluk kontrolü tutmaz, yeniden vektörleme denenir ve arama sessizce
        # anahtar kelime modunda kalır.
        if embeddings and len(embeddings) == len(chunks):
            for chunk, emb in zip(chunks, embeddings):
                chunk.embedding = emb
            try:
                cache_file.write_text(
                    json.dumps({"hash": corpus_hash, "embeddings": embeddings}),
                    encoding="utf-8",
                )
            except Exception as exc:
                logger.warning("Embedding önbelleği yazılamadı: %s", exc)
        elif chunks:
            logger.warning(
                "Korpus vektörlenemedi (%s, %d parça); arama anahtar kelime "
                "moduyla çalışacak. Anlamsal arama devre dışı.",
                self.lang, len(chunks)
            )

        self._chunks = chunks
        return chunks

    def _embed_query(self, query: str) -> list[float] | None:
        """Sorgu vektörünü LRU önbellek üzerinden üretir."""
        key = " ".join(query.lower().split())
        if key in self._query_cache:
            self._query_cache.move_to_end(key)
            return self._query_cache[key]
        embs = self._embed_texts([query])
        emb = embs[0] if embs else None
        if emb:
            self._query_cache[key] = emb
            if len(self._query_cache) > _QUERY_CACHE_MAX:
                self._query_cache.popitem(last=False)
        return emb

    @staticmethod
    def _cosine(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
        return dot / norm if norm else 0.0

    def semantic_ready(self) -> bool:
        """Korpusun tamamı vektörlendi mi?

        Kısmi vektörle kosinüs araması yapılamaz: embedding'i olmayan parçalar
        skorlamaya giremez ve sonuçlar sessizce çarpıtılır. Bu yüzden ya hepsi
        ya hiçbiri.
        """
        chunks = self._ensure_loaded()
        return bool(chunks) and all(c.embedding for c in chunks)

    def search(self, query: str, top_k: int = 3) -> list[dict[str, str]]:
        chunks = self._ensure_loaded()
        if not chunks:
            return []

        scored: list[tuple[float, Chunk]] = []
        query_emb = None
        if self.semantic_ready():
            query_emb = self._embed_query(query)

        if query_emb:
            for chunk in chunks:
                scored.append((self._cosine(query_emb, chunk.embedding), chunk))
        else:
            q_tokens = _tokenize(query)
            for chunk in chunks:
                overlap = len(q_tokens & chunk.keywords)
                scored.append((overlap / (len(q_tokens) + 1), chunk))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            {"doc": c.doc, "title": c.title, "text": c.text, "score": round(s, 3)}
            for s, c in scored[:top_k] if s > 0
        ]


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
