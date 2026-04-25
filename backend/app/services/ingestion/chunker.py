import re
from dataclasses import dataclass

from app.services.ingestion.token_counter import count_tokens


@dataclass
class ChunkResult:
    chunk_index: int
    text: str
    token_count: int


class Chunker:
    def __init__(self, max_tokens: int = 800, overlap_tokens: int = 100):
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens

    def chunk(self, text: str) -> list[ChunkResult]:
        paragraphs = self._split_paragraphs(text)
        merged = self._merge_paragraphs(paragraphs)
        chunks = self._add_overlap(merged)
        return [
            ChunkResult(chunk_index=i, text=c, token_count=count_tokens(c))
            for i, c in enumerate(chunks)
        ]

    def _split_paragraphs(self, text: str) -> list[str]:
        raw = re.split(r"\n\s*\n", text.strip())
        paragraphs = []
        for p in raw:
            p = p.strip()
            if not p:
                continue
            if count_tokens(p) <= self.max_tokens:
                paragraphs.append(p)
            else:
                paragraphs.extend(self._split_on_sentences(p))
        return paragraphs

    def _split_on_sentences(self, text: str) -> list[str]:
        sentences = re.split(r"(?<=[.!?])\s+", text)
        parts: list[str] = []
        current: list[str] = []
        current_tokens = 0

        for sentence in sentences:
            stokens = count_tokens(sentence)
            if current and current_tokens + stokens > self.max_tokens:
                parts.append(" ".join(current))
                current = [sentence]
                current_tokens = stokens
            else:
                current.append(sentence)
                current_tokens += stokens

        if current:
            parts.append(" ".join(current))
        return parts

    def _merge_paragraphs(self, paragraphs: list[str]) -> list[str]:
        merged: list[str] = []
        current: list[str] = []
        current_tokens = 0

        for p in paragraphs:
            ptokens = count_tokens(p)
            if current and current_tokens + ptokens > self.max_tokens:
                merged.append("\n\n".join(current))
                current = [p]
                current_tokens = ptokens
            else:
                current.append(p)
                current_tokens += ptokens

        if current:
            merged.append("\n\n".join(current))
        return merged

    def _add_overlap(self, segments: list[str]) -> list[str]:
        if len(segments) <= 1:
            return segments

        result: list[str] = [segments[0]]
        for i in range(1, len(segments)):
            prev_words = segments[i - 1].split()
            overlap_words: list[str] = []
            token_budget = self.overlap_tokens

            for w in reversed(prev_words):
                wtokens = count_tokens(w)
                if token_budget - wtokens < 0 and overlap_words:
                    break
                overlap_words.insert(0, w)
                token_budget -= wtokens

            overlap_text = " ".join(overlap_words)
            result.append(overlap_text + "\n\n" + segments[i])

        return result
