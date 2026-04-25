#!/usr/bin/env python
"""Seed a book from a text file. Usage: python scripts/seed_math_text.py --title "..." --file path/to/file.txt"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal
from app.models.book import Book
from app.services.ingestion.text_ingestor import TextIngestor


def main():
    parser = argparse.ArgumentParser(description="Seed a math text into the database")
    parser.add_argument("--title", required=True, help="Book title")
    parser.add_argument("--file", required=True, help="Path to .txt file")
    parser.add_argument("--max-tokens", type=int, default=800)
    parser.add_argument("--overlap", type=int, default=100)
    args = parser.parse_args()

    text = Path(args.file).read_text(encoding="utf-8")
    print(f"Read {len(text)} chars from {args.file}")

    db = SessionLocal()
    try:
        book = Book(title=args.title, source_type="text")
        db.add(book)
        db.flush()

        ingestor = TextIngestor(max_tokens=args.max_tokens, overlap_tokens=args.overlap)
        chunks = ingestor.ingest(db, book.id, text)

        total_tokens = sum(c.token_count for c in chunks)
        print(f"\nbook_id:      {book.id}")
        print(f"chunks:       {len(chunks)}")
        print(f"total_tokens: {total_tokens}")
        print(f"status:       {book.status}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
