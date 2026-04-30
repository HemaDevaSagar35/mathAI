import uuid

from sqlalchemy.orm import Session

from app.llm.clients import BaseLLMClient, get_llm_client
from app.llm.prompts.loader import load_prompt
from app.models.book import BookChunk
from app.models.concept import Concept
from app.models.lesson import TidbitLesson
from app.models.profile import BookProfile
from app.models.tidbit import Tidbit


class LessonGenerator:
    def __init__(self, llm: BaseLLMClient | None = None):
        self.llm = llm or get_llm_client(task="lesson_generation")

    async def generate_lesson(self, db: Session, tidbit_id: uuid.UUID) -> TidbitLesson:
        tidbit = db.get(Tidbit, tidbit_id)
        if not tidbit:
            raise ValueError(f"Tidbit {tidbit_id} not found")

        concept = db.get(Concept, tidbit.concept_id) if tidbit.concept_id else None
        profile = db.query(BookProfile).filter(BookProfile.book_id == tidbit.book_id).first()

        chunks = self._load_source_chunks(db, tidbit)
        chunks_text = "\n\n---\n\n".join(
            f"[Chunk {c.chunk_index} | id={c.id}]\n{c.clean_text}" for c in chunks
        )

        strategy = {}
        if profile and profile.profile_json:
            strategy = profile.profile_json.get("learning_strategy", {})

        prompt = load_prompt(
            "lesson_generation",
            title=tidbit.title,
            concept_name=concept.name if concept else tidbit.title,
            learning_goal=tidbit.learning_goal,
            source_chunks_text=chunks_text or "(no source chunks available)",
            subject=profile.detected_subject if profile else "mathematics",
            level=profile.level if profile else "undergraduate",
            style=profile.style if profile else "mixed",
            proof_ladder_weight=strategy.get("proof_ladder_weight", "medium"),
        )

        data = await self.llm.generate_json(prompt, task="lesson_generation")

        lesson = TidbitLesson(
            tidbit_id=tidbit_id,
            lesson_json=data,
            version=1,
        )
        db.add(lesson)
        db.commit()
        db.refresh(lesson)
        return lesson

    @staticmethod
    def _load_source_chunks(db: Session, tidbit: Tidbit) -> list[BookChunk]:
        chunk_ids = tidbit.source_chunk_ids or []
        if not chunk_ids:
            return (
                db.query(BookChunk)
                .filter(BookChunk.book_id == tidbit.book_id)
                .order_by(BookChunk.chunk_index)
                .limit(3)
                .all()
            )

        valid_ids = []
        for cid in chunk_ids:
            try:
                valid_ids.append(uuid.UUID(str(cid)))
            except (ValueError, AttributeError):
                continue

        if not valid_ids:
            return (
                db.query(BookChunk)
                .filter(BookChunk.book_id == tidbit.book_id)
                .order_by(BookChunk.chunk_index)
                .limit(3)
                .all()
            )

        return db.query(BookChunk).filter(BookChunk.id.in_(valid_ids)).all()
