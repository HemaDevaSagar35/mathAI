#!/usr/bin/env python
"""
Run the full MathPath pipeline.

Usage:
  python scripts/run_pipeline.py --file tests/fixtures/linear_algebra_span_source.txt --title "Linear Algebra"
  python scripts/run_pipeline.py --pdf path/to/chapter.pdf --title "Calculus Ch3" --provider anthropic
"""
import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


async def main():
    parser = argparse.ArgumentParser(description="Run the full MathPath pipeline")
    parser.add_argument("--file", help="Path to .txt file")
    parser.add_argument("--pdf", help="Path to .pdf file")
    parser.add_argument("--title", required=True, help="Book title")
    parser.add_argument("--provider", help="LLM provider override (openai, anthropic, gemini)")
    parser.add_argument("--model", help="LLM model override")
    args = parser.parse_args()

    if not args.file and not args.pdf:
        parser.error("Provide either --file (text) or --pdf")

    from app.db.session import SessionLocal
    from app.models.book import Book
    from app.services.pipeline import PipelineOrchestrator

    db = SessionLocal()
    try:
        # Step 1: Ingest
        if args.pdf:
            from app.services.ingestion.pdf_ingestor import PDFIngestor
            book = Book(title=args.title, source_type="pdf", status="uploaded")
            db.add(book)
            db.flush()
            book.file_url = args.pdf
            ingestor = PDFIngestor()
            chunks = ingestor.ingest(db, book.id, args.pdf)
            print(f"✓ Ingested PDF: {book.id}, {len(chunks)} chunks")
        else:
            from app.services.ingestion.text_ingestor import TextIngestor
            text = Path(args.file).read_text(encoding="utf-8")
            book = Book(title=args.title, source_type="text")
            db.add(book)
            db.flush()
            ingestor = TextIngestor()
            chunks = ingestor.ingest(db, book.id, text)
            print(f"✓ Ingested text: {book.id}, {len(chunks)} chunks")

        # Step 2: Run pipeline
        orchestrator = PipelineOrchestrator(provider=args.provider, model=args.model)
        result = await orchestrator.run(db, book.id)

        # Print results
        print()
        for step in result.get("steps_run", []):
            print(f"✓ {step}")

        if result.get("errors"):
            for err in result["errors"]:
                print(f"✗ {err}")

        print("\n--- Pipeline Complete ---")
        print(f"Book ID:       {result['book_id']}")
        if "profile" in result:
            p = result["profile"]
            print(f"Subject:       {p['subject']} ({p['level']}, {p['style']})")
        if "concepts" in result:
            print(f"Concepts:      {result['concepts']}")
        if "edges" in result:
            print(f"Graph edges:   {result['edges']}")
        if "tidbits" in result:
            print(f"Tidbits:       {result['tidbits']}")
        if "first_lesson_tidbit" in result:
            print(f"First lesson:  {result['first_lesson_tidbit']}")
        if "first_quiz_questions" in result:
            print(f"First quiz:    {result['first_quiz_questions']} questions")

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
