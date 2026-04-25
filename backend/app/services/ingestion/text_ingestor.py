import re
import uuid

from sqlalchemy.orm import Session

from app.models.book import Book, BookChunk
from app.services.ingestion.chunker import Chunker


class TextIngestor:
    def __init__(self, max_tokens: int = 800, overlap_tokens: int = 100):
        self.chunker = Chunker(max_tokens=max_tokens, overlap_tokens=overlap_tokens)

    def ingest(self, db: Session, book_id: uuid.UUID, raw_text: str) -> list[BookChunk]:
        clean = self._clean_text(raw_text)
        chunk_results = self.chunker.chunk(clean)

        chunks: list[BookChunk] = []
        for cr in chunk_results:
            chunk = BookChunk(
                book_id=book_id,
                chunk_index=cr.chunk_index,
                raw_text=cr.text,
                clean_text=cr.text,
                token_count=cr.token_count,
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

    @staticmethod
    def _clean_text(text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"[^\S\n]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
