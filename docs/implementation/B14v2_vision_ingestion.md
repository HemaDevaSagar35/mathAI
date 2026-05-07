# B14v2 — Vision-First PDF Ingestion

> **Objective:** Replace text-extraction-then-chunk with a single-pass, vision-based per-page extractor that captures structural hierarchy (chapters, sections), typed content blocks (definitions, theorems, proofs, equations, figures, etc.), and figure crops in one LLM call. Produces a structured book ready for downstream profiling, concept extraction, lessons, and quizzes.
>
> **Why this exists:** B14 (the legacy text-only path) loses three things that downstream stages need: (a) chapter/section boundaries, (b) math notation fidelity (PyMuPDF mangles equations), and (c) figures. For a tutoring app whose AI output must stay grounded in the textbook, none of those losses are acceptable. Vision-first ingestion solves all three at once with a frontier multimodal LLM.

**Depends on:** B01 (skeleton), B02 (models), B04 (LLM clients with vision support — added in this milestone).

**Status:** ✅ Implemented and merged. **Opt-in.** Default ingestion path is still B14 (legacy) unless `VISION_INGESTION_ENABLED=true` or the upload request passes `?use_vision=true`.

---

## Architecture

One pass over the PDF. For each page, the multimodal LLM sees the rendered page image (and optionally the PyMuPDF text-layer as a hint) and emits both structural events (chapter/section starts) and a stream of typed content blocks. A post-processor walks the per-page stream, opens/closes section rows on a stack, groups blocks into chunks within sections, and crops figures from the rendered images.

```text
PDF
 ├─ render every page → uploads/{book_id}/pages/p####.png
 ├─ extract text-layer hint per page (may be empty for scans)
 ├─ read PDF outline titles (page numbers ignored — unreliable)
 │
 │   PageExtractor (LLM, batched 5/call, multimodal)
 │   ├─ continuity context: current section path stack
 │   ├─ inputs: images + text hints + TOC titles
 │   └─ output: list[PageExtraction]
 │
 │   StructurePostprocessor
 │   ├─ open/close BookSection rows from structure_events
 │   ├─ group typed blocks into BookChunks within sections
 │   ├─ render markdown into clean_text (backward compat)
 │   └─ crop figure bboxes via callback → BookFigure rows
 │
 └─ book.status = "ingested"
```

### Why vision and not text-extraction-then-LLM?

- **Born-digital, scanned, and OCR'd PDFs** all collapse to one path. No detection branching.
- **Math notation** is rendered. The LLM emits LaTeX from the visual equation; PyMuPDF's text extraction garbles it. OCR of math is famously unreliable.
- **Layout is preserved.** Two-column papers, sidebars, theorem boxes are seen the way a human sees them; reading order is right.
- **Heading detection** falls out of the visual signal — you don't need brittle regex on font sizes.
- **Cost is fine.** ~$0.05–0.15 per book on Gemini 2.0 Flash for a 300-page textbook with figures. The user's API key, the user's call.

---

## Tasks

### 1. Per-page extraction prompt — `app/llm/prompts/page_extract.md`

A single prompt that asks the LLM to:

1. Classify each page (`frontmatter | toc | preface | body | exercises | appendix | references | index | back_matter`).
2. Emit `structure_events` for any chapter/section heading visually present.
3. Emit `blocks` — a typed, ordered stream of the page content.
4. Return a `confidence` and optional `notes`.

Placeholders supplied by `load_prompt`:

- `book_title_hint`, `subject_hint`
- `known_toc_titles` (titles only — page numbers ignored as suspect)
- `n_pages`, `page_numbers`, `raw_text_hints`
- `current_section_path` (continuity from previous batch)

### 2. Pydantic schemas — `app/schemas/page_extraction.py`

The strict contract the LLM must produce:

```python
class PageExtraction(BaseModel):
    page: int
    page_kind: PageKind  # enum, see above
    structure_events: list[StructureEvent]
    blocks: list[Block]                  # typed union over 12 kinds
    confidence: float
    notes: str | None
```

Block union (with kind-specific fields):

| `kind` | required fields |
|---|---|
| `heading` | `level`, `text` |
| `paragraph` | `markdown` |
| `definition` | `markdown`, `label?` |
| `theorem` | `markdown`, `subkind` (`theorem|lemma|corollary|proposition`), `label?` |
| `proof` | `markdown` |
| `example` | `markdown`, `label?` |
| `remark` | `markdown` |
| `equation` | `latex`, `label?` (display equations only; inline math stays in `markdown` of other blocks) |
| `figure` | `bbox: [x, y, w, h]` (image px, top-left origin), `caption?` |
| `table` | `bbox`, `caption?`, `markdown?` (pipe-table when extractable) |
| `list` | `ordered`, `items: [markdown]` |
| `exercise` | `markdown`, `number?` |

