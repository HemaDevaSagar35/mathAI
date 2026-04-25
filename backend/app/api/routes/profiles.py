import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.book import Book
from app.models.profile import BookProfile
from app.schemas.profile import BookProfileRead
from app.services.profiling.book_profiler import BookProfiler

router = APIRouter(tags=["profiles"])


@router.post("/books/{book_id}/profile", response_model=BookProfileRead)
async def profile_book(book_id: uuid.UUID, db: Session = Depends(get_db)):
    book = db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    existing = db.query(BookProfile).filter(BookProfile.book_id == book_id).first()
    if existing:
        return existing

    profiler = BookProfiler()
    profile = await profiler.profile_book(db, book_id)
    return profile


@router.get("/books/{book_id}/profile", response_model=BookProfileRead)
def get_profile(book_id: uuid.UUID, db: Session = Depends(get_db)):
    profile = db.query(BookProfile).filter(BookProfile.book_id == book_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found. POST to create one.")
    return profile
