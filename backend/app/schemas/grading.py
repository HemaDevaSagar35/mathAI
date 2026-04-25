from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class GradeRequest(BaseModel):
    question_id: str
    transcript_final: str


class GradingResultRead(BaseModel):
    attempt_id: UUID
    grading: dict


class AnswerAttemptRead(BaseModel):
    id: UUID
    user_id: UUID
    tidbit_id: UUID
    question_id: str
    input_mode: str
    transcript_final: str
    score: float
    feedback_json: dict
    misconception: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
