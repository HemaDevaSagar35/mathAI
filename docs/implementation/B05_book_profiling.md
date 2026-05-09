# B05 — Book Profiling

> **Objective:** Auto-detect subject, level, style, and learning strategy from uploaded book chunks. Save a structured `BookProfile`.

**Depends on:** B02 (models), B03 (chunks exist), B04 (LLM client)

> ### Update — structure-aware sampling (added with [B14v2](B14v2_vision_ingestion.md))
>
> The original sampling rule (first 5 + middle 3 + last 2 chunks) is still implemented as `BookProfiler._sample_chunks_flat`, but it is now the **fallback**. The active rule is:
>
> - **If `BookSection` rows exist for the book** (i.e. it was ingested via the vision-first path), sample **3 chunks per chapter** (first / middle / last of each chapter), capped at 30 chunks total. This guarantees every chapter is represented in the profile, fixes the multi-subject undersampling failure mode, and scales naturally with book length.
> - **Otherwise** (legacy text ingestion or structure detection produced no chapters), fall back to the original 5-3-2 split unchanged.
>
> Everything else in this spec — prompt template, output schema, API endpoints, CLI script — remains accurate. A future follow-up (tracked in B14v2's "Known limitations") will derive `proof_density` / `computation_density` deterministically from the typed-block distribution rather than asking the LLM, making profiling near-free once concepts are extracted.

---

## Tasks

### 1. Book profiling prompt — `app/llm/prompts/book_profile.md`

```markdown
You are a math education expert. Analyze the following text excerpts from a math textbook and produce a structured profile.

## Text Excerpts
{chunks_text}

## Instructions
Identify the subject, topics, level, style, proof density, computation density, and diagram dependency. Recommend a learning strategy.

## Output Format
Respond ONLY with JSON matching this schema:
{schema}
```

### 2. Profile output schema

```json
{
  "title_guess": "string",
  "detected_subjects": [
    {"subject": "string", "confidence": 0.0}
  ],
  "topics": ["string"],
  "level": "string — high_school | undergraduate | graduate",
  "style": "string — definition_theorem_proof | intuition_examples | computation_drill | mixed",
  "proof_density": "string — none | low | medium | high",
  "computation_density": "string — none | low | medium | high",
  "diagram_dependency": "string — none | low | medium | high",
  "content_structure": {
    "has_definitions": "boolean",
    "has_theorems": "boolean",
    "has_proofs": "boolean",
    "has_worked_examples": "boolean",
    "has_exercises": "boolean"
  },
  "learning_strategy": {
    "proof_ladder_weight": "string — none | low | medium | high",
    "drill_practice_weight": "string — none | low | medium | high",
    "visual_intuition_weight": "string — none | low | medium | high",
    "application_weight": "string — none | low | medium | high"
  }
}
```

### 3. Book profiler service — `app/services/profiling/book_profiler.py`

```python
class BookProfiler:
    def __init__(self, llm: BaseLLMClient | None = None):
        # If no client passed, use task-specific routing
        self.llm = llm or get_llm_client(task="book_profiling")

    async def profile_book(self, db: Session, book_id: UUID) -> BookProfile:
        """
        1. Load sample chunks (first 5 + middle 3 + last 2, or all if ≤10).
        2. Build prompt from template.
        3. Call llm.generate_json() with BookProfileSchema.
        4. Create BookProfile row.
        5. Update book status.
        6. Return profile.
        """
```

Chunk sampling strategy: Use diverse chunks from the beginning, middle, and end to get an accurate picture.

**Token budget awareness:** Sampling 10 chunks at ~800 tokens each = ~8K tokens of source. Plus prompt overhead, expect ~10K input tokens per profiling call. This is cheap across all providers.

**Provider recommendation:** A fast, cheap multimodal/long-context model (e.g. Gemini Flash) is ideal here. Configure via `LLM_BOOK_PROFILING_PROVIDER` + `LLM_BOOK_PROFILING_MODEL` in `.env`, or fall back to `LLM_ALL_*`.

### 4. API endpoint — `app/api/routes/profiles.py`

```python
@router.post("/books/{book_id}/profile")
async def profile_book(book_id: UUID, db: Session = Depends(get_db)):
    ...

@router.get("/books/{book_id}/profile")
async def get_profile(book_id: UUID, db: Session = Depends(get_db)):
    ...
```

### 5. CLI script — `scripts/profile_book.py`

```bash
python scripts/profile_book.py --book-id BOOK_ID
```

Prints the generated profile JSON.

---

## Files to Create

```text
app/services/profiling/__init__.py
app/services/profiling/book_profiler.py
app/llm/prompts/book_profile.md
app/api/routes/profiles.py
scripts/profile_book.py
```

---

## Acceptance Criteria

- [ ] Calculus fixture → detected subject includes `calculus`.
- [ ] Linear algebra fixture → detected subject includes `linear_algebra`.
- [ ] Proof-heavy fixture → `proof_density` is `medium` or `high`.
- [ ] Profile is stored in `book_profiles` with all fields populated.
- [ ] `GET /books/{book_id}/profile` returns the stored profile.
- [ ] Profile JSON matches the schema.

---

## Agent Prompt

```text
Create book profiling for MathPath:

1. app/llm/prompts/book_profile.md — prompt template that takes text excerpts and returns structured profile JSON.
2. app/services/profiling/book_profiler.py — BookProfiler class that samples chunks, calls LLM, validates JSON, and saves BookProfile to DB.
3. app/api/routes/profiles.py — POST /books/{book_id}/profile to trigger profiling, GET /books/{book_id}/profile to retrieve.
4. scripts/profile_book.py — CLI script.

Sample 5 chunks from start + 3 from middle + 2 from end. Profile schema includes: title_guess, detected_subjects, topics, level, style, proof_density, computation_density, diagram_dependency, content_structure, learning_strategy.
```
