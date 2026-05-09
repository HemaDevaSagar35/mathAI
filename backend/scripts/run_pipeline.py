#!/usr/bin/env python
"""
Run the full MathPath pipeline on a PDF.

Usage:
  python scripts/run_pipeline.py --pdf path/to/book.pdf --title "Calculus Ch3"
  python scripts/run_pipeline.py --pdf path/to/book.pdf --title "Calculus Ch3" \
      --provider anthropic --model claude-sonnet-4-20250514
"""
import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run the full MathPath pipeline")
    parser.add_argument("--pdf", required=True, help="Path to .pdf file")
    parser.add_argument("--title", required=True, help="Book title")
    parser.add_argument(
        "--provider",
        help="LLM provider override (openai | anthropic | gemini). "
        "Must be passed together with --model.",
    )
    parser.add_argument(
        "--model",
        help="LLM model override. Must be passed together with --provider.",
    )
    args = parser.parse_args()

    if bool(args.provider) ^ bool(args.model):
        parser.error("--provider and --model must be passed together")

    from app.core.config import settings
    from app.db.session import SessionLocal
    from app.models.book import Book
    from app.services.ingestion.page_extractor import (
        PageExtractor,
        PageExtractorConfig,
    )
    from app.services.ingestion.structure_postprocessor import StructurePostprocessor
    from app.services.ingestion.vision_pdf_ingestor import (
        VisionPDFIngestor,
        save_upload_file,
    )
    from app.services.pipeline import PipelineOrchestrator

    db = SessionLocal()
    try:
        book = Book(title=args.title, source_type="pdf", status="uploaded")
        db.add(book)
        db.flush()

        content = Path(args.pdf).read_bytes()
        file_path = save_upload_file(content, book.id)
        book.file_url = file_path

        ingestor = VisionPDFIngestor(
            page_extractor=PageExtractor(
                config=PageExtractorConfig(batch_size=settings.VISION_BATCH_SIZE)
            ),
            postprocessor=StructurePostprocessor(),
            render_dpi=settings.VISION_RENDER_DPI,
            figure_dpi=settings.VISION_FIGURE_DPI,
        )
        result = await ingestor.ingest(db, book.id, file_path)
        print(
            f"Ingested PDF: book_id={book.id} pages={result.pages_extracted} "
            f"sections={result.structure.sections_created} "
            f"chunks={result.structure.chunks_created} "
            f"figures={result.structure.figures_created}"
        )

        orchestrator = PipelineOrchestrator(provider=args.provider, model=args.model)
        run_result = await orchestrator.run(db, book.id)

        print()
        for step in run_result.get("steps_run", []):
            print(f"[done] {step}")
        for err in run_result.get("errors", []):
            print(f"[err]  {err}")

        print("\n--- Pipeline Complete ---")
        print(f"Book ID:       {run_result['book_id']}")
        if "profile" in run_result:
            p = run_result["profile"]
            print(f"Subject:       {p['subject']} ({p['level']}, {p['style']})")
        if "concepts" in run_result:
            print(f"Concepts:      {run_result['concepts']}")
        if "edges" in run_result:
            print(f"Graph edges:   {run_result['edges']}")
        if "tidbits" in run_result:
            print(f"Tidbits:       {run_result['tidbits']}")
        if "first_lesson_tidbit" in run_result:
            print(f"First lesson:  {run_result['first_lesson_tidbit']}")
        if "first_quiz_questions" in run_result:
            print(f"First quiz:    {run_result['first_quiz_questions']} questions")

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
