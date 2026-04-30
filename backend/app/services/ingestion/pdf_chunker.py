import re
from dataclasses import dataclass

from app.services.ingestion.pdf_extractor import PageText
from app.services.ingestion.token_counter import count_tokens


@dataclass
class PDFChunkResult:
    chunk_index: int
    text: str
    token_count: int
    page_start: int
    page_end: int


class PDFChunker:
    def __init__(self, max_tokens: int = 800, overlap_tokens: int = 100):
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens

    def chunk_with_pages(self, pages: list[PageText]) -> list[PDFChunkResult]:
        segments = self._build_segments(pages)
        chunks = self._merge_and_chunk(segments)
        return chunks

    def _build_segments(self, pages: list[PageText]) -> list[dict]:
        """Split each page into paragraphs, keeping page number."""
        segments: list[dict] = []
        for page in pages:
            paragraphs = re.split(r"\n\s*\n", page.text.strip())
            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue
                segments.append({
                    "text": para,
                    "tokens": count_tokens(para),
                    "page": page.page_number,
                })
        return segments

    def _merge_and_chunk(self, segments: list[dict]) -> list[PDFChunkResult]:
        chunks: list[PDFChunkResult] = []
        current_texts: list[str] = []
        current_tokens = 0
        current_page_start = 0
        current_page_end = 0

        for seg in segments:
            if not current_texts:
                current_page_start = seg["page"]

            if current_tokens + seg["tokens"] > self.max_tokens and current_texts:
                chunks.append(PDFChunkResult(
                    chunk_index=len(chunks),
                    text="\n\n".join(current_texts),
                    token_count=current_tokens,
                    page_start=current_page_start,
                    page_end=current_page_end,
                ))

                # Overlap: carry tail of previous chunk
                overlap_text = self._get_overlap(current_texts)
                current_texts = [overlap_text, seg["text"]] if overlap_text else [seg["text"]]
                current_tokens = count_tokens("\n\n".join(current_texts))
                current_page_start = current_page_end
            else:
                current_texts.append(seg["text"])
                current_tokens += seg["tokens"]

            current_page_end = seg["page"]

        if current_texts:
            chunks.append(PDFChunkResult(
                chunk_index=len(chunks),
                text="\n\n".join(current_texts),
                token_count=count_tokens("\n\n".join(current_texts)),
                page_start=current_page_start,
                page_end=current_page_end,
            ))

        return chunks

    def _get_overlap(self, texts: list[str]) -> str:
        full = "\n\n".join(texts)
        words = full.split()
        overlap_words: list[str] = []
        budget = self.overlap_tokens

        for w in reversed(words):
            wt = count_tokens(w)
            if budget - wt < 0 and overlap_words:
                break
            overlap_words.insert(0, w)
            budget -= wt

        return " ".join(overlap_words) if overlap_words else ""
