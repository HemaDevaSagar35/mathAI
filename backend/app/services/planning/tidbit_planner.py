import uuid

from sqlalchemy.orm import Session

from app.llm.clients import BaseLLMClient, get_llm_client
from app.llm.prompts.loader import load_prompt
from app.models.concept import Concept, ConceptEdge
from app.models.plan import StudyPlan
from app.models.profile import BookProfile
from app.models.tidbit import Tidbit
from app.services.planning.topo_sort import topological_sort_concepts


class TidbitPlanner:
    def __init__(self, llm: BaseLLMClient | None = None):
        self.llm = llm or get_llm_client(task="tidbit_planning")

    async def generate_plan(
        self,
        db: Session,
        book_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
    ) -> StudyPlan:
        profile = db.query(BookProfile).filter(BookProfile.book_id == book_id).first()
        if not profile:
            raise ValueError(f"No profile for book {book_id}.")

        concepts = db.query(Concept).filter(Concept.book_id == book_id).all()
        if not concepts:
            raise ValueError(f"No concepts for book {book_id}.")

        edges = db.query(ConceptEdge).filter(ConceptEdge.book_id == book_id).all()

        sorted_concepts = topological_sort_concepts(concepts, edges)

        concepts_json = "\n".join(
            f"{i+1}. {c.name} (type: {c.concept_type}, difficulty: {c.difficulty}, "
            f"importance: {c.importance}, chunks: {c.source_chunk_ids})"
            for i, c in enumerate(sorted_concepts)
        )

        edges_json = "\n".join(
            f"- {self._concept_name(e.source_concept_id, concepts)} → "
            f"{self._concept_name(e.target_concept_id, concepts)} ({e.edge_type})"
            for e in edges
        )

        prompt = load_prompt(
            "tidbit_planning",
            subject=profile.detected_subject,
            level=profile.level,
            style=profile.style,
            concepts_json=concepts_json,
            edges_json=edges_json or "(no edges)",
        )

        data = await self.llm.generate_json(prompt, task="tidbit_planning")
        tidbits_data = data.get("tidbits", [])

        plan = StudyPlan(book_id=book_id, user_id=user_id, status="active")
        db.add(plan)
        db.flush()

        concept_name_to_id = {c.name.strip().lower(): c.id for c in concepts}

        db_tidbits: list[Tidbit] = []
        for i, t in enumerate(tidbits_data):
            concept_name = t.get("concept_name", "").strip().lower()
            concept_id = concept_name_to_id.get(concept_name)

            tidbit = Tidbit(
                study_plan_id=plan.id,
                book_id=book_id,
                order_index=i,
                title=t.get("title", f"Tidbit {i+1}"),
                concept_id=concept_id,
                learning_goal=t.get("learning_goal", ""),
                source_chunk_ids=t.get("source_chunk_ids", []),
                estimated_minutes=t.get("estimated_minutes", 15),
                difficulty=t.get("difficulty", 1),
                is_original_plan=True,
                tidbit_type="original",
            )
            db.add(tidbit)
            db_tidbits.append(tidbit)

        db.commit()
        db.refresh(plan)
        return plan

    @staticmethod
    def _concept_name(concept_id: uuid.UUID, concepts: list[Concept]) -> str:
        for c in concepts:
            if c.id == concept_id:
                return c.name
        return str(concept_id)