Unknown block kinds are **silently dropped** with a warning so a single hallucinated label doesn't fail the whole batch. Helpers `section_path_after()` and `page_kind_is_chunkable()` are exported for the post-processor.

### 3. LLM client image support — `app/llm/clients/{base,gemini,openai,anthropic}_client.py`

Adds an `images: list[bytes] | None = None` parameter to `BaseLLMClient.generate()` and `generate_json()`. Each entry is PNG-encoded bytes. Per-provider wire formats:

- **Gemini:** content list of `{"mime_type": "image/png", "data": bytes}` parts followed by the prompt.
- **OpenAI:** chat-completion `content` array with `image_url` items as `data:image/png;base64,...`.
- **Anthropic:** message `content` array with `{type: "image", source: {type: "base64", media_type: "image/png", data: ...}}` blocks.

All existing call sites pass `images=None` and behave exactly as before.

### 4. Page extractor — `app/services/ingestion/page_extractor.py`

```python
@dataclass
class PageInput:
    page: int
    image: bytes
    text_hint: str | None

class PageExtractor:
    async def extract(self, pages: list[PageInput]) -> list[PageExtraction]:
        # Batch into N-page calls (default 5).
        # Thread `current_section_path` between batches.
        # Validate each batch via PageBatchExtraction.
        # On per-batch failure: emit empty placeholders so the rest of the
        # book still ingests; never abort the whole file.
```

### 5. Models — `app/models/section.py`, `app/models/figure.py`, updates to `app/models/book.py`

```python
class BookSection(Base):  # chapter / section tree, self-FK on parent_id
    id, book_id, parent_id, level, order_index, kind, number, title,
    page_start, page_end, confidence, created_at

class BookFigure(Base):
    id, book_id, section_id?, chunk_id?, page,
    image_url, caption?, bbox_json?, created_at

# BookChunk additions (all nullable, additive migration):
section_id   FK → book_sections.id   ON DELETE SET NULL
blocks       JSONB                    # typed block list
page_kind    str?
confidence   float?
```

Migration: `alembic/versions/a1c7f2b3e4d5_add_book_sections_figures_and_chunk_blocks.py`. Two new tables, four new columns on `book_chunks`. Legacy chunks have `section_id = NULL` and continue to work.

### 6. Structure post-processor — `app/services/ingestion/structure_postprocessor.py`

```python
class StructurePostprocessor:
    def process(
        db, book_id, extractions: list[PageExtraction],
        crop_figure: Callable[[int, list[float]], bytes] | None,
        figures_dir: Path | None,
    ) -> StructureProcessResult:
        # Walk pages in order:
        #  - apply each structure_event to a section stack (push/pop by level)
        #  - skip non-chunkable pages (frontmatter, toc, index, references, back_matter)
        #  - for each chunkable page, group blocks into BookChunks within
        #    the deepest open section, respecting token budget
        #  - render each chunk's blocks to markdown for backward-compat clean_text
        #  - for figure blocks, call crop_figure(bbox), save PNG, write BookFigure
```

Key design choices:

- **Atomic block kinds** (`definition`, `theorem`, `proof`, `example`, `equation`) are kept whole in chunks where possible.
- **`clean_text` is always populated** (markdown-rendered from blocks) so `ConceptExtractor` and friends keep working without changes.
- **Section page ranges** are extended as we walk pages, so a chapter row knows its full page span by the time the next chapter starts.
- **`chapter_title`** on `BookChunk` is denormalized by walking up the section tree, for backward compat with code that reads it.

### 7. Vision PDF ingestor — `app/services/ingestion/vision_pdf_ingestor.py`

```python
class VisionPDFIngestor:
    async def ingest(db, book_id, file_path) -> VisionIngestResult:
        with fitz.open(file_path) as doc:
            page_inputs = render_and_collect(doc, dpi=150)
            toc_titles = extract_toc_titles(doc)         # titles only
            extractions = await page_extractor.extract(page_inputs)
            crop_figure = make_crop_figure(doc, dpi=200, render_dpi=150)
            return postprocessor.process(
                db, book_id, extractions, crop_figure, figures_dir
            )
```

Figure cropping converts the LLM's image-pixel bbox back to PDF point space (`pdf_pt = px * 72 / render_dpi`) and re-renders the clipped region at higher DPI for quality.

### 8. Profiler upgrade — `app/services/profiling/book_profiler.py`

When `BookSection` rows exist, sample **3 chunks per chapter** (first / middle / last), capped at 30 chunks total. When sections are absent (legacy text path or structure detection produced nothing), fall back to the original 5-3-2 sampling. The legacy method is preserved as `_sample_chunks_flat`.

