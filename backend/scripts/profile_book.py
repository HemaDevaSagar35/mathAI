#!/usr/bin/env python
"""Profile a book. Usage: python scripts/profile_book.py --book-id BOOK_ID"""
import argparse
import asyncio
import json
import sys
from pathlib import Path
from uuid import UUID

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal
from app.services.profiling.book_profiler import BookProfiler


async def main():
    parser = argparse.ArgumentParser(description="Profile a book using LLM")
    parser.add_argument("--book-id", required=True, help="Book UUID")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        profiler = BookProfiler()
        profile = await profiler.profile_book(db, UUID(args.book_id))
        print(json.dumps(profile.profile_json, indent=2))
        print(f"\nSubject: {profile.detected_subject} (confidence: {profile.confidence})")
        print(f"Level: {profile.level} | Style: {profile.style}")
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
