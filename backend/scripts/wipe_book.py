#!/usr/bin/env python
"""Wipe MathPath book data — DB rows + on-disk files.

For ingestion validation runs where you want a clean slate between attempts.

Usage:
    python scripts/wipe_book.py <book_id>             # wipe one book (asks confirm)
    python scripts/wipe_book.py <book_id> --yes       # skip confirm
    python scripts/wipe_book.py --all                 # wipe ALL books
    python scripts/wipe_book.py --all --yes           # skip confirm
    python scripts/wipe_book.py <book_id> --dry-run   # show what would happen

What gets removed (per book):

  DB rows (cascades from `books.id` FK with ondelete=CASCADE):
    book_sections, book_chunks, book_figures, book_profiles,
    concepts, concept_edges, study_plans, tidbits,
    tidbit_lessons, tidbit_quizzes, tidbit_questions, proof_ladders.
    learning_memory_events: cleared explicitly (FK has no CASCADE).

  Files:
    uploads/<book_id>.pdf        (original upload)
    uploads/<book_id>/           (page renders + figure crops)

The `uploads/dumps/` directory is preserved by --all.
"""
from __future__ import annotations

import argparse
import shutil
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.db.session import SessionLocal  # noqa: E402
from app.models.book import Book  # noqa: E402
from app.models.memory import LearningMemoryEvent  # noqa: E402

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
PRESERVED_DIRS = {"dumps"}

# `learning_memory_events.book_id` has no ON DELETE CASCADE, so we have to
# clear those rows explicitly before deleting books. We use the model's
# `__tablename__` so a future rename can't desync this script.
MEMORY_TABLE = LearningMemoryEvent.__tablename__


def _table_exists(db: Session, table_name: str) -> bool:
    """Defensive: a fresh dev DB may not have every table. Skip silently."""
    row = db.execute(
        text("SELECT to_regclass(:t)"), {"t": table_name}
    ).scalar()
    return row is not None


def _files_for_book(book_id: uuid.UUID) -> list[Path]:
    candidates = [
        UPLOAD_DIR / f"{book_id}.pdf",
        UPLOAD_DIR / str(book_id),
    ]
    return [p for p in candidates if p.exists()]


def _remove_path(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()


def wipe_one(book_id: uuid.UUID, *, dry_run: bool) -> tuple[int, list[Path]]:
    db = SessionLocal()
    try:
        book = db.get(Book, book_id)
        if not book:
            print(f"No book with id {book_id} in DB.")
            files = _files_for_book(book_id)
            if files and not dry_run:
                print("Found stray on-disk files for that id; removing.")
                for f in files:
                    _remove_path(f)
            return 0, files

        files = _files_for_book(book_id)

        if not dry_run:
            if _table_exists(db, MEMORY_TABLE):
                db.execute(
                    text(f"DELETE FROM {MEMORY_TABLE} WHERE book_id = :bid"),
                    {"bid": str(book_id)},
                )
            db.delete(book)
            db.commit()
            for f in files:
                _remove_path(f)

        return 1, files
    finally:
        db.close()


def wipe_all(*, dry_run: bool) -> tuple[int, list[Path]]:
    db = SessionLocal()
    try:
        all_books = db.query(Book).all()
        n_books = len(all_books)

        if not dry_run and n_books:
            if _table_exists(db, MEMORY_TABLE):
                db.execute(text(f"DELETE FROM {MEMORY_TABLE}"))
            db.execute(text("TRUNCATE books CASCADE"))
            db.commit()

        if not UPLOAD_DIR.exists():
            return n_books, []

        targets = [
            p for p in UPLOAD_DIR.iterdir() if p.name not in PRESERVED_DIRS
        ]

        if not dry_run:
            for t in targets:
                _remove_path(t)

        return n_books, targets
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__.strip().splitlines()[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="\n".join(__doc__.splitlines()[2:]),
    )
    parser.add_argument(
        "book_id",
        nargs="?",
        help="UUID of the book to wipe (omit when using --all)",
    )
    parser.add_argument("--all", action="store_true", help="Wipe ALL books")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
    )
    args = parser.parse_args()

    if args.all and args.book_id:
        parser.error("pass either a book_id or --all, not both")
    if not args.all and not args.book_id:
        parser.error("provide a book_id, or pass --all")

    if args.all:
        action_desc = "ALL books and per-book files (uploads/dumps/ preserved)"
        book_uuid: uuid.UUID | None = None
    else:
        try:
            book_uuid = uuid.UUID(args.book_id)
        except ValueError:
            print(f"Invalid book_id: {args.book_id!r}", file=sys.stderr)
            return 2
        action_desc = f"book {book_uuid} and its files"

    if args.dry_run:
        print(f"DRY RUN — would delete {action_desc}")
    elif not args.yes:
        print(f"About to delete {action_desc}.")
        try:
            resp = input("Type 'yes' to confirm: ").strip().lower()
        except EOFError:
            resp = ""
        if resp != "yes":
            print("Aborted.")
            return 1

    if args.all:
        n_books, file_list = wipe_all(dry_run=args.dry_run)
    else:
        assert book_uuid is not None
        n_books, file_list = wipe_one(book_uuid, dry_run=args.dry_run)

    verb = "Would delete" if args.dry_run else "Deleted"
    print(
        f"\n{verb} {n_books} book row(s) "
        f"(cascading to sections/chunks/figures/profile/concepts/plans/tidbits/lessons/quizzes)."
    )
    print(f"{verb} {len(file_list)} on-disk target(s):")
    for f in file_list:
        print(f"  - {f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