This addresses the limitation called out in the original B05 doc: a fixed 10-chunk sample undersamples a 300-page book and entirely misses topics in multi-subject textbooks.

### 9. Upload endpoint — `app/api/routes/books.py`

```python
@router.post("/books/upload")
async def upload_book_pdf(
    file: UploadFile, title: str | None = None,
    use_vision: bool | None = None,
    db: Session = Depends(get_db),
):
    # Choose path:
    #   1. ?use_vision=true on the request, OR
    #   2. settings.VISION_INGESTION_ENABLED=true,
    # else legacy PDFIngestor.
```

### 10. Configuration — `app/core/config.py`

```python
VISION_INGESTION_ENABLED: bool = False   # default off
VISION_RENDER_DPI: int = 150             # for the structure pass
VISION_FIGURE_DPI: int = 200             # for figure crops
VISION_BATCH_SIZE: int = 5

LLM_TASK_ROUTING: dict = {
    "page_extraction": {"provider": "gemini", "model": "gemini-2.0-flash"},
}
```

### 11. CLI scripts — `scripts/`

- **`scripts/test_page_extract.py`** — render the first N pages of a PDF, run them through `PageExtractor`, print summary, optionally dump full JSON. **No DB writes.** Use for prompt iteration.
- **`scripts/inspect_structure.py --book-id <uuid>`** — print the detected `BookSection` tree, chunk attachment rate, `page_kind` distribution, average per-page confidence, figure count. Use after a real ingest to verify quality.

---

## Files Created / Modified

```text
NEW:
  app/schemas/page_extraction.py
  app/llm/prompts/page_extract.md
  app/services/ingestion/page_extractor.py
  app/services/ingestion/structure_postprocessor.py
  app/services/ingestion/vision_pdf_ingestor.py
  app/models/section.py
  app/models/figure.py
  alembic/versions/a1c7f2b3e4d5_add_book_sections_figures_and_chunk_blocks.py
  scripts/test_page_extract.py
  scripts/inspect_structure.py
  docs/implementation/B14v2_vision_ingestion.md   (this file)

MODIFIED (backward-compatible):
  app/llm/clients/base.py            # images param on generate / generate_json
  app/llm/clients/gemini_client.py   # vision wire format
  app/llm/clients/openai_client.py   # vision wire format
  app/llm/clients/anthropic_client.py # vision wire format
  app/models/book.py                  # 4 new nullable columns on BookChunk
  app/models/__init__.py              # register BookSection + BookFigure
  app/services/profiling/book_profiler.py  # per-chapter sampling
  app/api/routes/books.py             # ?use_vision=true switch
  app/core/config.py                  # VISION_* settings + task routing
  PROGRESS.md
  docs/implementation/B05_book_profiling.md  # status note
  docs/implementation/B14_pdf_ingestion.md   # superseded note
  docs/implementation/README.md              # build order table
```

---

## Acceptance Criteria

- [x] All four LLM clients (`Base`, Gemini, OpenAI, Anthropic) accept `images=`. Existing callers pass `None` and behave unchanged.
- [x] `PageBatchExtraction` parses a realistic LLM response and silently drops unknown block kinds.
- [x] `load_prompt("page_extract", ...)` substitutes all 7 placeholders correctly.
- [x] Functional test against an in-memory SQLite DB: 5 pages → 4 sections, 3 chunks (atomic blocks preserved), 1 cropped figure, 2 unchunkable pages skipped, chapter-title denormalization correct.
- [x] Migration `a1c7f2b3e4d5` is additive only — `book_chunks` legacy rows remain valid (`section_id=NULL`, `blocks=NULL`).
- [x] `BookProfiler` falls back to legacy 5-3-2 sampling when no sections exist.
- [x] `?use_vision=true` opt-in routes upload through `VisionPDFIngestor`; default upload path is unchanged.
- [ ] (Manual) End-to-end ingest of a real 30+ page PDF: structure tree printed by `inspect_structure.py` matches the book's actual TOC.
- [ ] (Manual) Figures are cropped to non-degenerate PNGs and rendered correctly.

---

## Operational notes

- **Cost.** Gemini 2.0 Flash on a 300-page book runs ~$0.05–0.10 inclusive of structure + content + figure detection.
- **Latency.** Sequential batches of 5 pages take ~3–5 s each. A 300-page book ingests in ~3 minutes. Run async; the upload endpoint already awaits the ingestor.
- **Failure isolation.** Per-batch errors emit empty `PageExtraction` placeholders rather than aborting the file. Low-confidence pages (`< 0.5`) are logged and reported in `StructureProcessResult.low_confidence_pages` so they can be re-run with a stronger model.
- **Re-runnable.** Page renders are cached at `uploads/{book_id}/pages/`. To re-ingest with a new prompt or model, the renders don't need to be regenerated.

