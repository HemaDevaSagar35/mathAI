import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.book import Book, BookChunk
from app.schemas.book import BookChunkRead, BookCreate, BookRead
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
