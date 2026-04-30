import logging
from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF
import pdfplumber

logger = logging.getLogger(__name__)

MIN_CHARS_PER_PAGE = 50


@dataclass
class PageText:
    page_number: int
    text: str


class PDFExtractor:
    def extract(self, file_path: str) -> list[PageText]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {file_path}")

        pages = self._extract_pymupdf(str(path))

        poor_pages = [p for p in pages if len(p.text.strip()) < MIN_CHARS_PER_PAGE]
        if poor_pages:
            logger.info(
                "%d pages had thin text from PyMuPDF, trying pdfplumber fallback",
                len(poor_pages),
            )
            fallback = self._extract_pdfplumber_pages(str(path), [p.page_number for p in poor_pages])
            page_map = {p.page_number: p for p in pages}
            for fb in fallback:
                if len(fb.text.strip()) > len(page_map.get(fb.page_number, PageText(0, "")).text.strip()):
                    page_map[fb.page_number] = fb
            pages = sorted(page_map.values(), key=lambda p: p.page_number)

        pages = self._strip_headers_footers(pages)
        return [p for p in pages if p.text.strip()]

    @staticmethod
    def _extract_pymupdf(file_path: str) -> list[PageText]:
        doc = fitz.open(file_path)
        pages = []
        for i, page in enumerate(doc):
            text = page.get_text("text")
            pages.append(PageText(page_number=i + 1, text=text))
        doc.close()
        return pages

    @staticmethod
    def _extract_pdfplumber_pages(file_path: str, page_numbers: list[int]) -> list[PageText]:
        results = []
        with pdfplumber.open(file_path) as pdf:
            for pn in page_numbers:
                idx = pn - 1
                if 0 <= idx < len(pdf.pages):
                    text = pdf.pages[idx].extract_text() or ""
                    results.append(PageText(page_number=pn, text=text))
        return results

    @staticmethod
    def _strip_headers_footers(pages: list[PageText], min_pages: int = 3) -> list[PageText]:
        """Remove lines that appear identically on many pages (likely headers/footers)."""
        if len(pages) < min_pages:
            return pages

        first_lines: dict[str, int] = {}
        last_lines: dict[str, int] = {}

        for p in pages:
            lines = p.text.strip().split("\n")
            if lines:
                fl = lines[0].strip()
                if fl:
                    first_lines[fl] = first_lines.get(fl, 0) + 1
                ll = lines[-1].strip()
                if ll:
                    last_lines[ll] = last_lines.get(ll, 0) + 1

        threshold = len(pages) * 0.5
        repeated_first = {line for line, count in first_lines.items() if count >= threshold}
        repeated_last = {line for line, count in last_lines.items() if count >= threshold}

        cleaned = []
        for p in pages:
            lines = p.text.strip().split("\n")
            if lines and lines[0].strip() in repeated_first:
                lines = lines[1:]
            if lines and lines[-1].strip() in repeated_last:
                lines = lines[:-1]
            cleaned.append(PageText(page_number=p.page_number, text="\n".join(lines)))

        return cleaned
