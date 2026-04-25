from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TidbitQuizRead(BaseModel):
    id: UUID
    tidbit_id: UUID
    quiz_json: dict
    created_at: datetime

    model_config = {"from_attributes": True}
