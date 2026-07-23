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
from dataclasses import dataclass, field

from core import config

logger = logging.getLogger(__name__)

_EMBED_CACHE_FILE = config.CACHE_DIR / "rag_embeddings.json"


@dataclass
class Chunk:
    doc: str
    title: str
    text: str
    embedding: list[float] | None = None
    keywords: set[str] = field(default_factory=set)


def _tokenize(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-zçğıöşü]{3,}", text.lower().replace("ı", "i"))}


def _load_chunks() -> list[Chunk]:
    corpus_dir = config.KNOWLEDGE_DIR / "corpus"
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


class _KnowledgeBase:
    def __init__(self):
        self._chunks: list[Chunk] | None = None

    def _embed_texts(self, texts: list[str]) -> list[list[float]] | None:
        if not config.GEMINI_API_KEY:
            return None
        try:
            from google import genai

            client = genai.Client(api_key=config.GEMINI_API_KEY)
            result = client.models.embed_content(
                model=config.EMBEDDING_MODEL, contents=texts
            )
            return [e.values for e in result.embeddings]
        except Exception as exc:
            logger.warning("Embedding üretilemedi: %s", exc)
            return None

    def _ensure_loaded(self) -> list[Chunk]:
        if self._chunks is not None:
            return self._chunks

        chunks = _load_chunks()
        corpus_hash = hashlib.sha256(
            "".join(c.text for c in chunks).encode("utf-8")
        ).hexdigest()[:16]

        # Diskteki embedding önbelleğini dene
        if _EMBED_CACHE_FILE.exists():
            try:
                cached = json.loads(_EMBED_CACHE_FILE.read_text(encoding="utf-8"))
                if cached.get("hash") == corpus_hash and len(cached["embeddings"]) == len(chunks):
                    for chunk, emb in zip(chunks, cached["embeddings"]):
                        chunk.embedding = emb
                    self._chunks = chunks
                    return chunks
            except Exception:
                pass

        embeddings = self._embed_texts([c.text for c in chunks]) if chunks else None
        if embeddings:
            for chunk, emb in zip(chunks, embeddings):
                chunk.embedding = emb
            try:
                _EMBED_CACHE_FILE.write_text(
                    json.dumps({"hash": corpus_hash, "embeddings": embeddings}),
                    encoding="utf-8",
                )
            except Exception:
                pass

        self._chunks = chunks
        return chunks

    @staticmethod
    def _cosine(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
        return dot / norm if norm else 0.0

    def search(self, query: str, top_k: int = 3) -> list[dict[str, str]]:
        chunks = self._ensure_loaded()
        if not chunks:
            return []

        scored: list[tuple[float, Chunk]] = []
        query_emb = None
        if all(c.embedding for c in chunks):
            embs = self._embed_texts([query])
            query_emb = embs[0] if embs else None

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


knowledge_base = _KnowledgeBase()


def retrieve_context(query: str, top_k: int = 3) -> str:
    """Sorguya en uygun kadim metin pasajlarını prompt bağlamı olarak döndürür."""
    results = knowledge_base.search(query, top_k=top_k)
    if not results:
        return ""
    parts = [f"[Kaynak: {r['doc']} / {r['title']}]\n{r['text']}" for r in results]
    return "\n\n---\n\n".join(parts)
