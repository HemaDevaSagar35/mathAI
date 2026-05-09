# B15 — End-to-End Backend Pipeline

> **Objective:** Create a single pipeline script and API endpoint that runs the full chain: ingest → profile → concepts → graph → plan → first lesson → first quiz.

**Depends on:** B03–B14 (all backend services)

---

## Tasks

### 1. Pipeline script — `scripts/run_pipeline.py`

```bash
python scripts/run_pipeline.py \
  --file tests/fixtures/linear_algebra_span_source.txt \
  --title "Linear Algebra - Span"

# Choose a specific LLM provider
python scripts/run_pipeline.py \
  --file tests/fixtures/linear_algebra_span_source.txt \
  --title "Linear Algebra - Span" \
  --provider anthropic \
  --model claude-sonnet-4-20250514
```

Or for PDF:

```bash
python scripts/run_pipeline.py \
  --pdf path/to/chapter.pdf \
  --title "Calculus Chapter 3" \
  --provider gemini
```

The `--provider` and `--model` flags must be passed together (or neither). When passed, they override the per-task / `LLM_ALL_*` settings for the entire run. When omitted, the orchestrator uses whatever each task resolves to from `.env` (per-task `LLM_<TASK>_*` or the `LLM_ALL_*` global).

The script should:

```python
async def run_pipeline(file_path: str, title: str, is_pdf: bool = False):
    # 1. Ingest
    if is_pdf:
        book = ingest_pdf(file_path, title)
    else:
        book = ingest_text(file_path, title)
    print(f"✓ Ingested: {book.id}, {len(chunks)} chunks")

    # 2. Profile
    profile = await profiler.profile_book(db, book.id)
    print(f"✓ Profiled: {profile.detected_subject} ({profile.level})")

    # 3. Extract concepts
    concepts = await extractor.extract_from_book(db, book.id)
    print(f"✓ Extracted: {len(concepts)} concepts")

    # 4. Build graph
    edges = await graph_builder.build_graph(db, book.id)
    print(f"✓ Graph: {len(edges)} edges")

    # 5. Generate plan
    plan = await planner.generate_plan(db, book.id)
    print(f"✓ Plan: {len(plan.tidbits)} tidbits")

    # 6. Generate first lesson
    first_tidbit = plan.tidbits[0]
    lesson = await lesson_gen.generate_lesson(db, first_tidbit.id)
    print(f"✓ First lesson generated")

    # 7. Generate first quiz
    quiz = await quiz_gen.generate_quiz(db, first_tidbit.id)
    print(f"✓ First quiz generated: {len(quiz.questions)} questions")

    # 8. Optionally generate proof ladder for first tidbit
    ladder = await proof_gen.generate(db, first_tidbit.id)
    if ladder:
        print(f"✓ Proof ladder generated")
    else:
        print("- No proof ladder needed for first tidbit")

    # Summary
    print("\n--- Pipeline Complete ---")
    print(f"Book ID:       {book.id}")
    print(f"Subject:       {profile.detected_subject}")
    print(f"Concepts:      {len(concepts)}")
    print(f"Tidbits:       {len(plan.tidbits)}")
    print(f"First tidbit:  {first_tidbit.title}")
```

### 2. API endpoint for pipeline — `app/api/routes/books.py` (extend)

```python
@router.post("/books/{book_id}/process")
async def process_book(
    book_id: UUID,
    data: ProcessRequest,  # { steps: ["profile", "concepts", "graph", "plan"] }
    db = Depends(get_db),
):
    """
    Run requested pipeline steps sequentially.
    For MVP, runs synchronously.
    Returns status.
    """
```

### 3. Pipeline orchestrator service — `app/services/pipeline.py`

```python
class PipelineOrchestrator:
    def __init__(self, profiler, extractor, graph_builder, planner, lesson_gen, quiz_gen, proof_gen):
        ...

    async def run(self, db: Session, book_id: UUID, steps: list[str] | None = None) -> dict:
        """
        Run all steps (or specified steps) in order.
        Return summary dict with counts and IDs.
        """
```

---

## Files to Create

```text
scripts/run_pipeline.py
app/services/pipeline.py
```

---

## Acceptance Criteria

- [ ] One command processes a text fixture from ingestion to first quiz.
- [ ] Output includes: book profile, concept count, edge count, tidbit count, first lesson, first quiz.
- [ ] `POST /books/{book_id}/process` with `steps: ["profile", "concepts", "graph", "plan"]` works.
- [ ] Pipeline can be re-run for individual steps without breaking existing data.
- [ ] Pipeline handles errors gracefully: if concept extraction fails, it reports the failure and stops.
- [ ] `--provider` flag switches the LLM provider for the entire run.
- [ ] Pipeline prints total token usage and estimated cost at the end.
- [ ] Pipeline works with all 3 providers (OpenAI, Anthropic, Gemini).

---

## Agent Prompt

```text
Create end-to-end pipeline for MathPath:

1. scripts/run_pipeline.py — CLI that takes a text file or PDF, runs the full chain: ingest → profile → concepts → graph → plan → first lesson → first quiz → optional proof ladder. Supports --provider and --model flags. Prints progress at each step. Prints total token usage summary at end.

2. app/services/pipeline.py — PipelineOrchestrator class that coordinates all services in order. Accepts optional step list for partial runs and optional provider override.

3. Extend POST /books/{book_id}/process to call PipelineOrchestrator with requested steps. Accept optional provider/model in request body.
```
