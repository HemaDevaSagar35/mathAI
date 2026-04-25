from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class QuestionCreate(BaseModel):
    question: str


class QuestionRead(BaseModel):
    id: UUID
    tidbit_id: UUID
    question_text: str
    answer_text: str
    answer_grounding_json: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}
