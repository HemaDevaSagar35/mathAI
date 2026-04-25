import uuid

from sqlalchemy.orm import Session

from app.llm.clients import BaseLLMClient, get_llm_client
from app.llm.prompts.loader import load_prompt
from app.models.book import Book, BookChunk
from app.models.profile import BookProfile


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

        sampled = self._sample_chunks(chunks)
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

    @staticmethod
    def _sample_chunks(chunks: list[BookChunk], max_chunks: int = 10) -> list[BookChunk]:
        """Sample first 5 + middle 3 + last 2 chunks for diverse coverage."""
        if len(chunks) <= max_chunks:
            return chunks

        n = len(chunks)
        mid = n // 2
        first = chunks[:5]
        middle = chunks[mid - 1 : mid + 2]
        last = chunks[-2:]

        seen_ids = set()
        result = []
        for c in first + middle + last:
            if c.id not in seen_ids:
                seen_ids.add(c.id)
                result.append(c)
        return result[:max_chunks]
