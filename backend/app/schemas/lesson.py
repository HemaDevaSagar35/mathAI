from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TidbitLessonRead(BaseModel):
    id: UUID
    tidbit_id: UUID
    lesson_json: dict
    version: int
    created_at: datetime

    model_config = {"from_attributes": True}
