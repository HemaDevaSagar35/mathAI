"""VisionPDFIngestor — vision-first PDF ingestion (B14 v2).

Pipeline:
  1. Open the PDF with PyMuPDF.
  2. Render every page to a PNG (cached under uploads/{book_id}/pages/).
  3. Extract a text-layer hint per page (may be empty for scans).
  4. Read the PDF outline (titles only; page numbers are unreliable so we
     pass them as hints, not ground truth).
  5. Run PageExtractor over the page batches to get typed PageExtraction rows.
  6. Run StructurePostprocessor to persist BookSection / BookChunk / BookFigure
     rows, with figure crops written under uploads/{book_id}/figures/.

This service is async because PageExtractor calls a multimodal LLM. The
DB writes inside StructurePostprocessor are sync (matching the rest of
this codebase).
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF
from sqlalchemy.orm import Session

from app.models.book import Book
from app.schemas.page_extraction import PageExtraction
from app.services.ingestion.page_extractor import (
    PageExtractor,
    PageExtractorConfig,
    PageInput,
)
from app.services.ingestion.structure_postprocessor import (
    StructureProcessResult,
    StructurePostprocessor,
)

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path("uploads")
DEFAULT_RENDER_DPI = 150
DEFAULT_FIGURE_DPI = 200


@dataclass
class VisionIngestResult:
    pages_extracted: int
    extractions: list[PageExtraction]
    structure: StructureProcessResult


class VisionPDFIngestor:
    def __init__(
        self,
        page_extractor: PageExtractor | None = None,
        postprocessor: StructurePostprocessor | None = None,
        render_dpi: int = DEFAULT_RENDER_DPI,
        figure_dpi: int = DEFAULT_FIGURE_DPI,
    ):
        self.page_extractor = page_extractor or PageExtractor()
        self.postprocessor = postprocessor or StructurePostprocessor()
        self.render_dpi = render_dpi
        self.figure_dpi = figure_dpi

    async def ingest(
        self,
        db: Session,
        book_id: uuid.UUID,
        file_path: str,
    ) -> VisionIngestResult:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {file_path}")

        book = db.get(Book, book_id)
        book_title = book.title if book else ""

        book_root = UPLOAD_DIR / str(book_id)
        pages_dir = book_root / "pages"
        figures_dir = book_root / "figures"
        pages_dir.mkdir(parents=True, exist_ok=True)
        figures_dir.mkdir(parents=True, exist_ok=True)

        with fitz.open(file_path) as doc:
            page_inputs = self._render_and_collect(doc, pages_dir)
            toc_titles = self._extract_toc_titles(doc)

            self.page_extractor.config = self._configure_extractor_config(
                book_title, toc_titles
            )

            logger.info(
                "VisionPDFIngestor: rendering %d pages, calling LLM in batches of %d",
                len(page_inputs),
                self.page_extractor.config.batch_size,
            )
            extractions = await self.page_extractor.extract(page_inputs)

            crop_figure = _make_crop_figure(doc, dpi=self.figure_dpi, render_dpi=self.render_dpi)

            structure = self.postprocessor.process(
                db=db,
                book_id=book_id,
                extractions=extractions,
                crop_figure=crop_figure,
                figures_dir=figures_dir,
            )

        logger.info(
            "VisionPDFIngestor done: pages=%d sections=%d chunks=%d figures=%d low_conf=%d",
            structure.pages_processed,
            structure.sections_created,
            structure.chunks_created,
            structure.figures_created,
            len(structure.low_confidence_pages),
        )
        return VisionIngestResult(
            pages_extracted=len(extractions),
            extractions=extractions,
            structure=structure,
        )

    def _configure_extractor_config(
        self, book_title: str, toc_titles: list[str]
    ) -> PageExtractorConfig:
        cfg = self.page_extractor.config
        return PageExtractorConfig(
            book_title_hint=book_title or cfg.book_title_hint,
            subject_hint=cfg.subject_hint,
            known_toc_titles=toc_titles,
            batch_size=cfg.batch_size,
            max_concurrency=cfg.max_concurrency,
            max_tokens=cfg.max_tokens,
            text_hint_char_limit=cfg.text_hint_char_limit,
        )

    def _render_and_collect(
        self, doc: "fitz.Document", pages_dir: Path
    ) -> list[PageInput]:
        inputs: list[PageInput] = []
        for index in range(doc.page_count):
            page = doc[index]
            page_number = index + 1

            pix = page.get_pixmap(dpi=self.render_dpi)
            png_bytes = pix.tobytes("png")
            (pages_dir / f"p{page_number:04d}.png").write_bytes(png_bytes)

            text_hint = page.get_text("text") or ""
            inputs.append(
                PageInput(page=page_number, image=png_bytes, text_hint=text_hint)
            )
        return inputs

    @staticmethod
    def _extract_toc_titles(doc: "fitz.Document") -> list[str]:
        """Pull titles from the PDF outline. Page numbers are intentionally
        ignored — they're often miscalibrated against printed page numbers."""
        try:
            toc = doc.get_toc(simple=True)  # [[level, title, page], ...]
        except Exception:
            return []
        titles: list[str] = []
        for entry in toc:
            if len(entry) < 2:
                continue
            title = (entry[1] or "").strip()
            if title:
                titles.append(title)
        return titles


def _make_crop_figure(doc: "fitz.Document", *, dpi: int, render_dpi: int):
    """Build a `(page, bbox) -> png_bytes` callable that crops figures.

    `bbox` is in image pixel coordinates of the page rendered at `render_dpi`
    (origin top-left, [x, y, width, height]). We convert back to PDF point
    coordinates (1/72 inch) and re-render the clipped region at `dpi`.
    """

    scale = 72.0 / render_dpi

    def crop(page_number: int, bbox: list[float]) -> bytes:
        if page_number < 1 or page_number > doc.page_count:
            raise ValueError(f"page {page_number} out of range")
        if len(bbox) != 4:
            raise ValueError(f"bbox must have 4 elements, got {bbox!r}")

        x, y, w, h = bbox
        x0 = max(0.0, x) * scale
        y0 = max(0.0, y) * scale
        x1 = (x + max(0.0, w)) * scale
        y1 = (y + max(0.0, h)) * scale

        page = doc[page_number - 1]
        page_rect = page.rect
        # Clip into the page rect to defend against bbox bleed-over.
        x1 = min(x1, page_rect.width)
        y1 = min(y1, page_rect.height)
        if x1 <= x0 or y1 <= y0:
            raise ValueError(f"degenerate bbox after clipping: {bbox!r}")

        clip = fitz.Rect(x0, y0, x1, y1)
        pix = page.get_pixmap(dpi=dpi, clip=clip)
        return pix.tobytes("png")

    return crop


__all__ = ["VisionPDFIngestor", "VisionIngestResult"]
