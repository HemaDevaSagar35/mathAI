import asyncio
import logging
import uuid

from sqlalchemy.orm import Session

from app.llm.clients import BaseLLMClient, get_llm_client
from app.llm.prompts.loader import load_prompt
from app.models.book import BookChunk
from app.models.concept import Concept
from app.models.profile import BookProfile
from app.services.concept_extraction.concept_normalizer import ConceptNormalizer

logger = logging.getLogger(__name__)

MAX_CONCURRENT = 5


class ConceptExtractor:
    def __init__(self, llm: BaseLLMClient | None = None):
        self.llm = llm or get_llm_client(task="concept_extraction")
        self.normalizer = ConceptNormalizer(self.llm)

    async def extract_from_book(
        self, db: Session, book_id: uuid.UUID
    ) -> list[Concept]:
        profile = db.query(BookProfile).filter(BookProfile.book_id == book_id).first()
        if not profile:
            raise ValueError(f"No profile for book {book_id}. Run profiling first.")

        chunks = (
            db.query(BookChunk)
            .filter(BookChunk.book_id == book_id)
            .order_by(BookChunk.chunk_index)
            .all()
        )
        if not chunks:
            raise ValueError(f"No chunks for book {book_id}.")

        batches = self._batch_chunks(chunks, batch_size=2)

        sem = asyncio.Semaphore(MAX_CONCURRENT)
        raw_concepts: list[dict] = []

        async def process_batch(batch: list[BookChunk]) -> list[dict]:
            async with sem:
                return await self._extract_batch(batch, profile)

        tasks = [process_batch(batch) for batch in batches]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error("Batch %d failed: %s", i, result)
                continue
            raw_concepts.extend(result)

        normalized = await self.normalizer.normalize(raw_concepts)

        db_concepts: list[Concept] = []
        for c in normalized:
            concept = Concept(
                book_id=book_id,
                name=c["name"],
                normalized_name=c.get("normalized_name", c["name"].strip().lower()),
                concept_type=c.get("concept_type", "definition"),
                difficulty=c.get("difficulty", 1),
                importance=c.get("importance", "supporting"),
                source_chunk_ids=c.get("source_chunk_ids", []),
                prerequisite_names=c.get("prerequisite_names", []),
                common_confusions=c.get("common_confusions", []),
                confidence=0.8,
            )
            db.add(concept)
            db_concepts.append(concept)

        db.commit()
        for c in db_concepts:
            db.refresh(c)
        return db_concepts

    async def _extract_batch(
        self, batch: list[BookChunk], profile: BookProfile
    ) -> list[dict]:
        chunk_text = "\n\n---\n\n".join(
            f"[Chunk {c.chunk_index}]\n{c.clean_text}" for c in batch
        )
        chunk_ids = [str(c.id) for c in batch]

        prompt = load_prompt(
            "concept_extraction",
            chunk_text=chunk_text,
            subject=profile.detected_subject,
            level=profile.level,
            style=profile.style,
        )

        data = await self.llm.generate_json(prompt, task="concept_extraction")
        concepts = data.get("concepts", [])

        for c in concepts:
            c.setdefault("source_chunk_ids", [])
            c["source_chunk_ids"].extend(chunk_ids)

        return concepts

    @staticmethod
    def _batch_chunks(chunks: list[BookChunk], batch_size: int = 2) -> list[list[BookChunk]]:
        return [chunks[i : i + batch_size] for i in range(0, len(chunks), batch_size)]
