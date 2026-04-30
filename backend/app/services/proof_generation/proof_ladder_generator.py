import uuid

from sqlalchemy.orm import Session

from app.llm.clients import BaseLLMClient, get_llm_client
from app.llm.prompts.loader import load_prompt
from app.models.book import BookChunk
from app.models.concept import Concept
from app.models.profile import BookProfile
from app.models.proof import ProofLadder
from app.models.tidbit import Tidbit


def needs_proof_ladder(tidbit: Tidbit, concept: Concept | None, profile: BookProfile | None) -> bool:
    if concept and concept.concept_type in ("theorem", "proof"):
        return True
    if (
        profile
        and profile.proof_density in ("medium", "high")
        and concept
        and concept.concept_type == "definition"
        and "proof" in (tidbit.learning_goal or "").lower()
    ):
        return True
    return False


class ProofLadderGenerator:
    def __init__(self, llm: BaseLLMClient | None = None):
        self.llm = llm or get_llm_client(task="proof_ladder")

    async def generate(self, db: Session, tidbit_id: uuid.UUID) -> ProofLadder | None:
        tidbit = db.get(Tidbit, tidbit_id)
        if not tidbit:
            raise ValueError(f"Tidbit {tidbit_id} not found")

        concept = db.get(Concept, tidbit.concept_id) if tidbit.concept_id else None
        profile = db.query(BookProfile).filter(BookProfile.book_id == tidbit.book_id).first()

        if not needs_proof_ladder(tidbit, concept, profile):
            return None

        chunks = self._load_chunks(db, tidbit)
        source_text = "\n\n---\n\n".join(
            f"[Chunk {c.chunk_index} | id={c.id}]\n{c.clean_text}" for c in chunks
        )

        theorem_statement = self._extract_theorem(tidbit, concept)

        prompt = load_prompt(
            "proof_ladder",
            theorem_statement=theorem_statement,
            source_text=source_text or "(no source text available)",
            subject=profile.detected_subject if profile else "mathematics",
            level=profile.level if profile else "undergraduate",
        )

        data = await self.llm.generate_json(prompt, task="proof_ladder")

        ladder = ProofLadder(
            tidbit_id=tidbit_id,
            theorem_statement=data.get("theorem", theorem_statement),
            proof_ladder_json=data,
        )
        db.add(ladder)
        db.commit()
        db.refresh(ladder)
        return ladder

    @staticmethod
    def _extract_theorem(tidbit: Tidbit, concept: Concept | None) -> str:
        if concept and concept.name:
            return f"{concept.name}: {tidbit.learning_goal}"
        return tidbit.learning_goal or tidbit.title

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
