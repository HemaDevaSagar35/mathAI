from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TidbitRead(BaseModel):
    id: UUID
    study_plan_id: UUID
    book_id: UUID
    order_index: int
    title: str
    concept_id: UUID | None
    learning_goal: str
    source_chunk_ids: list
    estimated_minutes: int
    difficulty: int
    is_original_plan: bool
    tidbit_type: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TidbitDetailRead(BaseModel):
    tidbit: TidbitRead
    lesson: dict | None = None
    quiz: dict | None = None
    proof_ladder: dict | None = None
    progress: dict | None = None
