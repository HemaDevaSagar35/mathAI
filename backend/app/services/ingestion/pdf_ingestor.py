import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.book import Book, BookChunk
from app.services.ingestion.pdf_chunker import PDFChunker
from app.services.ingestion.pdf_extractor import PDFExtractor

UPLOAD_DIR = Path("uploads")


def save_upload_file(content: bytes, book_id: uuid.UUID) -> str:
    UPLOAD_DIR.mkdir(exist_ok=True)
    path = UPLOAD_DIR / f"{book_id}.pdf"
    path.write_bytes(content)
    return str(path)


class PDFIngestor:
    def __init__(self, max_tokens: int = 800, overlap_tokens: int = 100):
        self.extractor = PDFExtractor()
        self.chunker = PDFChunker(max_tokens=max_tokens, overlap_tokens=overlap_tokens)

    def ingest(self, db: Session, book_id: uuid.UUID, file_path: str) -> list[BookChunk]:
        pages = self.extractor.extract(file_path)
        if not pages:
            raise ValueError(f"No text extracted from PDF: {file_path}")

        chunk_results = self.chunker.chunk_with_pages(pages)

        chunks: list[BookChunk] = []
        for cr in chunk_results:
            chunk = BookChunk(
                book_id=book_id,
                chunk_index=cr.chunk_index,
                raw_text=cr.text,
                clean_text=cr.text,
                token_count=cr.token_count,
                page_start=cr.page_start,
                page_end=cr.page_end,
            )
            db.add(chunk)
            chunks.append(chunk)

        book = db.get(Book, book_id)
        if book:
            book.status = "processed"

        db.commit()
        for c in chunks:
            db.refresh(c)
        return chunks
