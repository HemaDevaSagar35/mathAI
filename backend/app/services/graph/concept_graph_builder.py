import logging
import uuid
from collections import defaultdict

from sqlalchemy.orm import Session

from app.llm.clients import BaseLLMClient, get_llm_client
from app.llm.prompts.loader import load_prompt
from app.models.concept import Concept, ConceptEdge
from app.models.profile import BookProfile

logger = logging.getLogger(__name__)

BATCH_SIZE = 20


class ConceptGraphBuilder:
    def __init__(self, llm: BaseLLMClient | None = None):
        self.llm = llm or get_llm_client(task="concept_graph")

    async def build_graph(
        self, db: Session, book_id: uuid.UUID
    ) -> list[ConceptEdge]:
        concepts = (
            db.query(Concept).filter(Concept.book_id == book_id).all()
        )
        if not concepts:
            raise ValueError(f"No concepts for book {book_id}. Run extraction first.")

        profile = db.query(BookProfile).filter(BookProfile.book_id == book_id).first()
        subject = profile.detected_subject if profile else "mathematics"

        name_to_id = {c.name.strip().lower(): c.id for c in concepts}
        all_raw_edges: list[dict] = []

        # Seed edges from prerequisite_names already on each concept
        all_raw_edges.extend(self._seed_edges_from_prereqs(concepts, name_to_id))

        # LLM-generated edges
        if len(concepts) <= BATCH_SIZE:
            llm_edges = await self._generate_edges(concepts, subject)
            all_raw_edges.extend(llm_edges)
        else:
            for i in range(0, len(concepts), BATCH_SIZE):
                batch = concepts[i : i + BATCH_SIZE]
                llm_edges = await self._generate_edges(batch, subject)
                all_raw_edges.extend(llm_edges)

        validated = self._validate_edges(all_raw_edges, name_to_id)

        db_edges: list[ConceptEdge] = []
        for e in validated:
            edge = ConceptEdge(
                book_id=book_id,
                source_concept_id=e["source_id"],
                target_concept_id=e["target_id"],
                edge_type=e["edge_type"],
                confidence=e.get("confidence", 0.8),
            )
            db.add(edge)
            db_edges.append(edge)

        db.commit()
        for e in db_edges:
            db.refresh(e)
        return db_edges

    async def _generate_edges(
        self, concepts: list[Concept], subject: str
    ) -> list[dict]:
        concepts_json = "\n".join(
            f"- {c.name} (type: {c.concept_type}, difficulty: {c.difficulty})"
            for c in concepts
        )
        prompt = load_prompt(
            "concept_graph",
            subject=subject,
            concepts_json=concepts_json,
        )
        data = await self.llm.generate_json(prompt, task="concept_graph")
        return data.get("edges", [])

    @staticmethod
    def _seed_edges_from_prereqs(
        concepts: list[Concept], name_to_id: dict[str, uuid.UUID]
    ) -> list[dict]:
        edges = []
        for c in concepts:
            for prereq_name in (c.prerequisite_names or []):
                key = prereq_name.strip().lower()
                if key in name_to_id and key != c.name.strip().lower():
                    edges.append({
                        "source": prereq_name,
                        "target": c.name,
                        "edge_type": "prerequisite",
                        "confidence": 0.9,
                    })
        return edges

    @staticmethod
    def _validate_edges(
        raw_edges: list[dict], name_to_id: dict[str, uuid.UUID]
    ) -> list[dict]:
        seen: set[tuple] = set()
        valid: list[dict] = []

        for e in raw_edges:
            src = e.get("source", "").strip().lower()
            tgt = e.get("target", "").strip().lower()
            edge_type = e.get("edge_type", "related")

            if src == tgt:
                continue
            if src not in name_to_id or tgt not in name_to_id:
                continue

            key = (src, tgt, edge_type)
            if key in seen:
                continue
            seen.add(key)

            valid.append({
                "source_id": name_to_id[src],
                "target_id": name_to_id[tgt],
                "edge_type": edge_type,
                "confidence": e.get("confidence", 0.8),
            })

        return valid
