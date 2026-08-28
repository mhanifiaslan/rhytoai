# Rytho Astrology RAG Corpus

Bilingual (English + Turkish), chunked, metadata-rich corpus of 7 public-domain
astrology books, ready for embedding/ingestion into the Rytho app's RAG index.

## Contents

- `chunks/<book_id>.jsonl` — one JSON object per line, one file per book.
- `chunks/all_chunks.jsonl` — all 1245 chunks from all 7 books, concatenated.
- `clean/<book_id>.md` — clean English reference text (pre-chunking), with YAML frontmatter.
- `clean/<book_id>_tr.md` — Turkish reference text, reconstructed from translated chunks
  (grouped by heading). Note: consecutive chunks share ~15% tail-overlap by design, so
  a small amount of repeated text appears at chunk boundaries in this file — expected,
  not a bug. The JSONL is the canonical/deduplicated-per-chunk source.
- `manifest.json` — corpus-level build manifest: per-book stats, translation stats, QA summary.
- `stats/tr_merge_report.json` — translation-merge report (per book: chunks, missing count).
- `stats/qa_report.json` — full QA pass output (schema validation, duplicate/empty checks,
  token distribution, OCR confidence, glossary spot-check).

## The 7 books

| id | title | author | year | tradition |
|---|---|---|---|---|
| ptolemy_tetrabiblos | Tetrabiblos (Quadripartite) | Claudius Ptolemy (tr. Ashmand) | 1822 ed. | classical |
| lilly_christian_astrology | Christian Astrology | William Lilly | 1647 | traditional/horary |
| lilly_intro_1852 | An Introduction to Astrology | William Lilly (ed. Zadkiel) | 1852 ed. | traditional/horary |
| sepharial_astrology | Astrology: How to Make and Read Your Own Horoscope | Sepharial | 1920 | modern |
| alanleo_judge_nativity | How to Judge a Nativity | Alan Leo | 1928 | modern/theosophical |
| baughan_influence_stars | The Influence of the Stars | Rosa Baughan | 1904 | modern |
| bonatti_anima_astrologiae | Anima Astrologiae | Bonatti & Cardan (tr. Coley, ed. Serjeant) | 1886 ed. | medieval, Arabic-Latin transmission |

All public domain in the US (see `license`/`source_url` per book in manifest.json).
`bonatti_anima_astrologiae` and `lilly_intro_1852` are the two Islamic/Arabic-Persian-
tradition-adjacent sources added later, via Latin transmitters, since no pre-1930
English translation of a primary Arabic-tradition author (al-Bīrūnī, Abū Maʿshar, etc.)
is both public-domain and available.

## Chunk JSON schema

```
{
  "id": "<source_id>__s<section>__c<chunk>",
  "text": "<English chunk text, ~800 target / 1150 max tokens, 15% tail-overlap>",
  "text_tr": "<Turkish translation of the same chunk>",
  "embedding_text": "<TR header + breadcrumb + TR keywords>\n\n<English text>  — embed this for EN queries",
  "embedding_text_tr": "<TR header + breadcrumb + TR keywords>\n\n<Turkish text>  — embed this for TR queries",
  "metadata": {
    "source", "source_id", "source_tr", "author", "translator", "year",
    "school", "school_tr", "era", "era_tr", "tradition", "authority_weight",
    "language", "license", "source_url",
    "section_path", "heading", "breadcrumb",
    "topic", "topic_en", "topic_tr",
    "entity_planet", "entity_sign", "entity_house", "entity_aspect", "entity_dignity", "entity_tr",
    "tr_keywords",
    "content_type", "ocr_quality",
    "section_index", "chunk_index", "n_chunks_in_section",
    "token_estimate", "char_count", "word_count",
    "has_overlap_prefix", "content_sha1", "ocr_confidence",
    "prev_id", "next_id"
  }
}
```

Recommended: embed `embedding_text` and `embedding_text_tr` as two separate vectors per
chunk (or concatenate both into one multilingual embedding, depending on the embedding
model) so both English- and Turkish-phrased user queries retrieve the same underlying
chunk. Use `metadata.authority_weight` (3-5) to break ties between sources when they
disagree — traditional/classical sources (Lilly, Ptolemy, Bonatti) are weighted highest
for horary/traditional technique questions.

## Known limitations (see manifest.json → qa for full detail)

- 42/1245 chunks (3.4%) run slightly over the 1150-token ceiling (max 1562) — an artifact
  of the calibrated token estimator (tiktoken's remote BPE file was unreachable in the
  build sandbox) vs. the true tokenizer of whichever embedding model is used downstream.
  Not re-chunked, to avoid invalidating the chunk-id ↔ translation mapping; re-embed with
  a model that has headroom (or split downstream) if this matters for your index.
- `lilly_christian_astrology` has the lowest mean OCR confidence (0.908) of the 7 books —
  it's the hardest source (1647 long-s black-letter-adjacent scan) and went through the
  heaviest correction pipeline; a small residual error rate is expected there.
- Turkish translation is machine-translated (agent-based, glossary-anchored for
  consistent astrological terminology) and QA'd for completeness (length-ratio check
  against English, glossary spot-check), not human-proofread line by line.
