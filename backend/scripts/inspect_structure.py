#!/usr/bin/env python
"""Inspect the detected structure of a book ingested via the vision pipeline.

Prints the BookSection tree, per-chunk page-kind / confidence summary, and
counts of figures. Use after a vision ingest to verify detection quality.

Usage:
    python scripts/inspect_structure.py --book-id <uuid>
"""
from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path

# Make `app.*` imports resolve when this file is run directly via
# `python scripts/inspect_structure.py` from the backend/ directory.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.orm import Session  # noqa: E402

from app.db.session import SessionLocal  # noqa: E402
from app.models.book import Book, BookChunk  # noqa: E402
from app.models.figure import BookFigure  # noqa: E402
from app.models.section import BookSection  # noqa: E402


def _print_section_tree(
    sections: list[BookSection],
    parent_id: uuid.UUID | None = None,
    depth: int = 0,
) -> None:
    children = [s for s in sections if s.parent_id == parent_id]
    children.sort(key=lambda s: s.order_index)
    for s in children:
        indent = "  " * depth
        page_range = (
            f"pp.{s.page_start}–{s.page_end}"
            if s.page_start and s.page_end
            else "pp.?"
        )
        number = f"{s.number} " if s.number else ""
        marker = "[CH]" if s.level == 1 else "[§]"
        print(
            f"{indent}{marker} {number}{s.title}  "
            f"({page_range}, kind={s.kind}, conf={s.confidence:.2f})"
        )
        _print_section_tree(sections, s.id, depth + 1)


def _summarize(db: Session, book_id: uuid.UUID) -> int:
    book = db.get(Book, book_id)
    if not book:
        print(f"Book {book_id} not found", file=sys.stderr)
        return 1

    print(f"\nBook: {book.title}  (id={book.id}, status={book.status})")

    sections = (
        db.query(BookSection)
        .filter(BookSection.book_id == book_id)
        .all()
    )
    print(f"\nSections: {len(sections)} total")
    if sections:
        print()
        _print_section_tree(sections)
    else:
        print("  (none — book ingested via legacy / text path or structure detection failed)")

    chunks = (
        db.query(BookChunk)
        .filter(BookChunk.book_id == book_id)
        .order_by(BookChunk.chunk_index)
        .all()
    )
    print(f"\nChunks: {len(chunks)} total")
    if chunks:
        kinds: dict[str | None, int] = {}
        with_section = 0
        with_blocks = 0
        confs: list[float] = []
        for c in chunks:
            kinds[c.page_kind] = kinds.get(c.page_kind, 0) + 1
            if c.section_id is not None:
                with_section += 1
            if c.blocks:
                with_blocks += 1
            if c.confidence is not None:
                confs.append(c.confidence)
        avg_conf = sum(confs) / len(confs) if confs else 0.0
        print(
            f"  attached to a section: {with_section}/{len(chunks)}, "
            f"with typed blocks: {with_blocks}/{len(chunks)}, "
            f"avg confidence: {avg_conf:.2f}"
        )
        print("  by page_kind:")
        for kind, count in sorted(kinds.items(), key=lambda kv: -kv[1]):
            print(f"    {kind or '(legacy)':<14} {count}")

    figures = db.query(BookFigure).filter(BookFigure.book_id == book_id).count()
    print(f"\nFigures: {figures}")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--book-id", required=True, help="UUID of the book to inspect")
    args = parser.parse_args()

    try:
        book_id = uuid.UUID(args.book_id)
    except ValueError:
        print(f"Not a valid UUID: {args.book_id!r}", file=sys.stderr)
        return 2

    db = SessionLocal()
    try:
        return _summarize(db, book_id)
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
