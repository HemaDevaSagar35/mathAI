from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class BookProfileRead(BaseModel):
    id: UUID
    book_id: UUID
    profile_json: dict
    detected_subject: str
    level: str
    style: str
    proof_density: str
    computation_density: str
    diagram_dependency: str
    confidence: float
    created_at: datetime

    model_config = {"from_attributes": True}
