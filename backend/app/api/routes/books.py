import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.book import Book, BookChunk
from app.schemas.book import BookChunkRead, BookCreate, BookRead, ProcessRequest
from app.services.ingestion.text_ingestor import TextIngestor

router = APIRouter(tags=["books"])

_ingestor = TextIngestor()


@router.post("/books/text", response_model=BookRead)
def create_book_from_text(data: BookCreate, db: Session = Depends(get_db)):
    if not data.text:
        raise HTTPException(status_code=400, detail="text field is required for text ingestion")

    book = Book(title=data.title, source_type=data.source_type)
    db.add(book)
    db.flush()

    _ingestor.ingest(db, book.id, data.text)
    db.refresh(book)
    return book


@router.get("/books", response_model=list[BookRead])
def list_books(db: Session = Depends(get_db)):
    return db.query(Book).order_by(Book.created_at.desc()).all()


@router.get("/books/{book_id}", response_model=BookRead)
def get_book(book_id: uuid.UUID, db: Session = Depends(get_db)):
    book = db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.get("/books/{book_id}/chunks", response_model=list[BookChunkRead])
def get_book_chunks(book_id: uuid.UUID, db: Session = Depends(get_db)):
    book = db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return (
        db.query(BookChunk)
        .filter(BookChunk.book_id == book_id)
        .order_by(BookChunk.chunk_index)
        .all()
    )


@router.post("/books/upload", response_model=BookRead)
async def upload_book_pdf(
    file: UploadFile = File(...),
    title: str = Form(None),
    use_vision: bool | None = None,
    db: Session = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    from app.core.config import settings
    from app.services.ingestion.pdf_ingestor import PDFIngestor, save_upload_file

    book_title = title or file.filename.rsplit(".", 1)[0]
    book = Book(title=book_title, source_type="pdf", status="uploaded")
    db.add(book)
    db.flush()

    content = await file.read()
    file_path = save_upload_file(content, book.id)
    book.file_url = file_path

    vision_on = use_vision if use_vision is not None else settings.VISION_INGESTION_ENABLED
    if vision_on:
        from app.services.ingestion.page_extractor import (
            PageExtractor,
            PageExtractorConfig,
        )
        from app.services.ingestion.structure_postprocessor import (
            StructurePostprocessor,
        )
        from app.services.ingestion.vision_pdf_ingestor import VisionPDFIngestor

        extractor = PageExtractor(
            config=PageExtractorConfig(batch_size=settings.VISION_BATCH_SIZE)
        )
        ingestor = VisionPDFIngestor(
            page_extractor=extractor,
            postprocessor=StructurePostprocessor(),
            render_dpi=settings.VISION_RENDER_DPI,
            figure_dpi=settings.VISION_FIGURE_DPI,
        )
        await ingestor.ingest(db, book.id, file_path)
    else:
        PDFIngestor().ingest(db, book.id, file_path)

    db.refresh(book)
    return book


@router.post("/books/{book_id}/process")
async def process_book(
    book_id: uuid.UUID,
    data: ProcessRequest | None = None,
    db: Session = Depends(get_db),
):
    book = db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    from app.services.pipeline import PipelineOrchestrator

    orchestrator = PipelineOrchestrator(
        provider=data.provider if data else None,
        model=data.model if data else None,
    )
    steps = data.steps if data else None
    result = await orchestrator.run(db, book_id, steps=steps)
    return result
