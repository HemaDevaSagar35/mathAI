# B03 — Manual Text Ingestion

> **Objective:** Implement text ingestion: accept raw text, split it into overlapping chunks, compute token counts, and persist chunks to the database.

**Depends on:** B01 (skeleton), B02 (models)

---

## Tasks

### 1. Text ingestor service — `app/services/ingestion/text_ingestor.py`

```python
class TextIngestor:
    def ingest(self, db: Session, book_id: UUID, raw_text: str) -> list[BookChunk]:
        """
        1. Clean text (normalize whitespace, fix encoding).
        2. Call Chunker to split.
        3. Create BookChunk rows.
        4. Return created chunks.
        """
```

### 2. Chunker — `app/services/ingestion/chunker.py`

```python
class Chunker:
    def __init__(self, max_tokens: int = 800, overlap_tokens: int = 100):
        ...

    def chunk(self, text: str) -> list[ChunkResult]:
        """
        Split text into chunks of ~max_tokens with overlap_tokens overlap.
        Return list of ChunkResult(chunk_index, text, token_count).
        """
```

Use `tiktoken` (or a simple whitespace tokenizer for MVP) to count tokens.

Strategy:
- Split on paragraph breaks first.
- Merge short paragraphs until approaching `max_tokens`.
- If a single paragraph exceeds `max_tokens`, split on sentence boundaries.
- Add `overlap_tokens` from the end of the previous chunk to the start of the next.

### 3. Token counter utility

Use `tiktoken` for accurate counting. Since we support multiple LLM providers, default to the `cl100k_base` encoding (shared by GPT-4, Claude, and close enough for Gemini). This doesn't need to be exact — it's for chunking, not billing.

```python
import tiktoken

_encoding = tiktoken.get_encoding("cl100k_base")

def count_tokens(text: str) -> int:
    return len(_encoding.encode(text))
```

### 4. POST endpoint — `app/api/routes/books.py`

```python
@router.post("/books/text")
def create_book_from_text(data: BookCreate, db: Session = Depends(get_db)):
    """
    1. Create Book with source_type='text'.
    2. Run TextIngestor.
    3. Set book.status = 'processed'.
    4. Return book_id and status.
    """
```

### 5. CLI script — `scripts/seed_math_text.py`

```bash
python scripts/seed_math_text.py \
  --title "Span Fixture" \
  --file tests/fixtures/linear_algebra_span_source.txt
```

The script should:
1. Read the file.
2. Call the text ingestor.
3. Print book_id, number of chunks created, and total tokens.

### 6. Test fixtures

Create all 4 golden test fixtures (representative ~2000 words each):

```text
tests/fixtures/linear_algebra_span_source.txt
  → span, linear combinations, basis, linear independence
  → definition-theorem-proof style, medium proof density

tests/fixtures/calculus_limit_source.txt
  → limits, epsilon-delta, continuity, squeeze theorem
  → computation-heavy style, worked examples

tests/fixtures/probability_bayes_source.txt
  → conditional probability, Bayes' theorem, independence
  → mixed style, formula-heavy with applications

tests/fixtures/real_analysis_sequence_source.txt
  → sequences, convergence, Cauchy sequences, completeness
  → proof-heavy style, high proof density
```

These fixtures are used throughout all later milestones for testing.

---

## Files to Create/Modify

```text
app/services/ingestion/__init__.py
app/services/ingestion/text_ingestor.py
app/services/ingestion/chunker.py
app/api/routes/books.py
scripts/seed_math_text.py
tests/fixtures/linear_algebra_span_source.txt
tests/fixtures/calculus_limit_source.txt
tests/fixtures/probability_bayes_source.txt
tests/fixtures/real_analysis_sequence_source.txt
```

Add `tiktoken` to `requirements.txt`.

---

## Acceptance Criteria

- [ ] `scripts/seed_math_text.py` creates a book and chunks from the fixture file.
- [ ] Chunks are stored in `book_chunks` with correct `chunk_index`, `raw_text`, `clean_text`, `token_count`.
- [ ] No chunk exceeds `max_tokens` + small tolerance.
- [ ] Overlap exists between consecutive chunks.
- [ ] `POST /books/text` returns `{"book_id": "...", "status": "processed"}`.

---

## Agent Prompt

```text
Create text ingestion for MathPath:

1. app/services/ingestion/chunker.py — split text into chunks of ~800 tokens with 100-token overlap. Split on paragraphs first, then sentences. Use tiktoken for counting.

2. app/services/ingestion/text_ingestor.py — accept raw text, clean it, chunk it, create BookChunk rows in DB.

3. app/api/routes/books.py — POST /books/text endpoint that creates a Book, runs TextIngestor, returns book_id.

4. scripts/seed_math_text.py — CLI script that reads a .txt file and calls the ingestor.

5. tests/fixtures/linear_algebra_span_source.txt — a ~2000-word fixture about span, linear combinations, basis, and linear independence.
```
