from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UserTidbitProgressRead(BaseModel):
    id: UUID
    user_id: UUID
    tidbit_id: UUID
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    quiz_score: float | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConceptMasteryRead(BaseModel):
    id: UUID
    user_id: UUID
    concept_id: UUID
    mastery_score: float
    confidence: float
    last_seen_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ProgressDashboard(BaseModel):
    active_book: dict | None = None
    current_tidbit: dict | None = None
    streak: int = 0
    overall_progress: float = 0.0
    weak_concepts: list[dict] = []
    recent_activity: list[dict] = []
