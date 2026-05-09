# B14 — PDF Ingestion (legacy text-extraction path)

> **Objective:** Accept PDF file uploads, extract text page-by-page, chunk extracted text with page references, and persist to the database.

**Depends on:** B01 (skeleton), B02 (models), B03 (chunker)

> ### 🗑️ Status: REMOVED — replaced wholesale by [B14v2 — Vision-First PDF Ingestion](B14v2_vision_ingestion.md)
>
> The legacy text-extraction PDF path has been **deleted** from the codebase. `PDFIngestor`, `PDFExtractor`, `PDFChunker`, the `pdfplumber` dependency, and the `?use_vision=true` toggle are all gone. `POST /api/books/upload` now unconditionally runs the multimodal vision pipeline.
>
> Reasons for removal:
>
> - It loses chapter / section structure (chunks were flat).
> - It mangles math notation (PyMuPDF's text extraction was not built for equations).
> - It cannot handle scanned or image-based PDFs.
> - It produces no figure references.
>
> This doc remains as a historical record of the milestone.
> For any production use against real-world textbooks, prefer the vision-first path. Switch by setting `VISION_INGESTION_ENABLED=true` in `.env` or by passing `?use_vision=true` to `POST /api/books/upload`. See [B14v2](B14v2_vision_ingestion.md) for the full design.
>
> The legacy path described below remains in the codebase as a backwards-compat fallback and as a zero-LLM-cost option for users without a configured vision-capable provider.

---

## Tasks

### 1. PDF extractor — `app/services/ingestion/pdf_extractor.py`

```python
class PDFExtractor:
    def extract(self, file_path: str) -> list[PageText]:
        """
        1. Open PDF with PyMuPDF (fitz).
        2. Extract text per page.
        3. Fall back to pdfplumber if PyMuPDF yields poor results.
        4. Return list of PageText(page_number, text).
        """
```

Strategy:
- Use PyMuPDF for fast text extraction.
- If a page returns <50 chars but appears to have content, try pdfplumber for that page.
- Strip headers/footers heuristically (repeated text on multiple pages).

### 2. PDF chunker with page tracking

Extend the existing `Chunker` to accept page-annotated text:

```python
class PDFChunker:
    def chunk_with_pages(self, pages: list[PageText], max_tokens=800, overlap_tokens=100) -> list[PDFChunkResult]:
        """
        Chunk across pages, tracking page_start and page_end for each chunk.
        """
```

Each `PDFChunkResult` includes `chunk_index`, `text`, `token_count`, `page_start`, `page_end`.

### 3. Upload endpoint — `app/api/routes/books.py` (extend)

```python
@router.post("/books/upload")
async def upload_book_pdf(
    file: UploadFile = File(...),
    title: str = Form(None),
    db: Session = Depends(get_db),
):
    """
    1. Save uploaded file to local storage (./uploads/{book_id}.pdf).
    2. Create Book row with source_type='pdf', status='uploaded'.
    3. Return book_id.
    """
```

### 4. PDF processing integration

Extend the `/books/{book_id}/process` endpoint (or create a dedicated one):

```python
async def process_pdf_book(db: Session, book_id: UUID):
    """
    1. Load book, get file_url.
    2. Extract text with PDFExtractor.
    3. Chunk with PDFChunker.
    4. Save BookChunk rows with page_start, page_end.
    5. Update book status to 'processed'.
    """
```

### 5. CLI script — `scripts/ingest_pdf.py`

```bash
python scripts/ingest_pdf.py --file path/to/chapter.pdf --title "Calculus Chapter 3"
```

### 6. File storage utility

```python
UPLOAD_DIR = Path("uploads")

def save_upload(file: UploadFile, book_id: UUID) -> str:
    path = UPLOAD_DIR / f"{book_id}.pdf"
    path.write_bytes(file.file.read())
    return str(path)
```

For MVP, store locally. S3 support can come later.

---

## Files to Create/Modify

```text
app/services/ingestion/pdf_extractor.py
app/services/ingestion/pdf_chunker.py   (or extend chunker.py)
app/api/routes/books.py                 (extend with /books/upload)
scripts/ingest_pdf.py
```

Add to `requirements.txt`:

```text
PyMuPDF>=1.24
pdfplumber>=0.11
python-multipart>=0.0.9
```

---

## Acceptance Criteria

- [ ] A small PDF chapter can be uploaded via `POST /books/upload`.
- [ ] PDF text is extracted page-by-page.
- [ ] Chunks are saved with correct `page_start` and `page_end`.
- [ ] Book status transitions: `uploaded` → `processed`.
- [ ] `scripts/ingest_pdf.py` works end-to-end.
- [ ] Chunks from PDF have similar quality to manually ingested text.

---

## Agent Prompt

```text
Add PDF ingestion to MathPath:

1. app/services/ingestion/pdf_extractor.py — PDFExtractor using PyMuPDF (primary) with pdfplumber fallback. Returns list of PageText(page_number, text).

2. app/services/ingestion/pdf_chunker.py — PDFChunker that chunks across pages while tracking page_start/page_end per chunk.

3. Extend app/api/routes/books.py — add POST /books/upload for multipart PDF upload. Save file locally, create Book row.

4. Add processing logic that extracts PDF text, chunks it, saves BookChunks with page refs.

5. scripts/ingest_pdf.py — CLI for PDF ingestion.

Add PyMuPDF, pdfplumber, python-multipart to requirements.
```
