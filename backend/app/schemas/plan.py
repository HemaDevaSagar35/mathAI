from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.tidbit import TidbitRead


class StudyPlanRead(BaseModel):
    id: UUID
    book_id: UUID
    status: str
    tidbits: list[TidbitRead] = []
    created_at: datetime

    model_config = {"from_attributes": True}
