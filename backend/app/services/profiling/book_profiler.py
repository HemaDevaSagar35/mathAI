import uuid

from sqlalchemy.orm import Session

from app.llm.clients import BaseLLMClient, get_llm_client
from app.llm.prompts.loader import load_prompt
from app.models.book import Book, BookChunk
from app.models.profile import BookProfile
from app.models.section import BookSection


class BookProfiler:
    def __init__(self, llm: BaseLLMClient | None = None):
        self.llm = llm or get_llm_client(task="book_profiling")

    async def profile_book(self, db: Session, book_id: uuid.UUID) -> BookProfile:
        book = db.get(Book, book_id)
        if not book:
            raise ValueError(f"Book {book_id} not found")

        chunks = (
            db.query(BookChunk)
            .filter(BookChunk.book_id == book_id)
            .order_by(BookChunk.chunk_index)
            .all()
        )
        if not chunks:
            raise ValueError(f"No chunks found for book {book_id}. Run text ingestion first.")

        sampled = self._sample_chunks_structure_aware(db, book_id, chunks)
        chunks_text = "\n\n---\n\n".join(
            f"[Chunk {c.chunk_index}]\n{c.clean_text}" for c in sampled
        )

        prompt = load_prompt("book_profile", chunks_text=chunks_text)
        data = await self.llm.generate_json(prompt, task="book_profiling")

        primary_subject = "unknown"
        confidence = 0.0
        if data.get("detected_subjects"):
            top = max(data["detected_subjects"], key=lambda s: s.get("confidence", 0))
            primary_subject = top["subject"]
            confidence = top.get("confidence", 0.0)

        profile = BookProfile(
            book_id=book_id,
            profile_json=data,
            detected_subject=primary_subject,
            level=data.get("level", "undergraduate"),
            style=data.get("style", "mixed"),
            proof_density=data.get("proof_density", "medium"),
            computation_density=data.get("computation_density", "medium"),
            diagram_dependency=data.get("diagram_dependency", "low"),
            confidence=confidence,
        )
        db.add(profile)

        book.status = "profiled"
        db.commit()
        db.refresh(profile)
        return profile

    def _sample_chunks_structure_aware(
        self,
        db: Session,
        book_id: uuid.UUID,
        chunks: list[BookChunk],
    ) -> list[BookChunk]:
        """Per-chapter sampling when BookSection rows exist; legacy fallback otherwise.

        With structure: take 3 chunks per chapter (first / middle / last). For
        books that came in via the legacy text-only path or where structure
        detection produced nothing, fall back to the original 5-3-2 split.
        """
        chapters = (
            db.query(BookSection)
            .filter(BookSection.book_id == book_id, BookSection.level == 1)
            .order_by(BookSection.order_index)
            .all()
        )
        if not chapters:
            return self._sample_chunks_flat(chunks)

        chunks_by_chapter: dict[uuid.UUID, list[BookChunk]] = {}
        for c in chunks:
            if c.section_id is None:
                continue
            chapter_id = self._find_chapter_id(db, c.section_id)
            if chapter_id is None:
                continue
            chunks_by_chapter.setdefault(chapter_id, []).append(c)

        if not chunks_by_chapter:
            return self._sample_chunks_flat(chunks)

        sampled: list[BookChunk] = []
        seen: set[uuid.UUID] = set()
        for ch in chapters:
            ch_chunks = chunks_by_chapter.get(ch.id, [])
            if not ch_chunks:
                continue
            for picked in self._pick_first_middle_last(ch_chunks, k=3):
                if picked.id not in seen:
                    seen.add(picked.id)
                    sampled.append(picked)

        # Cap to keep the prompt token budget bounded; ~30 chunks at ~800
        # tokens each is comfortably under typical model context windows.
        return sampled[:30] if sampled else self._sample_chunks_flat(chunks)

    @staticmethod
    def _pick_first_middle_last(chunks: list[BookChunk], k: int = 3) -> list[BookChunk]:
        n = len(chunks)
        if n <= k:
            return list(chunks)
        if k == 1:
            return [chunks[n // 2]]
        if k == 2:
            return [chunks[0], chunks[-1]]
        return [chunks[0], chunks[n // 2], chunks[-1]]

    @staticmethod
    def _find_chapter_id(db: Session, section_id: uuid.UUID) -> uuid.UUID | None:
        cur = db.get(BookSection, section_id)
        while cur is not None:
            if cur.level == 1:
                return cur.id
            if cur.parent_id is None:
                return None
            cur = db.get(BookSection, cur.parent_id)
        return None

    @staticmethod
    def _sample_chunks_flat(chunks: list[BookChunk], max_chunks: int = 10) -> list[BookChunk]:
        """Legacy 5-3-2 sampling for books without detected structure."""
        if len(chunks) <= max_chunks:
            return chunks

        n = len(chunks)
        mid = n // 2
        first = chunks[:5]
        middle = chunks[mid - 1 : mid + 2]
        last = chunks[-2:]

        seen_ids: set[uuid.UUID] = set()
        result: list[BookChunk] = []
        for c in first + middle + last:
            if c.id not in seen_ids:
                seen_ids.add(c.id)
                result.append(c)
        return result[:max_chunks]

    # Kept for any callers that imported the old name.
    _sample_chunks = _sample_chunks_flat
