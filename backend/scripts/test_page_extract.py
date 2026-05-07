#!/usr/bin/env python
"""Smoke-test the vision-based page extractor on a real PDF.

Renders the first N pages, sends them through the multimodal LLM via
PageExtractor, and prints the structured result. Does NOT touch the
database — purely for validating the prompt + extractor before committing
to a full ingestion.

Usage:
    python scripts/test_page_extract.py path/to/book.pdf [--pages 6]
                                                         [--from 1]
                                                         [--provider gemini]
                                                         [--model gemini-2.0-flash]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Make `app.*` imports resolve when this file is run directly via
# `python scripts/test_page_extract.py` from the backend/ directory.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import fitz  # PyMuPDF  # noqa: E402

from app.llm.clients import get_llm_client  # noqa: E402
from app.services.ingestion.page_extractor import (  # noqa: E402
    PageExtractor,
    PageExtractorConfig,
    PageInput,
)


async def _run(args: argparse.Namespace) -> int:
    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"PDF not found: {pdf_path}", file=sys.stderr)
        return 2

    with fitz.open(str(pdf_path)) as doc:
        first = max(1, args.from_)
        last = min(doc.page_count, first + args.pages - 1)
        if first > doc.page_count:
            print(f"--from {first} is past end (PDF has {doc.page_count} pages)", file=sys.stderr)
            return 2

        toc = doc.get_toc(simple=True)
        toc_titles = [entry[1].strip() for entry in toc if len(entry) >= 2 and entry[1]]

        page_inputs: list[PageInput] = []
        for index in range(first - 1, last):
            page = doc[index]
            pix = page.get_pixmap(dpi=args.dpi)
            png_bytes = pix.tobytes("png")
            text_hint = page.get_text("text") or ""
            page_inputs.append(
                PageInput(page=index + 1, image=png_bytes, text_hint=text_hint)
            )

    print(f"Sending {len(page_inputs)} pages (from {first} to {last}) to LLM...")
    llm = get_llm_client(provider=args.provider, model=args.model, task="page_extraction")
    extractor = PageExtractor(
        llm=llm,
        config=PageExtractorConfig(
            book_title_hint=pdf_path.stem,
            subject_hint="mathematics",
            known_toc_titles=toc_titles[:50],
            batch_size=args.batch_size,
        ),
    )
    extractions = await extractor.extract(page_inputs)

    print(f"\nReceived {len(extractions)} page extractions:\n")
    for ext in extractions:
        events = [
            f"{e.kind} L{e.level} '{e.number or ''} {e.title}'".strip()
            for e in ext.structure_events
        ]
        block_kinds: dict[str, int] = {}
        for b in ext.blocks:
            block_kinds[b.kind] = block_kinds.get(b.kind, 0) + 1
        print(
            f"  page {ext.page:4d}  kind={ext.page_kind:<12}"
            f"  conf={ext.confidence:.2f}"
            f"  events={events or '[]'}"
            f"  blocks={block_kinds}"
        )

    if args.dump:
        path = Path(args.dump)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = [json.loads(p.model_dump_json()) for p in extractions]
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nFull JSON dump written to {path}")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("pdf", help="Path to a PDF file")
    parser.add_argument("--pages", type=int, default=6, help="How many pages to test")
    parser.add_argument("--from", dest="from_", type=int, default=1, help="First page (1-indexed)")
    parser.add_argument("--dpi", type=int, default=150, help="Render DPI")
    parser.add_argument("--batch-size", type=int, default=5)
    parser.add_argument("--provider", default=None, help="Override LLM provider (default = task routing)")
    parser.add_argument("--model", default=None, help="Override LLM model")
    parser.add_argument("--dump", default=None, help="Write full JSON to this file")
    args = parser.parse_args()
    return asyncio.run(_run(args))


if __name__ == "__main__":
    sys.exit(main())
