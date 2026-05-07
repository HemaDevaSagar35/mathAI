"""Vision-based per-page extraction service.

Takes rendered page images (PNG bytes), batches them, sends them to a
multimodal LLM with a structure+content extraction prompt, and returns typed
PageExtraction results. Threads section-path continuity across batches so the
model doesn't redundantly emit chapter_start events on every page.

This service is read-only with respect to the database; the caller is
responsible for persisting the resulting BookSection / BookChunk / BookFigure
rows via the structure post-processor (Phase 2).
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

from app.llm.clients import BaseLLMClient, get_llm_client
from app.llm.prompts.loader import load_prompt
from app.schemas.page_extraction import (
    PageBatchExtraction,
    PageExtraction,
    section_path_after,
)

logger = logging.getLogger(__name__)


DEFAULT_BATCH_SIZE = 5
DEFAULT_MAX_CONCURRENCY = 3
DEFAULT_MAX_TOKENS = 8192
LOW_CONFIDENCE_THRESHOLD = 0.5


@dataclass
class PageInput:
    """One page's input to the extractor."""

    page: int
    image: bytes  # PNG-encoded
    text_hint: str | None = None  # PyMuPDF text-layer extraction, may be empty


@dataclass
class PageExtractorConfig:
    book_title_hint: str = ""
    subject_hint: str = ""
    known_toc_titles: list[str] = field(default_factory=list)
    batch_size: int = DEFAULT_BATCH_SIZE
    max_concurrency: int = DEFAULT_MAX_CONCURRENCY
    max_tokens: int = DEFAULT_MAX_TOKENS
    text_hint_char_limit: int = 1500  # truncate long PyMuPDF dumps per page


class PageExtractor:
    """Run vision-based page extraction over a stream of PageInputs."""

    def __init__(
        self,
        llm: BaseLLMClient | None = None,
        config: PageExtractorConfig | None = None,
    ):
        self.llm = llm or get_llm_client(task="page_extraction")
        self.config = config or PageExtractorConfig()

    async def extract(self, pages: list[PageInput]) -> list[PageExtraction]:
        """Extract all pages, returning results in input order.

        Batches are processed in submission order to preserve continuity of
        section paths, but within the bound of `max_concurrency` we process
        non-adjacent batches in parallel by snapshotting the running path.
        For correctness we currently run batches sequentially; concurrency is
        a future optimization once we have a reliable continuity-merge step.
        """
        results: list[PageExtraction] = []
        current_path: list[str] = []

        batches = [
            pages[i : i + self.config.batch_size]
            for i in range(0, len(pages), self.config.batch_size)
        ]

        for batch_index, batch in enumerate(batches):
            try:
                extraction = await self._extract_batch(batch, current_path)
            except Exception as exc:
                logger.exception(
                    "page extraction failed for batch %d (pages %s): %s",
                    batch_index,
                    [p.page for p in batch],
                    exc,
                )
                # Emit empty placeholders so caller still has a per-page result.
                extraction = PageBatchExtraction(
                    pages=[
                        PageExtraction(
                            page=p.page,
                            page_kind="body",
                            structure_events=[],
                            blocks=[],
                            confidence=0.0,
                            notes=f"extraction failed: {exc!s}"[:500],
                        )
                        for p in batch
                    ]
                )

            results.extend(extraction.pages)

            # Update running section path from this batch's events in order.
            for page_result in extraction.pages:
                current_path = section_path_after(
                    current_path, page_result.structure_events
                )

            low_conf = [p for p in extraction.pages if p.confidence < LOW_CONFIDENCE_THRESHOLD]
            if low_conf:
                logger.info(
                    "batch %d had %d low-confidence pages: %s",
                    batch_index,
                    len(low_conf),
                    [p.page for p in low_conf],
                )

        return results

    async def _extract_batch(
        self, batch: list[PageInput], current_path: list[str]
    ) -> PageBatchExtraction:
        prompt = self._build_prompt(batch, current_path)
        images = [p.image for p in batch]

        raw = await self.llm.generate_json(
            prompt,
            task="page_extraction",
            images=images,
            max_tokens=self.config.max_tokens,
            temperature=0.1,
        )

        # Defensive: model may wrap output, may return list, etc.
        if isinstance(raw, list):
            raw = {"pages": raw}
        elif "pages" not in raw and isinstance(raw.get("page"), int):
            # Single-page response; wrap it.
            raw = {"pages": [raw]}

        return PageBatchExtraction.model_validate(raw)

    def _build_prompt(
        self, batch: list[PageInput], current_path: list[str]
    ) -> str:
        page_numbers = [p.page for p in batch]
        raw_text_hints = self._format_text_hints(batch)
        toc_titles_str = (
            "\n".join(f"- {t}" for t in self.config.known_toc_titles)
            if self.config.known_toc_titles
            else "(none provided)"
        )
        path_str = json.dumps(current_path or ["(before first chapter)"])

        return load_prompt(
            "page_extract",
            book_title_hint=self.config.book_title_hint or "(unknown)",
            subject_hint=self.config.subject_hint or "mathematics",
            known_toc_titles=toc_titles_str,
            n_pages=str(len(batch)),
            page_numbers=", ".join(str(n) for n in page_numbers),
            raw_text_hints=raw_text_hints,
            current_section_path=path_str,
        )

    def _format_text_hints(self, batch: list[PageInput]) -> str:
        limit = self.config.text_hint_char_limit
        parts: list[str] = []
        for p in batch:
            text = (p.text_hint or "").strip()
            if not text:
                parts.append(f"[Page {p.page}] (no text layer)")
                continue
            if len(text) > limit:
                text = text[:limit] + "...[truncated]"
            parts.append(f"[Page {p.page}]\n{text}")
        return "\n\n---\n\n".join(parts)


__all__ = [
    "PageExtractor",
    "PageExtractorConfig",
    "PageInput",
    "LOW_CONFIDENCE_THRESHOLD",
]
