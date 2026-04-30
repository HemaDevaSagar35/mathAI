import uuid

from sqlalchemy.orm import Session

from app.llm.clients import BaseLLMClient, get_llm_client
from app.llm.prompts.loader import load_prompt
from app.models.book import BookChunk
from app.models.concept import Concept
from app.models.lesson import TidbitLesson
from app.models.profile import BookProfile
from app.models.quiz import TidbitQuiz
from app.models.tidbit import Tidbit


class QuizGenerator:
    def __init__(self, llm: BaseLLMClient | None = None):
        self.llm = llm or get_llm_client(task="quiz_generation")

    async def generate_quiz(self, db: Session, tidbit_id: uuid.UUID) -> TidbitQuiz:
        tidbit = db.get(Tidbit, tidbit_id)
        if not tidbit:
            raise ValueError(f"Tidbit {tidbit_id} not found")

        concept = db.get(Concept, tidbit.concept_id) if tidbit.concept_id else None
        profile = db.query(BookProfile).filter(BookProfile.book_id == tidbit.book_id).first()
        lesson = db.query(TidbitLesson).filter(TidbitLesson.tidbit_id == tidbit_id).first()

        lesson_summary = ""
        if lesson and lesson.lesson_json:
            lj = lesson.lesson_json
            lesson_summary = (
                f"Core idea: {lj.get('core_idea', '')}\n"
                f"Quick summary: {lj.get('quick_summary', '')}\n"
                f"Formal definition: {lj.get('formal_definition_or_statement', '')}"
            )

        chunks = self._load_chunks(db, tidbit)
        source_text = "\n\n---\n\n".join(
            f"[Chunk {c.chunk_index} | id={c.id}]\n{c.clean_text}" for c in chunks
        )

        prompt = load_prompt(
            "quiz_generation",
            title=tidbit.title,
            concept_name=concept.name if concept else tidbit.title,
            learning_goal=tidbit.learning_goal,
            lesson_summary=lesson_summary or "(no lesson generated yet)",
            source_text=source_text or "(no source text)",
            subject=profile.detected_subject if profile else "mathematics",
            level=profile.level if profile else "undergraduate",
        )

        data = await self.llm.generate_json(prompt, task="quiz_generation")

        quiz = TidbitQuiz(
            tidbit_id=tidbit_id,
            quiz_json=data,
        )
        db.add(quiz)
        db.commit()
        db.refresh(quiz)
        return quiz

    @staticmethod
    def _load_chunks(db: Session, tidbit: Tidbit) -> list[BookChunk]:
        chunk_ids = tidbit.source_chunk_ids or []
        valid_ids = []
        for cid in chunk_ids:
            try:
                valid_ids.append(uuid.UUID(str(cid)))
            except (ValueError, AttributeError):
                continue

        if valid_ids:
            return db.query(BookChunk).filter(BookChunk.id.in_(valid_ids)).all()

        return (
            db.query(BookChunk)
            .filter(BookChunk.book_id == tidbit.book_id)
            .order_by(BookChunk.chunk_index)
            .limit(3)
            .all()
        )
