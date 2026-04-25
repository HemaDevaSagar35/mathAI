from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ConceptRead(BaseModel):
    id: UUID
    book_id: UUID
    name: str
    normalized_name: str
    concept_type: str
    difficulty: int
    importance: str
    source_chunk_ids: list
    prerequisite_names: list
    common_confusions: list
    confidence: float
    created_at: datetime

    model_config = {"from_attributes": True}


class ConceptEdgeRead(BaseModel):
    id: UUID
    book_id: UUID
    source_concept_id: UUID
    target_concept_id: UUID
    edge_type: str
    confidence: float
    created_at: datetime

    model_config = {"from_attributes": True}


class GraphRead(BaseModel):
    concepts: list[ConceptRead]
    edges: list[ConceptEdgeRead]