---

## Known limitations (deliberate, not bugs)

1. **Math fidelity is good but not Mathpix-good.** Frontier multimodal models occasionally drop a subscript or mis-render a complex aligned equation. For an MVP this is acceptable. Mathpix is the upgrade path: keep the schema unchanged, just replace the source of `equation.latex` for low-confidence equation blocks.
2. **Page-extractor batches run sequentially.** Section-path continuity makes naïve concurrency unsafe. Future optimization: pre-classify chapter boundaries cheaply and parallelize within-chapter batches.
3. **`ConceptExtractor` still reads `clean_text`.** Typed-block-aware extraction is a clean follow-up; the markdown rendering of blocks is faithful enough that it costs nothing today.
4. **No two-column reading-order detection beyond what the LLM does.** Two-column papers usually work; rare layouts may need prompt tuning.
5. **Profiling does not yet derive metrics from typed-block stats.** `proof_density` and friends are still LLM-judged. Once chapter detection is verified on real PDFs, deriving these deterministically (`count(theorem) / total`) is a small follow-up.

---

## Migration / rollback

Forward: `alembic upgrade head` runs `a1c7f2b3e4d5`. Two new tables, four new nullable columns. Zero data loss.

Rollback: `alembic downgrade db6f1536ede4` drops the new tables and columns. Any sections/figures/blocks data is lost; legacy chunks remain intact.

To switch a deployment to vision-first ingestion:

```bash
# .env
VISION_INGESTION_ENABLED=true
GEMINI_API_KEY=...                       # vision-default provider
LLM_TASK_ROUTING='{"page_extraction": {"provider": "gemini", "model": "gemini-2.0-flash"}}'
```

Existing books ingested via the legacy text path remain valid. New uploads use the vision pipeline.

---

## Agent prompt (for re-implementing or auditing)

```text
Implement vision-first PDF ingestion for MathPath as a single-pass, per-page,
multimodal LLM extraction that produces both structure (chapter/section
boundaries) and typed content blocks (definition, theorem, proof, example,
remark, equation, figure, table, list, exercise) in one call.

1) Pydantic schemas in app/schemas/page_extraction.py for PageBatchExtraction
   / PageExtraction / StructureEvent / Block (12 kinds). Drop unknown kinds
   silently. Provide section_path_after() and page_kind_is_chunkable() helpers.

2) Prompt template app/llm/prompts/page_extract.md driven by load_prompt()
   placeholders: book_title_hint, subject_hint, known_toc_titles, n_pages,
   page_numbers, raw_text_hints, current_section_path. Inline math in markdown
   as $...$, display math as `equation` blocks. Figures as bbox + caption.
   Page kinds frontmatter / toc / index / references / back_matter emit
   zero blocks.

3) Add `images: list[bytes] | None = None` to BaseLLMClient.generate and
   generate_json. Implement vision for Gemini, OpenAI, Anthropic providers.

4) PageExtractor in app/services/ingestion/page_extractor.py: batches pages,
   threads section path across batches, validates with Pydantic, error-
   isolates per batch.

5) BookSection + BookFigure models with self-FK section tree. BookChunk gains
   section_id (FK), blocks (JSONB), page_kind, confidence — all nullable,
   additive migration.

6) StructurePostprocessor in app/services/ingestion/structure_postprocessor.py:
   walks the per-page stream, opens/closes section stack, groups blocks into
   chunks within sections respecting token budget, renders block markdown into
   clean_text for backward compat, calls crop_figure(page, bbox) to save PNGs
   into uploads/{book_id}/figures/, writes BookFigure rows.

7) VisionPDFIngestor in app/services/ingestion/vision_pdf_ingestor.py:
   render pages with PyMuPDF (cache to uploads/{book_id}/pages/), extract TOC
   titles only, run PageExtractor, run StructurePostprocessor with a figure
   cropper that converts image-pixel bbox back to PDF points.

8) Update BookProfiler to do per-chapter sampling (3 per chapter) when
   BookSection rows exist; fall back to the legacy 5-3-2 sample otherwise.

9) Add ?use_vision=true to POST /api/books/upload, and a
   VISION_INGESTION_ENABLED setting (default false). Add LLM_TASK_ROUTING
   default for "page_extraction" → gemini-2.0-flash.

10) CLI scripts: scripts/test_page_extract.py (no-DB smoke test) and
    scripts/inspect_structure.py (print BookSection tree + chunk stats).
```
