# B06 — Concept Extraction

> **Objective:** Extract math concepts from book chunks, classify them by type/difficulty/importance, and normalize duplicates.

**Depends on:** B02 (models), B03 (chunks), B04 (LLM client), B05 (book profile for context)

---

## Tasks

### 1. Concept extraction prompt — `app/llm/prompts/concept_extraction.md`

```markdown
You are a math concept extraction expert. Given the following text from a {level} {subject} textbook, extract all mathematical concepts.

## Text
{chunk_text}

## Book Context
Subject: {subject}
Level: {level}
Style: {style}

## Instructions
For each concept, provide:
- name: canonical name
- concept_type: one of [definition, theorem, technique, example, proof, application]
- difficulty: 1-5
- importance: one of [core, supporting, optional]
- prerequisite_names: list of concepts this depends on
- common_confusions: list of common mistakes or confusions

Respond ONLY with JSON:
{schema}
```

### 2. Concept extractor — `app/services/concept_extraction/concept_extractor.py`

```python
class ConceptExtractor:
    def __init__(self, llm: BaseLLMClient):
        ...

    async def extract_from_book(self, db: Session, book_id: UUID) -> list[Concept]:
        """
        1. Load book profile (for subject/level context).
        2. Load all chunks.
        3. Batch chunks into groups of 2-3 (by adjacency).
        4. Process batches in parallel using asyncio.gather()
           with a concurrency limit (semaphore, max 5 concurrent calls)
           to avoid rate limits while keeping speed reasonable.
        5. Collect all raw concepts from all batches.
        6. Normalize and deduplicate.
        7. Save to DB.
        """
```

### 3. Concept normalizer — `app/services/concept_extraction/concept_normalizer.py`

```python
class ConceptNormalizer:
    def normalize(self, raw_concepts: list[dict]) -> list[dict]:
        """
        1. Lowercase and strip names.
        2. Merge duplicates by normalized_name.
        3. Keep highest importance and merge source_chunk_ids.
        4. Merge prerequisite_names and common_confusions lists.
        """
```

Normalization strategy (two passes):

**Pass 1 — Deterministic:** Lowercase, strip whitespace, merge exact `normalized_name` matches. Merge `source_chunk_ids`, keep highest `importance`, union `prerequisite_names` and `common_confusions`.

**Pass 2 — LLM-assisted dedup:** Send the remaining concept name list to the LLM and ask: "Which of these are duplicates or near-duplicates?" Merge flagged pairs. This catches `"Span"` vs `"Vector span"` vs `"Span of a set"`.

Both passes run unconditionally (the LLM dedup call is cheap since it's just a name list, not full definitions).

### 4. API endpoint — `app/api/routes/concepts.py`

```python
@router.post("/books/{book_id}/concepts/extract")
async def extract_concepts(book_id: UUID, db = Depends(get_db)):
    ...

@router.get("/books/{book_id}/concepts")
async def list_concepts(book_id: UUID, db = Depends(get_db)):
    ...
```

### 5. CLI script — `scripts/extract_concepts.py`

```bash
python scripts/extract_concepts.py --book-id BOOK_ID
```

Prints concept count and list of concept names.

---

## Files to Create

```text
app/services/concept_extraction/__init__.py
app/services/concept_extraction/concept_extractor.py
app/services/concept_extraction/concept_normalizer.py
app/llm/prompts/concept_extraction.md
app/api/routes/concepts.py
scripts/extract_concepts.py
```

---

## Acceptance Criteria

- [ ] Linear algebra span fixture extracts concepts including: `linear combination`, `span`, `basis`, `linear independence`.
- [ ] Each concept has `concept_type`, `difficulty`, `importance`, `source_chunk_ids`.
- [ ] Duplicate concept names across chunks are merged.
- [ ] `normalized_name` is lowercase and consistent.
- [ ] `GET /books/{book_id}/concepts` returns the concept list.

---

## Agent Prompt

```text
Create concept extraction for MathPath:

1. app/llm/prompts/concept_extraction.md — prompt that takes chunk text + book context, returns list of concepts with name, type, difficulty, importance, prerequisites, confusions.

2. app/services/concept_extraction/concept_extractor.py — batches chunks into groups of 2-3, processes batches in parallel with asyncio.gather (max 5 concurrent), collects raw concepts.

3. app/services/concept_extraction/concept_normalizer.py — two-pass dedup: (a) deterministic merge by lowercase name, (b) LLM-assisted dedup pass on remaining names. Merges metadata.

4. app/api/routes/concepts.py — POST to trigger extraction, GET to list concepts.

5. scripts/extract_concepts.py — CLI script.
```
